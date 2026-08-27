# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "28036db7-06de-4d98-926b-e3390fce3094",
# META       "default_lakehouse_name": "lh_gold",
# META       "default_lakehouse_workspace_id": "2df3c932-66da-491c-b5f1-a99427e0b1e2",
# META       "known_lakehouses": [
# META         {
# META           "id": "28036db7-06de-4d98-926b-e3390fce3094"
# META         },
# META         {
# META           "id": "8c2be482-5b5f-4b93-8a23-a7a68c6a91e7"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# Welcome to your new notebook
# Type here in the cell editor to add code!



from pyspark.sql.functions import avg, sum, count, round

# 1. Read clean records directly from the absolute OneLake ABFS URI path
exact_silver_path = "abfss://2df3c932-66da-491c-b5f1-a99427e0b1e2@onelake.dfs.fabric.microsoft.com/8c2be482-5b5f-4b93-8a23-a7a68c6a91e7/Tables/dbo/tbl_risk_transactions_silver"

silver_data = spark.read.format("delta").load(exact_silver_path)

# 2. Compute Corporate Analytical Metrics (Gold Aggregations)
# - Group by transaction date and status
# - Calculate absolute financial volumes, average risk metrics, and aggregate item volumes
gold_reporting_df = silver_data.groupBy("TransactionDate", "Status") \
    .agg(
        round(sum("TransactionAmount"), 2).alias("TotalFinancialAmount"),
        round(avg("RiskScore"), 4).alias("AverageRiskScore"),
        count("TransactionID").alias("TotalTransactionCount")
    )

# 3. Write data directly into your default Gold Lakehouse as a managed table
gold_reporting_df.write.format("delta") \
    .mode("overwrite") \
    .saveAsTable("fact_risk_summary")

print("🥇 Corporate Gold analytics engine successfully populated: fact_risk_summary!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
