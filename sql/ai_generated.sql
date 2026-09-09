WITH CLEANSED_TRANSACTIONS AS (
    SELECT 
        t.TransactionID,
        t.AccountIDFrom,
        t.AccountIDTo,
        t.TotalAmount,
        t.TransactionType, -- Confirmed as Service ID
        t.IsReversed,
        t.Date,
        t.ID,
        -- Assign row numbers to identify duplicate TransactionIDs deterministically
        ROW_NUMBER() OVER (
            PARTITION BY t.TransactionID 
            ORDER BY t.Date DESC, t.ID DESC
        ) AS rn
    FROM PLAYGROUND.TRANSACTIONS t
    WHERE 
        -- Week 6 DQ Rule 2: Exclude NULLs in critical columns
        t.TransactionID IS NOT NULL
        AND t.AccountIDFrom IS NOT NULL
        AND t.AccountIDTo IS NOT NULL
        AND t.TotalAmount IS NOT NULL
        AND t.TransactionType IS NOT NULL
        AND t.IsReversed IS NOT NULL
        AND t.Date IS NOT NULL
        -- Week 6 DQ Rule 3: Valid positive transaction amounts
        AND t.TotalAmount > 0
        -- Week 6 DQ Rule 5: Valid transaction status values
        AND t.IsReversed IN (0, 1)
        -- Week 6 DQ Rule 6: Exclude future transaction dates
        AND t.Date <= SYSTIMESTAMP
),

DEDUPLICATED_ACTIVE_TRANSACTIONS AS (
    SELECT 
        ct.TransactionID,
        ct.TotalAmount,
        ct.TransactionType AS SERVICE_ID,
        TRUNC(ct.Date) AS TRANSACTION_DATE
    FROM CLEANSED_TRANSACTIONS ct
    WHERE 
        -- Week 6 DQ Rule 1: Deduplication filter
        ct.rn = 1
        -- Business Logic Rule: Exclude reversed transactions from financial performance
        AND ct.IsReversed = 0
),

DAILY_SERVICE_AGGREGATES AS (
    SELECT 
        dat.TRANSACTION_DATE,
        dat.SERVICE_ID,
        s.NameAr AS SERVICE_NAME,
        COUNT(dat.TransactionID) AS DAILY_VOLUME,
        SUM(dat.TotalAmount) AS DAILY_REVENUE,
        ROUND(AVG(dat.TotalAmount), 3) AS AVG_TRANSACTION_AMOUNT
    FROM DEDUPLICATED_ACTIVE_TRANSACTIONS dat
    -- Week 6 DQ Rule 4 & Join Requirement: Join with SERVICES on TransactionType = ID
    INNER JOIN PLAYGROUND.SERVICES s 
        ON dat.SERVICE_ID = s.ID
    GROUP BY 
        dat.TRANSACTION_DATE,
        dat.SERVICE_ID,
        s.NameAr
),

SERVICE_OVERALL_METRICS AS (
    SELECT 
        dsa.SERVICE_ID,
        SUM(dsa.DAILY_VOLUME) AS OVERALL_VOLUME,
        SUM(dsa.DAILY_REVENUE) AS OVERALL_REVENUE,
        -- Calculate ranks across the 12-day dataset
        DENSE_RANK() OVER (ORDER BY SUM(dsa.DAILY_REVENUE) DESC) AS REVENUE_RANK,
        DENSE_RANK() OVER (ORDER BY SUM(dsa.DAILY_VOLUME) DESC) AS VOLUME_RANK
    FROM DAILY_SERVICE_AGGREGATES dsa
    GROUP BY dsa.SERVICE_ID
)

SELECT 
    dsa.TRANSACTION_DATE,
    dsa.SERVICE_ID,
    dsa.SERVICE_NAME,
    
    -- Daily Performance
    dsa.DAILY_VOLUME,
    dsa.DAILY_REVENUE,
    dsa.AVG_TRANSACTION_AMOUNT,
    
    -- Period Ranks & Totals
    som.OVERALL_REVENUE,
    som.OVERALL_VOLUME,
    som.REVENUE_RANK,
    som.VOLUME_RANK,
    
    -- Day-over-Day Trends
    LAG(dsa.DAILY_REVENUE) OVER (
        PARTITION BY dsa.SERVICE_ID 
        ORDER BY dsa.TRANSACTION_DATE
    ) AS PREVIOUS_DAY_REVENUE,
    
    LAG(dsa.DAILY_VOLUME) OVER (
        PARTITION BY dsa.SERVICE_ID 
        ORDER BY dsa.TRANSACTION_DATE
    ) AS PREVIOUS_DAY_VOLUME,
    
    -- Day-over-Day Growth % (avoiding division by zero)
    ROUND(
        (dsa.DAILY_REVENUE - LAG(dsa.DAILY_REVENUE) OVER (PARTITION BY dsa.SERVICE_ID ORDER BY dsa.TRANSACTION_DATE)) 
        / NULLIF(LAG(dsa.DAILY_REVENUE) OVER (PARTITION BY dsa.SERVICE_ID ORDER BY dsa.TRANSACTION_DATE), 0) * 100, 
        2
    ) AS REVENUE_GROWTH_PCT,
    
    ROUND(
        (dsa.DAILY_VOLUME - LAG(dsa.DAILY_VOLUME) OVER (PARTITION BY dsa.SERVICE_ID ORDER BY dsa.TRANSACTION_DATE)) 
        / NULLIF(LAG(dsa.DAILY_VOLUME) OVER (PARTITION BY dsa.SERVICE_ID ORDER BY dsa.TRANSACTION_DATE), 0) * 100, 
        2
    ) AS VOLUME_GROWTH_PCT

FROM DAILY_SERVICE_AGGREGATES dsa
JOIN SERVICE_OVERALL_METRICS som 
    ON dsa.SERVICE_ID = som.SERVICE_ID
ORDER BY 
    som.REVENUE_RANK ASC,
    dsa.SERVICE_ID ASC,
    dsa.TRANSACTION_DATE ASC;
