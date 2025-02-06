#!/bin/bash

# Création des répertoires nécessaires
mkdir -p /opt/bitnami/spark/data/crypto_data /opt/bitnami/spark/data/checkpoints /opt/bitnami/spark/data/logs
chown -R 1001:1001 /opt/bitnami/spark/data
chmod -R 777 /opt/bitnami/spark/data

# Démarrage du master Spark
echo "Starting Spark Master..."
/opt/bitnami/scripts/spark/entrypoint.sh /opt/bitnami/scripts/spark/run.sh > /opt/bitnami/spark/data/logs/spark-master.log 2>&1 &

# Attente de 10 secondes pour s'assurer que le master est complètement démarré
echo "Waiting for Spark Master to initialize..."
sleep 10

echo "Starting Spark application..."
/opt/bitnami/spark/bin/spark-submit \
    --master spark://spark-master:7077 \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0 \
    --conf spark.driver.memory=2g \
    --conf spark.executor.memory=2g \
    --conf spark.eventLog.enabled=true \
    --conf spark.eventLog.dir=/opt/bitnami/spark/data/logs \
    --conf spark.driver.supervise=true \
    --conf spark.submit.deployMode=client \
    --verbose \
    /opt/bitnami/spark/scripts/crypto_processor.py \
    2>&1 | tee /opt/bitnami/spark/data/logs/spark-submit.log

# En cas d'échec, afficher les logs
if [ $? -ne 0 ]; then
    echo "ERROR: Spark Submit failed. Checking logs:"
    cat /opt/bitnami/spark/data/logs/spark-submit.log
fi

# Garde le conteneur en vie et affiche les logs
tail -f /opt/bitnami/spark/data/logs/spark-master.log
