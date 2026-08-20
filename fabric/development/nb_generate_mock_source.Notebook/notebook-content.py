# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "3fbb2d91-fde3-43ab-8ddb-b327039eb012",
# META       "default_lakehouse_name": "lh_bronze",
# META       "default_lakehouse_workspace_id": "2df3c932-66da-491c-b5f1-a99427e0b1e2",
# META       "known_lakehouses": [
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

import pandas as pd
from datetime import datetime, timedelta
import random

# 1. Generate 1,000 rows of mock risk transaction records to mimic real-world requirements
mock_data = {
    "TransactionID": [1000 + i for i in range(1000)],
    "CustomerID": [random.randint(50000, 99999) for _ in range(1000)],
    "RiskScore": [round(random.uniform(0.0, 1.0), 2) for _ in range(1000)],
    "TransactionAmount": [round(random.uniform(10.0, 5000.0), 2) for _ in range(1000)],
    "TransactionDate": [(datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S") for _ in range(1000)],
    "Status": [random.choice(["Approved", "Pending", "Flagged_Review"]) for _ in range(1000)]
}

df = pd.DataFrame(mock_data)

# 2. Target path pointing directly to the landing folder inside the attached lh_bronze lakehouse
# Note: "default" targets the lakehouse set as the active default context for this notebook
target_path = "/lakehouse/default/Files/landing/mock_risk_transactions.csv"

# 3. Write out the transactional file
df.to_csv(target_path, index=False)
print("✅ Mock risk transaction data successfully dropped into 'lh_bronze/Files/landing/'!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
