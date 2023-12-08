from ..data_processing.analytics_class import Analytics
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from re import A
import pymysql

# Create a Spark session
spark = SparkSession.builder \
    .appName("Kafka_Consumer") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.4") \
    .getOrCreate()

# Display only WARN messages
spark.sparkContext.setLogLevel('WARN')

# Define the schema for the dataset
schema = (
    StructType()
    .add("user_id", StringType(), True)
    .add("Session_Start_Time", TimestampType(), True)
    .add("Page_URL", StringType(), True)
    .add("Timestamp", TimestampType(), True)
    .add("Duration_on_Page_s", StringType(), True)
    .add("Interaction_Type", StringType(), True)
    .add("Device_Type", StringType(), True)
    .add("Browser", StringType(), True)
    .add("Country", StringType(), True)
    .add("Referrer", StringType(), True)
)

# Topic from which data will be consumed
kafka_topic = "clickstreamV1"

# Read from Kafka topic
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", kafka_topic) \
    .load() \
    .select(from_json(col("value").cast("string"), schema).alias("data"))

# Cast the value column to string
df = df.select("data.*")
df = Analytics.all_analytics(df)

# PROCESSING
def insert_into_db(row):
    # Define the connection details for your PHPMyAdmin database
    host = "p3nlmysql47plsk.secureserver.net"
    port = 3306
    database = "big_data"
    username = "root"
    password = ""
    
    conn = pymysql.connect(host=host, port=port, user=username, passwd=password, db=database)
    cursor = conn.cursor()

    # Extract the required columns from the row
    column1_value = row.name
    column2_value = row.age

    # Prepare the SQL query to insert data into the table
    sql_query = f"INSERT INTO user (name, age) VALUES ('{column1_value}', '{column2_value}')"
    
    # Execute the SQL query
    cursor.execute(sql_query)

    # Commit the changes
    conn.commit()
    conn.close()


# Write to console
query = df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()
    # .foreach(insert_into_db) \

# Wait for query termination
query.awaitTermination()