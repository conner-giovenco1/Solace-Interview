import sys
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
import pandas as pd

# Glue job setup
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glue_ctx = GlueContext(sc)
job = Job(glue_ctx)
job.init(args['JOB_NAME'], args)

# Read enriched data from the Glue catalog (DynamoDB table)
dyf = glue_ctx.create_dynamic_frame.from_catalog(
    database="analytics_db",
    table_name="user_events"
)
df = dyf.toDF()

# Convert to pandas for richer transformations
pdf = df.toPandas()

# Transformation examples:
# 1. Count of purchases by city
city_counts = pdf.groupby(pdf['location'].apply(lambda l: l.get('city', 'Unknown'))).size()
pdf['purchasesByCity'] = pdf['location'].apply(lambda l: city_counts.get(l.get('city'), 0))

# 2. Average spend per purchase
pdf['avgSpendPerPurchase'] = pdf['totalSpent'] / pdf['timesPurchased'].replace(0, 1)

# 3. Flag high-value users (spent > $200)
pdf['highValueUser'] = pdf['totalSpent'] > 200

# Prepare back to Spark DataFrame
spark_df = glue_ctx.spark_session.createDataFrame(pdf)

# Write out Parquet, partitioned by state and eventDate
spark_df.withColumn(
    "eventDate",
    spark_df["eventTimestamp"].substr(1, 10)
).write.mode("overwrite") \
    .partitionBy("location.state", "eventDate") \
    .parquet("s3://your-bucket/processed-events/")

job.commit()
