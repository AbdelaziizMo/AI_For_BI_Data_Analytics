WITH DQ_Filtered_Transactions AS (
    SELECT 
        t."TransactionID",
        t."TransactionType",
        t."TotalAmount",
        t."Date",
        t."IsReversed",
        t."ID",
        ROW_NUMBER() OVER (
            PARTITION BY t."TransactionID" 
            ORDER BY t."ID" DESC
        ) AS "rn"
    FROM PLAYGROUND.TRANSACTIONS t
    WHERE t."TransactionID" IS NOT NULL
      AND t."AccountIDFrom" IS NOT NULL
      AND t."AccountIDTo" IS NOT NULL
      AND t."TotalAmount" IS NOT NULL
      AND t."TotalAmount" > 0
      AND t."TransactionType" IS NOT NULL
      AND t."IsReversed" IS NOT NULL
      AND t."IsReversed" IN (0, 1)
      AND t."Date" IS NOT NULL
      AND t."Date" <= SYSTIMESTAMP
      AND t."Date" >= :start_date
      AND t."Date" < :end_date
),
Valid_Active_Transactions AS (
    SELECT 
        t."TransactionID",
        t."TransactionType" AS "Service_ID",
        s."NameAr" AS "Service_Name",
        t."TotalAmount",
        TRUNC(t."Date") AS "Transaction_Date"
    FROM DQ_Filtered_Transactions t
    INNER JOIN PLAYGROUND.SERVICES s
        ON t."TransactionType" = s."ID"
    WHERE t."rn" = 1
      AND t."IsReversed" = 0
),
Daily_Aggregates AS (
    SELECT 
        "Service_ID",
        "Service_Name",
        "Transaction_Date",
        COUNT("TransactionID") AS "Daily_Transaction_Volume",
        SUM("TotalAmount") AS "Daily_Revenue",
        ROUND(AVG("TotalAmount"), 3) AS "Avg_Transaction_Amount"
    FROM Valid_Active_Transactions
    GROUP BY 
        "Service_ID",
        "Service_Name",
        "Transaction_Date"
),
Service_Overall_Totals AS (
    SELECT 
        "Service_ID",
        SUM("Daily_Transaction_Volume") AS "Service_Total_Volume",
        SUM("Daily_Revenue") AS "Service_Total_Revenue",
        DENSE_RANK() OVER (ORDER BY SUM("Daily_Revenue") DESC) AS "Overall_Revenue_Rank",
        DENSE_RANK() OVER (ORDER BY SUM("Daily_Transaction_Volume") DESC) AS "Overall_Volume_Rank"
    FROM Daily_Aggregates
    GROUP BY "Service_ID"
),
Daily_With_Lag AS (
    SELECT 
        d."Service_ID",
        d."Service_Name",
        d."Transaction_Date",
        d."Daily_Transaction_Volume",
        d."Daily_Revenue",
        d."Avg_Transaction_Amount",
        o."Service_Total_Volume",
        o."Service_Total_Revenue",
        o."Overall_Revenue_Rank",
        o."Overall_Volume_Rank",
        LAG(d."Daily_Revenue", 1) OVER (
            PARTITION BY d."Service_ID" 
            ORDER BY d."Transaction_Date" ASC
        ) AS "Prev_Day_Revenue",
        LAG(d."Daily_Transaction_Volume", 1) OVER (
            PARTITION BY d."Service_ID" 
            ORDER BY d."Transaction_Date" ASC
        ) AS "Prev_Day_Volume"
    FROM Daily_Aggregates d
    JOIN Service_Overall_Totals o
        ON d."Service_ID" = o."Service_ID"
)
SELECT 
    "Service_ID",
    "Service_Name",
    "Transaction_Date",
    "Daily_Transaction_Volume",
    "Daily_Revenue",
    "Avg_Transaction_Amount",
    "Service_Total_Volume",
    "Service_Total_Revenue",
    "Overall_Revenue_Rank",
    "Overall_Volume_Rank",
    "Prev_Day_Revenue",
    "Prev_Day_Volume",
    CASE 
        WHEN "Prev_Day_Revenue" IS NULL OR "Prev_Day_Revenue" = 0 THEN NULL
        ELSE ROUND((("Daily_Revenue" - "Prev_Day_Revenue") / "Prev_Day_Revenue") * 100, 2)
    END AS "Revenue_Growth_Pct",
    CASE 
        WHEN "Prev_Day_Volume" IS NULL OR "Prev_Day_Volume" = 0 THEN NULL
        ELSE ROUND((("Daily_Transaction_Volume" - "Prev_Day_Volume") / "Prev_Day_Volume") * 100, 2)
    END AS "Volume_Growth_Pct"
FROM Daily_With_Lag
ORDER BY 
    "Overall_Revenue_Rank" ASC,
    "Service_ID" ASC,
    "Transaction_Date" ASC;
