# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "8c2be482-5b5f-4b93-8a23-a7a68c6a91e7",
# META       "default_lakehouse_name": "lh_silver",
# META       "default_lakehouse_workspace_id": "2df3c932-66da-491c-b5f1-a99427e0b1e2",
# META       "known_lakehouses": [
# META         {
# META           "id": "8c2be482-5b5f-4b93-8a23-a7a68c6a91e7"
# META         },
# META         {
# META           "id": "3fbb2d91-fde3-43ab-8ddb-b327039eb012"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# Welcome to your new notebook
# Type here in the cell editor to add code!

# Added new code
from pyspark.sql.functions import current_timestamp, lit, col, to_timestamp

# 1. Read the raw transaction file from the Bronze lakehouse landing zone
# We target the absolute OneLake path since Silver is our default context here
raw_df = spark.read.format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .load("abfss://My-DataOps-DEV-Workspace@onelake.dfs.fabric.microsoft.com/lh_bronze.Lakehouse/Files/landing/mock_risk_transactions.csv")

# 2. Data Cleansing & Normalization:
# - Deduplicate records based on the primary key (TransactionID)
# - Drop any records missing a valid transaction ID
# - Cast the string transaction date into a formal SQL Timestamp type
clean_silver_df = raw_df.dropDuplicates(["TransactionID"]) \
                        .filter(col("TransactionID").isNotNull()) \
                        .withColumn("TransactionDate", to_timestamp(col("TransactionDate"))) \
                        .withColumn("IngestionTimestamp", current_timestamp()) \
                        .withColumn("SourceFileName", lit("mock_risk_transactions.csv"))

# 3. Write out the clean single-source-of-truth dataset as a managed Delta Table in Silver
clean_silver_df.write.format("delta") \
    .mode("overwrite") \
    .saveAsTable("tbl_risk_transactions_silver")

print("🥈 Cleaned data successfully written to lh_silver.tbl_risk_transactions_silver!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
