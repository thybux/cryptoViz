from confluent_kafka import Producer
import json
import logging
from datetime import datetime
import time
import pandas as pd
from pycoingecko import CoinGeckoAPI
from binance.client import Client


from config import (
    KAFKA_BROKER,
    CRYPTO_SYMBOLS,
    KAFKA_TOPIC_CURRENT,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

symbol_map = {
    "bitcoin": "BTCUSDT",
    "ethereum": "ETHUSDT",
    "binancecoin": "BNBUSDT",
    "solana": "SOLUSDT",
}


class CryptoProducer:
    def __init__(self):
        kafka_conf = {
            "bootstrap.servers": KAFKA_BROKER,
            "debug": "broker,topic,msg",
        }
        logger.info("Initialisation du producteur Kafka...")
        self.producer = Producer(kafka_conf)
        self.cg = CoinGeckoAPI()
        logger.info("Producteur initialisé avec succès")

    def delivery_report(self, err, msg):
        """Callback appelé pour chaque message produit"""
        if err is not None:
            logger.error(f"Erreur de livraison du message: {err}")
        else:
            logger.info(
                f"Message livré avec succès à {msg.topic()} [partition {msg.partition()}]"
            )

    def get_current_ohlc(
        self,
        coins=CRYPTO_SYMBOLS,
        vs_currency="usdt",
        interval=Client.KLINE_INTERVAL_1MINUTE,
    ):
        try:
            results = []
            client = Client(None, None)  # Pas besoin de clés pour les données publiques
            current_time = datetime.now()
            logger.info(f"Heure actuelle: {current_time}")

            # Map des symboles pour Binance
            symbol_map = {
                "bitcoin": "BTCUSDT",
                "ethereum": "ETHUSDT",
                "binancecoin": "BNBUSDT",
                "solana": "SOLUSDT",
            }

            for coin_id in coins:
                try:
                    binance_symbol = symbol_map.get(coin_id.lower())
                    if not binance_symbol:
                        logger.warning(f"Symbole non trouvé pour {coin_id}")
                        continue

                    logger.info(f"Récupération des données pour {binance_symbol}")

                    # Récupérer la dernière bougie
                    klines = client.get_klines(
                        symbol=binance_symbol,
                        interval=interval,
                        limit=1,  # Seulement la dernière bougie
                    )

                    if klines:
                        for kline in klines:
                            timestamp = datetime.fromtimestamp(kline[0] / 1000)

                            if timestamp <= current_time:
                                data = {
                                    "symbol": coin_id,
                                    "timestamp": timestamp.strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),
                                    "open": float(kline[1]),
                                    "high": float(kline[2]),
                                    "low": float(kline[3]),
                                    "close": float(kline[4]),
                                }
                                logger.info(f"Point de données valide: {data}")
                                results.append(data)

                    time.sleep(0.5)  # Court délai entre les requêtes

                except Exception as e:
                    logger.error(f"Erreur pour {coin_id}: {str(e)}")
                    continue

            results.sort(key=lambda x: x["timestamp"])
            return results

        except Exception as e:
            logger.error(f"Erreur globale: {str(e)}")
            return None

    def run(self):
        while True:
            try:
                logger.info("Récupération des données OHLC...")
                current_data = self.get_current_ohlc()

                if current_data:
                    logger.info(f"Données reçues: {len(current_data)} éléments")
                    for data in current_data:
                        json_data = json.dumps(data).encode("utf-8")
                        self.producer.produce(
                            KAFKA_TOPIC_CURRENT,
                            value=json_data,
                            callback=self.delivery_report,
                        )
                        logger.debug(f"Données envoyées pour {data['symbol']}")

                    logger.info("Flush des messages...")
                    self.producer.poll(0)
                    self.producer.flush()

                    logger.info("Attente avant le prochain cycle (15 minutes)...")
                    time.sleep(60 - datetime.now().second)
                else:
                    logger.warning("Aucune donnée reçue")
                    time.sleep(60)

            except Exception as e:
                logger.error(
                    f"Erreur dans la boucle principale: {str(e)}", exc_info=True
                )
                time.sleep(60)


if __name__ == "__main__":
    producer = CryptoProducer()
    producer.run()
