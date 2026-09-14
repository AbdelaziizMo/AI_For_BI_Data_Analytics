WITH DQ_DEDUPLICATED_TRANSACTIONS AS (
    /* -------------------------------------------------------------------------
       CTE 1: DQ_DEDUPLICATED_TRANSACTIONS
       Purpose: Apply core Data Quality (DQ) validation rules and assign row numbers 
                partitioned by TransactionID to identify duplicate records.
       ------------------------------------------------------------------------- */
    SELECT
        t.TransactionID,
        t.AccountIDFrom,
        t.AccountIDTo,
        t.TotalAmount,
        t.TransactionType AS ServiceID, -- TransactionType is explicitly confirmed as Service ID
        t.IsReversed,
        t.Date AS TransactionTimestamp,
        TRUNC(t.Date) AS TransactionDate,
        ROW_NUMBER() OVER (
            PARTITION BY t.TransactionID
            ORDER BY t.Date DESC, t.ID DESC
        ) AS RowNum
    FROM PLAYGROUND.TRANSACTIONS t
    WHERE t.TransactionID IS NOT NULL
      AND t.AccountIDFrom IS NOT NULL
      AND t.AccountIDTo IS NOT NULL
      AND t.TotalAmount IS NOT NULL
      AND t.TransactionType IS NOT NULL
      AND t.IsReversed IS NOT NULL
      AND t.Date IS NOT NULL
      AND t.TotalAmount > 0                   -- Exclude non-positive amounts
      AND t.IsReversed IN (0, 1)             -- Enforce binary status validity
      AND t.Date <= SYSTIMESTAMP              -- Exclude future-dated transactions
),
CLEAN_BUSINESS_TRANSACTIONS AS (
    /* -------------------------------------------------------------------------
       CTE 2: CLEAN_BUSINESS_TRANSACTIONS
       Purpose: Filter out duplicate records, exclude reversed transactions, and 
                validate Service IDs via explicit INNER JOIN with SERVICES table.
       ------------------------------------------------------------------------- */
    SELECT
        d.TransactionID,
        d.ServiceID,
        s.NameAr AS ServiceName,
        d.TransactionDate,
        d.TotalAmount
    FROM DQ_DEDUPLICATED_TRANSACTIONS d
    INNER JOIN PLAYGROUND.SERVICES s
        ON d.ServiceID = s.ID
    WHERE d.RowNum = 1                         -- Retain only the latest unique record
      AND d.IsReversed = 0                     -- Include valid non-reversed business activity
),
DAILY_SERVICE_SUMMARY AS (
    /* -------------------------------------------------------------------------
       CTE 3: DAILY_SERVICE_SUMMARY
       Purpose: Aggregate daily performance metrics per service.
       ------------------------------------------------------------------------- */
    SELECT
        ServiceID,
        ServiceName,
        TransactionDate,
        COUNT(TransactionID) AS DailyTransactionVolume,
        SUM(TotalAmount) AS DailyRevenue,
        ROUND(AVG(TotalAmount), 3) AS AvgTransactionAmount
    FROM CLEAN_BUSINESS_TRANSACTIONS
    GROUP BY
        ServiceID,
        ServiceName,
        TransactionDate
),
SERVICE_OVERALL_TOTALS AS (
    /* -------------------------------------------------------------------------
       CTE 4: SERVICE_OVERALL_TOTALS
       Purpose: Calculate 12-day period totals per service using window aggregates.
       ------------------------------------------------------------------------- */
    SELECT
        d.ServiceID,
        d.ServiceName,
        d.TransactionDate,
        d.DailyTransactionVolume,
        d.DailyRevenue,
        d.AvgTransactionAmount,
        SUM(d.DailyRevenue) OVER (PARTITION BY d.ServiceID) AS Total12DayRevenue,
        SUM(d.DailyTransactionVolume) OVER (PARTITION BY d.ServiceID) AS Total12DayVolume
    FROM DAILY_SERVICE_SUMMARY d
),
SERVICE_RANKINGS AS (
    /* -------------------------------------------------------------------------
       CTE 5: SERVICE_RANKINGS
       Purpose: Rank services globally based on 12-day revenue and volume.
       ------------------------------------------------------------------------- */
    SELECT
        s.*,
        DENSE_RANK() OVER (ORDER BY s.Total12DayRevenue DESC) AS RevenueRank,
        DENSE_RANK() OVER (ORDER BY s.Total12DayVolume DESC) AS VolumeRank
    FROM SERVICE_OVERALL_TOTALS s
),
LAG_PERFORMANCE AS (
    /* -------------------------------------------------------------------------
       CTE 6: LAG_PERFORMANCE
       Purpose: Retrieve previous day's metrics using LAG() for trend calculations.
       ------------------------------------------------------------------------- */
    SELECT
        r.ServiceID,
        r.ServiceName,
        r.TransactionDate,
        r.DailyTransactionVolume,
        r.DailyRevenue,
        r.AvgTransactionAmount,
        r.Total12DayRevenue,
        r.Total12DayVolume,
        r.RevenueRank,
        r.VolumeRank,
        LAG(r.DailyRevenue, 1) OVER (
            PARTITION BY r.ServiceID 
            ORDER BY r.TransactionDate ASC
        ) AS PrevDayRevenue,
        LAG(r.DailyTransactionVolume, 1) OVER (
            PARTITION BY r.ServiceID 
            ORDER BY r.TransactionDate ASC
        ) AS PrevDayVolume
    FROM SERVICE_RANKINGS r
)
/* -----------------------------------------------------------------------------
   FINAL SELECT:
   Calculate Day-over-Day (DoD) growth percentages with zero-division safety.
   ----------------------------------------------------------------------------- */
SELECT
    ServiceID,
    ServiceName,
    TransactionDate,
    DailyTransactionVolume,
    DailyRevenue,
    AvgTransactionAmount,
    Total12DayRevenue,
    Total12DayVolume,
    RevenueRank,
    VolumeRank,
    NVL(PrevDayRevenue, 0) AS PrevDayRevenue,
    NVL(PrevDayVolume, 0) AS PrevDayVolume,
    CASE
        WHEN PrevDayRevenue IS NULL OR PrevDayRevenue = 0 THEN NULL
        ELSE ROUND(((DailyRevenue - PrevDayRevenue) / PrevDayRevenue) * 100, 2)
    END AS RevenueGrowthPct,
    CASE
        WHEN PrevDayVolume IS NULL OR PrevDayVolume = 0 THEN NULL
        ELSE ROUND(((DailyTransactionVolume - PrevDayVolume) / PrevDayVolume) * 100, 2)
    END AS VolumeGrowthPct
FROM LAG_PERFORMANCE
ORDER BY
    RevenueRank ASC,
    ServiceID ASC,
    TransactionDate ASC;
