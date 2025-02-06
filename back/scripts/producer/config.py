import os
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le fichier .env
load_dotenv("../../.env")

# Configuration CoinMarketCap
CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"

# Configuration Kafka
KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
# KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC_CURRENT = "crypto_current"
KAFKA_TOPIC_HISTORICAL = "crypto_historical"

# Liste des cryptos à suivre
CRYPTO_SYMBOLS = [
    "bitcoin",
    "solana",
    "ethereum",
    "binancecoin",
]

# Intervalles de temps pour les données historiques
TIMEFRAMES = ["5m", "15m", "1h"]

# Limite de crédits quotidienne (10000/30 pour rester dans la limite mensuelle)
DAILY_CREDIT_LIMIT = 333
