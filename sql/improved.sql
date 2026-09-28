WITH "dedup_transactions" AS (
    SELECT 
        t."TransactionID",
        t."AccountIDFrom",
        t."AccountIDTo",
        t."TotalAmount",
        t."TransactionType" AS "Service_ID",
        t."IsReversed",
        t."Date" AS "TransactionTimestamp",
        TRUNC(t."Date") AS "Transaction_Date",
        t."ID",
        ROW_NUMBER() OVER (
            PARTITION BY t."TransactionID" 
            ORDER BY t."ID" DESC
        ) AS "RowNum"
    FROM PLAYGROUND.TRANSACTIONS t
    WHERE 
        t."TransactionID" IS NOT NULL
        AND t."AccountIDFrom" IS NOT NULL
        AND t."AccountIDTo" IS NOT NULL
        AND t."TotalAmount" IS NOT NULL
        AND t."TransactionType" IS NOT NULL
        AND t."IsReversed" IS NOT NULL
        AND t."Date" IS NOT NULL
        AND t."TotalAmount" > 0
        AND t."IsReversed" = 0
        AND t."Date" <= SYSTIMESTAMP
        AND t."Date" >= :start_date
        AND t."Date" < :end_date
),

"valid_transactions" AS (
    SELECT 
        dt."TransactionID",
        dt."TotalAmount",
        dt."Service_ID",
        dt."Transaction_Date",
        s."NameAr" AS "Service_Name"
    FROM "dedup_transactions" dt
    INNER JOIN PLAYGROUND.SERVICES s 
        ON dt."Service_ID" = s."ID"
    WHERE dt."RowNum" = 1
),

"daily_service_metrics" AS (
    SELECT 
        vt."Service_ID",
        vt."Service_Name",
        vt."Transaction_Date",
        COUNT(vt."TransactionID") AS "Daily_Transaction_Volume",
        SUM(vt."TotalAmount") AS "Daily_Revenue",
        ROUND(AVG(vt."TotalAmount"), 3) AS "Average_Transaction_Amount"
    FROM "valid_transactions" vt
    GROUP BY 
        vt."Service_ID",
        vt."Service_Name",
        vt."Transaction_Date"
),

"service_overall_ranks" AS (
    SELECT 
        d."Service_ID",
        SUM(d."Daily_Revenue") AS "Total_Revenue",
        SUM(d."Daily_Transaction_Volume") AS "Total_Transaction_Volume",
        DENSE_RANK() OVER (ORDER BY SUM(d."Daily_Revenue") DESC) AS "Revenue_Rank",
        DENSE_RANK() OVER (ORDER BY SUM(d."Daily_Transaction_Volume") DESC) AS "Volume_Rank"
    FROM "daily_service_metrics" d
    GROUP BY d."Service_ID"
),

"daily_trends" AS (
    SELECT 
        d."Service_ID",
        d."Service_Name",
        d."Transaction_Date",
        d."Daily_Transaction_Volume",
        d."Daily_Revenue",
        d."Average_Transaction_Amount",
        r."Total_Revenue",
        r."Total_Transaction_Volume",
        r."Revenue_Rank",
        r."Volume_Rank",
        LAG(d."Daily_Revenue", 1) OVER (
            PARTITION BY d."Service_ID" 
            ORDER BY d."Transaction_Date" ASC
        ) AS "Previous_Day_Revenue",
        LAG(d."Daily_Transaction_Volume", 1) OVER (
            PARTITION BY d."Service_ID" 
            ORDER BY d."Transaction_Date" ASC
        ) AS "Previous_Day_Transaction_Volume"
    FROM "daily_service_metrics" d
    INNER JOIN "service_overall_ranks" r 
        ON d."Service_ID" = r."Service_ID"
)

SELECT 
    t."Service_ID",
    t."Service_Name",
    t."Transaction_Date",
    t."Daily_Transaction_Volume",
    t."Daily_Revenue",
    t."Average_Transaction_Amount",
    t."Total_Revenue",
    t."Total_Transaction_Volume",
    t."Revenue_Rank",
    t."Volume_Rank",
    t."Previous_Day_Revenue",
    t."Previous_Day_Transaction_Volume",
    CASE 
        WHEN t."Previous_Day_Revenue" IS NULL OR t."Previous_Day_Revenue" = 0 THEN NULL
        ELSE ROUND(((t."Daily_Revenue" - t."Previous_Day_Revenue") / t."Previous_Day_Revenue") * 100, 2)
    END AS "Revenue_Growth_Pct",
    CASE 
        WHEN t."Previous_Day_Transaction_Volume" IS NULL OR t."Previous_Day_Transaction_Volume" = 0 THEN NULL
        ELSE ROUND(((t."Daily_Transaction_Volume" - t."Previous_Day_Transaction_Volume") / t."Previous_Day_Transaction_Volume") * 100, 2)
    END AS "Volume_Growth_Pct"
FROM "daily_trends" t
ORDER BY 
    t."Revenue_Rank" ASC,
    t."Service_ID" ASC,
    t."Transaction_Date" ASC;
