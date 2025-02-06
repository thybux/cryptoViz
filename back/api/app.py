from flask import Flask, jsonify, request
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, min, max, col, expr
import pandas as pd
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_PATH = "/opt/bitnami/spark/data/crypto_data"


def create_spark_session():
    return (
        SparkSession.builder.appName("CryptoAPI")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )


@app.route("/crypto/latest/<symbol>", methods=["GET"])
def get_latest_crypto(symbol):
    try:
        spark = create_spark_session()
        df = (
            spark.read.parquet(DATA_PATH)
            .filter(f"symbol = '{symbol.lower()}'")
            .orderBy("timestamp", ascending=False)
            .limit(1)
        )

        if df.count() == 0:
            return jsonify({"error": "Symbol not found"}), 404

        result = df.toPandas().to_dict("records")[0]
        return jsonify(
            {
                "symbol": result["symbol"],
                "timestamp": str(result["timestamp"]),
                "ohlc": {
                    "open": float(result["open"]),
                    "high": float(result["high"]),
                    "low": float(result["low"]),
                    "close": float(result["close"]),
                },
            }
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/crypto/symbols", methods=["GET"])
def get_symbols():
    try:
        spark = create_spark_session()
        df = spark.read.parquet(DATA_PATH)
        symbols = [row.symbol for row in df.select("symbol").distinct().collect()]

        if not symbols:
            return jsonify({"error": "No symbols found"}), 404

        return jsonify(symbols)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/crypto/stats/<symbol>", methods=["GET"])
def get_crypto_stats(symbol):
    try:
        spark = create_spark_session()
        df = spark.read.parquet(DATA_PATH).filter(f"symbol = '{symbol.lower()}'")

        if df.count() == 0:
            return jsonify({"error": "Symbol not found"}), 404

        # Statistiques OHLC
        stats = df.agg(
            min("low").alias("lowest_price"),
            max("high").alias("highest_price"),
            avg("close").alias("average_close"),
            min("timestamp").alias("first_date"),
            max("timestamp").alias("last_date"),
        ).collect()[0]

        # Variation de prix
        first_last = df.orderBy("timestamp").select("open", "close").collect()

        if len(first_last) >= 2:
            first_price = first_last[0]["open"]
            last_price = first_last[-1]["close"]
            price_change = ((last_price - first_price) / first_price) * 100
        else:
            price_change = 0

        return jsonify(
            {
                "symbol": symbol,
                "statistics": {
                    "lowest_price": float(stats["lowest_price"]),
                    "highest_price": float(stats["highest_price"]),
                    "average_close": float(stats["average_close"]),
                    "total_price_change_percent": float(price_change),
                    "period": {
                        "start": str(stats["first_date"]),
                        "end": str(stats["last_date"]),
                    },
                },
            }
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/crypto/history/<symbol>", methods=["GET"])
def get_crypto_history(symbol):
    try:
        spark = create_spark_session()

        # Construction de la requête de base
        base_query = f"symbol = '{symbol.lower()}'"

        # Gestion des dates optionnelles
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        query = base_query

        # Si les dates sont fournies, les ajouter à la requête
        if start_date:
            try:
                # Convertir en format datetime pour validation
                datetime.strptime(start_date, "%Y-%m-%d")
                query += f" AND timestamp >= '{start_date}'"
            except ValueError:
                return (
                    jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}),
                    400,
                )

        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
                query += f" AND timestamp <= '{end_date}'"
            except ValueError:
                return (
                    jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}),
                    400,
                )

        logger.info(f"Executing query with filter: {query}")

        # Lecture des données
        df = spark.read.parquet(DATA_PATH).filter(query).orderBy("timestamp")

        # Vérification si des données existent
        count = df.count()
        if count == 0:
            return (
                jsonify(
                    {
                        "symbol": symbol,
                        "error": "No data found for the specified criteria",
                        "history": [],
                    }
                ),
                404,
            )

        logger.info(f"Found {count} records for {symbol}")

        # Conversion en Pandas pour le formatage
        pandas_df = df.toPandas()

        # Formatage des résultats
        results = []
        for _, row in pandas_df.iterrows():
            results.append(
                {
                    "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "ohlc": {
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                    },
                }
            )

        response = {"symbol": symbol, "count": len(results), "history": results}

        if start_date or end_date:
            response["period"] = {
                "start": start_date if start_date else "earliest",
                "end": end_date if end_date else "latest",
            }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in get_crypto_history: {str(e)}", exc_info=True)
        return (
            jsonify(
                {
                    "symbol": symbol,
                    "error": str(e),
                    "details": "An error occurred while fetching historical data",
                }
            ),
            500,
        )


@app.route("/crypto/variations/<symbol>", methods=["GET"])
def get_crypto_variations(symbol):
    try:
        spark = create_spark_session()
        df = (
            spark.read.parquet(DATA_PATH)
            .filter(f"symbol = '{symbol.lower()}'")
            .orderBy("timestamp", ascending=False)
        )

        if df.count() == 0:
            return jsonify({"error": "Symbol not found"}), 404

        latest = df.first()
        variations = {"current_price": float(latest["close"]), "variations": {}}

        periods = {
            "24h": "interval 24 hours",
            "7d": "interval 7 days",
            "30d": "interval 30 days",
        }

        for period, interval in periods.items():
            old_price = (
                df.filter(f"timestamp <= date_sub('{latest['timestamp']}', {interval})")
                .orderBy("timestamp", ascending=False)
                .first()
            )

            if old_price:
                variation = (
                    (latest["close"] - old_price["close"]) / old_price["close"]
                ) * 100
                variations["variations"][period] = float(variation)
            else:
                variations["variations"][period] = None

        return jsonify(variations)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
