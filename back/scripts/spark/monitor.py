import os
import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_parquet_files():
    parquet_dir = "./data/crypto_data"
    
    while True:
        try:
            total_size = 0
            file_count = 0
            
            for root, dirs, files in os.walk(parquet_dir):
                for file in files:
                    if file.endswith('.parquet'):
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        total_size += size
                        file_count += 1
            
            logger.info(f"""
            [Monitoring Parquet - {datetime.now()}]
            Nombre de fichiers: {file_count}
            Taille totale: {total_size / (1024*1024):.2f} MB
            """)
            
        except Exception as e:
            logger.error(f"Erreur de monitoring: {str(e)}")
        
        time.sleep(60)  # Vérification toutes les minutes

if __name__ == "__main__":
    monitor_parquet_files()