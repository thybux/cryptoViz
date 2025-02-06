FROM bitnami/spark:latest

# Ajout des dépendances PostgreSQL et Kafka
USER root
RUN curl -O https://jdbc.postgresql.org/download/postgresql-42.2.23.jar && \
    mv postgresql-42.2.23.jar /opt/bitnami/spark/jars/

COPY scripts/spark/* /opt/spark/scripts/

USER 1001