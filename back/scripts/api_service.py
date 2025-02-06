from flask import Flask, jsonify, request
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, avg
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    TimestampType,
)
from pyspark.sql.window import Window
import logging
import os
import datetime
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATA_PATH = "/opt/bitnami/spark/data/crypto_data"


def create_spark_session():
    return (
        SparkSession.builder.appName("CryptoAPI")
        .config("spark.driver.memory", "2g")
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


@app.route("/crypto/latest/<symbol>", methods=["GET"])
def get_latest_crypto(symbol):
    try:
        spark = create_spark_session()
        logger.info(f"Reading data for symbol: {symbol}")

        # Lecture sans schéma prédéfini
        df = spark.read.parquet(DATA_PATH)

        # Filtrer par symbole et prendre le plus récent timestamp
        filtered_df = df.filter(col("symbol") == symbol.lower()).orderBy(
            col("timestamp").desc()
        )  # Tri descendant par timestamp

        count = filtered_df.count()
        logger.info(f"Found {count} records for {symbol}")

        if count == 0:
            return jsonify({"error": "Symbol not found"}), 404

        # Récupérer la dernière valeur (timestamp le plus récent)
        result = filtered_df.first()

        return jsonify(
            {
                "symbol": result["symbol"],
                "timestamp": result["timestamp"],  # Le timestamp est déjà formaté
                "ohlc": {
                    "open": float(result["open"]),
                    "high": float(result["high"]),
                    "low": float(result["low"]),
                    "close": float(result["close"]),
                },
            }
        )

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/crypto/history/<symbol>", methods=["GET"])
def get_crypto_history(symbol):
    try:
        spark = create_spark_session()
        from pyspark.sql.functions import (
            window,
            max,
            min,
            first,
            last,
            current_timestamp,
        )

        timeframe = request.args.get("timeframe", "1m")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        ma_period = int(request.args.get("ma_period", "20"))

        # Base query
        df = spark.read.parquet(DATA_PATH).filter(col("symbol") == symbol.lower())
        df = df.withColumn("ts", to_timestamp(col("timestamp")))

        # Calculer end_date arrondi à la minute inférieure
        if not end_date:
            now = datetime.datetime.now()
            end_date = now.replace(second=0, microsecond=0).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        # Calculer start_date basé sur end_date
        if not start_date:
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
            if timeframe == "5m":
                start_date = (end_dt - datetime.timedelta(minutes=4)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            elif timeframe == "1h":
                start_date = (end_dt - datetime.timedelta(minutes=54)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            elif timeframe == "1d":
                start_date = (end_dt - datetime.timedelta(hours=23)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

        # Configuration des fenêtres selon le timeframe
        if timeframe == "5m":
            window_duration = "1 minute"
            sliding_duration = "1 minute"
            limit_points = 5
        elif timeframe == "1h":
            window_duration = "6 minutes"
            sliding_duration = "6 minutes"
            limit_points = 10
        elif timeframe == "1d":
            window_duration = "1 hour"
            sliding_duration = "1 hour"
            limit_points = 24
        else:
            window_duration = "1 minute"
            sliding_duration = "1 minute"
            limit_points = 60

        # Pour le cas 5m, on s'assure d'avoir exactement 5 points
        if timeframe == "5m":
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
            delta = (end_dt - start_dt).total_seconds() / 60
            if (
                delta != 4
            ):  # On devrait avoir exactement 4 minutes d'écart pour avoir 5 points
                logger.warning(
                    f"Adjusting timeframe for 5m view. Delta was: {delta} minutes"
                )

        # Filtrage par date
        if start_date:
            df = df.filter(col("ts") >= start_date)
        if end_date:
            df = df.filter(col("ts") <= end_date)

        # Agrégation des données OHLC
        windowed_df = (
            df.groupBy(window(col("ts"), window_duration, sliding_duration))
            .agg(
                first("open").alias("open"),
                max("high").alias("high"),
                min("low").alias("low"),
                last("close").alias("close"),
            )
            .orderBy("window")
        )

        # Calcul de la moyenne mobile
        windowSpec = Window.orderBy("window").rowsBetween(-(ma_period - 1), 0)
        windowed_df = windowed_df.withColumn("ma", avg("close").over(windowSpec))

        # Limite du nombre de points
        windowed_df = windowed_df.limit(limit_points)

        # Conversion en format JSON
        history = []
        for row in windowed_df.collect():
            entry = {
                "timestamp": row["window"]["start"].strftime("%Y-%m-%d %H:%M:%S"),
                "ohlc": {
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                },
                "ma": float(row["ma"]) if row["ma"] is not None else None,
            }
            history.append(entry)

        period_info = {
            "5m": "5 dernières minutes, 1 point par minute",
            "1h": "Dernière heure, 1 point toutes les 6 minutes",
            "1d": "Dernier jour, 1 point par heure",
        }

        return jsonify(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "ma_period": ma_period,
                "description": period_info.get(timeframe, "1 point par minute"),
                "count": len(history),
                "history": history,
                "period": {"start": start_date, "end": end_date},
            }
        )

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/debug/storage", methods=["GET"])
def debug_storage():
    try:
        spark = create_spark_session()

        if not os.path.exists(DATA_PATH):
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Data directory does not exist",
                        "path": DATA_PATH,
                    }
                ),
                404,
            )

        df = spark.read.schema(get_schema()).parquet(DATA_PATH)

        total_count = df.count()
        symbols = [row.symbol for row in df.select("symbol").distinct().collect()]

        # Stats per symbol
        symbol_stats = {}
        for symbol in symbols:
            count = df.filter(col("symbol") == symbol).count()
            symbol_stats[symbol] = count

        return jsonify(
            {
                "status": "success",
                "total_records": total_count,
                "symbols": symbols,
                "records_per_symbol": symbol_stats,
                "data_path": DATA_PATH,
            }
        )

    except Exception as e:
        logger.error(f"Debug error: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/crypto/symbols", methods=["GET"])
def get_symbols():
    try:
        spark = create_spark_session()
        df = spark.read.schema(get_schema()).parquet(DATA_PATH)
        symbols = [row.symbol for row in df.select("symbol").distinct().collect()]

        return jsonify(symbols)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
