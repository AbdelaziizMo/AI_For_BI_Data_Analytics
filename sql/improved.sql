WITH "DQ_DEDUPLICATED_TRANSACTIONS" AS (
    SELECT
        t."TransactionID",
        t."AccountIDFrom",
        t."AccountIDTo",
        t."TotalAmount",
        t."TransactionType" AS "Service_ID",
        t."IsReversed",
        t."Date",
        TRUNC(t."Date") AS "Transaction_Date",
        t."ID",
        ROW_NUMBER() OVER (
            PARTITION BY t."TransactionID"
            ORDER BY t."ID" DESC
        ) AS "RowNum"
    FROM PLAYGROUND.TRANSACTIONS t
    WHERE t."TransactionID" IS NOT NULL
      AND t."AccountIDFrom" IS NOT NULL
      AND t."AccountIDTo" IS NOT NULL
      AND t."TotalAmount" IS NOT NULL
      AND t."TransactionType" IS NOT NULL
      AND t."IsReversed" IS NOT NULL
      AND t."Date" IS NOT NULL
      AND t."ID" IS NOT NULL
      AND t."TotalAmount" > 0
      AND t."IsReversed" IN (0, 1)
      AND t."Date" <= SYSTIMESTAMP
      AND t."Date" >= :start_date
      AND t."Date" < :end_date
),
"CLEAN_BUSINESS_TRANSACTIONS" AS (
    SELECT
        d."TransactionID",
        d."Service_ID",
        s."NameAr" AS "Service_Name",
        d."Transaction_Date",
        d."TotalAmount"
    FROM "DQ_DEDUPLICATED_TRANSACTIONS" d
    INNER JOIN PLAYGROUND.SERVICES s
        ON d."Service_ID" = s."ID"
    WHERE d."RowNum" = 1
      AND d."IsReversed" = 0
),
"DAILY_SERVICE_SUMMARY" AS (
    SELECT
        d."Service_ID",
        d."Service_Name",
        d."Transaction_Date",
        COUNT(d."TransactionID") AS "Daily_Transaction_Volume",
        SUM(d."TotalAmount") AS "Daily_Revenue",
        ROUND(AVG(d."TotalAmount"), 3) AS "Average_Transaction_Amount"
    FROM "CLEAN_BUSINESS_TRANSACTIONS" d
    GROUP BY
        d."Service_ID",
        d."Service_Name",
        d."Transaction_Date"
),
"SERVICE_OVERALL_TOTALS" AS (
    SELECT
        d."Service_ID",
        d."Service_Name",
        d."Transaction_Date",
        d."Daily_Transaction_Volume",
        d."Daily_Revenue",
        d."Average_Transaction_Amount",
        SUM(d."Daily_Revenue") OVER (PARTITION BY d."Service_ID") AS "Total_Revenue",
        SUM(d."Daily_Transaction_Volume") OVER (PARTITION BY d."Service_ID") AS "Total_Transaction_Volume"
    FROM "DAILY_SERVICE_SUMMARY" d
),
"SERVICE_RANKINGS" AS (
    SELECT
        s."Service_ID",
        s."Service_Name",
        s."Transaction_Date",
        s."Daily_Transaction_Volume",
        s."Daily_Revenue",
        s."Average_Transaction_Amount",
        s."Total_Revenue",
        s."Total_Transaction_Volume",
        DENSE_RANK() OVER (ORDER BY s."Total_Revenue" DESC) AS "Revenue_Rank",
        DENSE_RANK() OVER (ORDER BY s."Total_Transaction_Volume" DESC) AS "Volume_Rank"
    FROM "SERVICE_OVERALL_TOTALS" s
),
"LAG_PERFORMANCE" AS (
    SELECT
        r."Service_ID",
        r."Service_Name",
        r."Transaction_Date",
        r."Daily_Transaction_Volume",
        r."Daily_Revenue",
        r."Average_Transaction_Amount",
        r."Total_Revenue",
        r."Total_Transaction_Volume",
        r."Revenue_Rank",
        r."Volume_Rank",
        LAG(r."Daily_Revenue", 1) OVER (
            PARTITION BY r."Service_ID"
            ORDER BY r."Transaction_Date" ASC
        ) AS "Previous_Day_Revenue",
        LAG(r."Daily_Transaction_Volume", 1) OVER (
            PARTITION BY r."Service_ID"
            ORDER BY r."Transaction_Date" ASC
        ) AS "Previous_Day_Transaction_Volume"
    FROM "SERVICE_RANKINGS" r
)
SELECT
    l."Service_ID",
    l."Service_Name",
    l."Transaction_Date",
    l."Daily_Transaction_Volume",
    l."Daily_Revenue",
    l."Average_Transaction_Amount",
    l."Total_Revenue",
    l."Total_Transaction_Volume",
    l."Revenue_Rank",
    l."Volume_Rank",
    l."Previous_Day_Revenue",
    l."Previous_Day_Transaction_Volume",
    CASE
        WHEN l."Previous_Day_Revenue" IS NULL OR l."Previous_Day_Revenue" = 0 THEN NULL
        ELSE ROUND(((l."Daily_Revenue" - l."Previous_Day_Revenue") / l."Previous_Day_Revenue") * 100, 2)
    END AS "Revenue_Growth_Pct",
    CASE
        WHEN l."Previous_Day_Transaction_Volume" IS NULL OR l."Previous_Day_Transaction_Volume" = 0 THEN NULL
        ELSE ROUND(((l."Daily_Transaction_Volume" - l."Previous_Day_Transaction_Volume") / l."Previous_Day_Transaction_Volume") * 100, 2)
    END AS "Volume_Growth_Pct"
FROM "LAG_PERFORMANCE" l
ORDER BY
    l."Revenue_Rank" ASC,
    l."Service_ID" ASC,
    l."Transaction_Date" ASC;
