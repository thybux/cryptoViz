from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    TimestampType,
)
from pyspark.sql.streaming import StreamingQueryException
import logging
import time
import os

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Chemins de stockage
DATA_PATH = "/opt/bitnami/spark/data/crypto_data"
CHECKPOINT_PATH = "/opt/bitnami/spark/data/checkpoints"


def create_spark_session():
    return (
        SparkSession.builder.appName("CryptoProcessor")
        .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_PATH)
        .config(
            "spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0"
        )
        .getOrCreate()
    )


def get_schema():
    return StructType(
        [
            StructField("symbol", StringType(), True),
            StructField("timestamp", StringType(), True),
            StructField("open", DoubleType(), True),
            StructField("high", DoubleType(), True),
            StructField("low", DoubleType(), True),
            StructField("close", DoubleType(), True),
        ]
    )


def process_batch(batch_df, batch_id, spark_session):
    try:
        logger.info(f"Starting to process batch {batch_id}")

        if batch_df.isEmpty():
            logger.info(f"Batch {batch_id} is empty, skipping")
            return

        # Log des données brutes
        logger.info("Raw data received:")
        batch_df.show(5)

        # Convertir le timestamp en format approprié
        processed_df = batch_df.withColumn(
            "timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss")
        )

        logger.info("Data after timestamp conversion:")
        processed_df.show(5)

        # Déduplication
        deduplicated_df = processed_df.dropDuplicates(["symbol", "timestamp"])

        # Log des statistiques
        count = deduplicated_df.count()
        logger.info(
            f"Processing batch {batch_id} with {count} records after deduplication"
        )

        logger.info("Final data to be written:")
        deduplicated_df.show(5)

        if count > 0:
            try:
                # Écriture des données
                (
                    deduplicated_df.write.partitionBy("symbol")
                    .mode("append")
                    .parquet(DATA_PATH)
                )

                logger.info(f"Successfully wrote {count} records to {DATA_PATH}")

                # Vérification de l'écriture
                verification_df = spark_session.read.parquet(DATA_PATH)
                logger.info(
                    f"Verification - Records in Parquet: {verification_df.count()}"
                )
                verification_df.show(5)

            except Exception as write_error:
                logger.error(f"Error while writing data: {write_error}", exc_info=True)
                raise
        else:
            logger.warning("No records to write after deduplication")

    except Exception as e:
        logger.error(f"Error processing batch {batch_id}: {str(e)}", exc_info=True)
        raise


def process_stream(spark):
    try:
        # Création des répertoires si nécessaire
        os.makedirs(DATA_PATH, exist_ok=True)
        os.makedirs(CHECKPOINT_PATH, exist_ok=True)
        logger.info(f"Directories created/verified: {DATA_PATH}, {CHECKPOINT_PATH}")

        # Configuration du stream Kafka
        logger.info("Configuring Kafka stream...")
        df = (
            spark.readStream.format("kafka")
            .option("kafka.bootstrap.servers", "kafka:29092")
            .option("subscribe", "crypto_current")
            .option("startingOffsets", "earliest")  # Changed from latest to earliest
            .option("failOnDataLoss", "false")
            .load()
        )

        logger.info("Kafka stream configured successfully")

        # Parse du JSON
        schema = get_schema()
        logger.info(f"Using schema: {schema.simpleString()}")

        parsed_df = (
            df.selectExpr("CAST(value AS STRING) as json")
            .select(from_json("json", schema).alias("data"))
            .select("data.*")
        )

        logger.info("JSON parsing configuration complete")

        # Configuration et démarrage du stream
        query = (
            parsed_df.writeStream.foreachBatch(
                lambda df, id: process_batch(df, id, spark)
            )
            .option("checkpointLocation", CHECKPOINT_PATH)
            .trigger(processingTime="30 seconds")  # Changed from 1 minute to 30 seconds
            .start()
        )

        logger.info("Stream started successfully")
        return query

    except Exception as e:
        logger.error(f"Error in stream configuration: {e}", exc_info=True)
        raise


def main():
    while True:
        try:
            spark = None
            query = None

            try:
                spark = create_spark_session()
                logger.info("Spark session created successfully")

                query = process_stream(spark)
                logger.info("Stream processing started")

                query.awaitTermination()

            except StreamingQueryException as e:
                logger.error(f"Streaming error: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Processing error: {str(e)}", exc_info=True)
                raise

        except Exception as e:
            logger.error(f"General error: {str(e)}")

            if query and query.isActive:
                try:
                    query.stop()
                except Exception:
                    pass

            if spark:
                try:
                    spark.stop()
                except Exception:
                    pass

            logger.info("Waiting 10 seconds before restart...")
            time.sleep(10)
            logger.info("Restarting application...")


if __name__ == "__main__":
    main()
