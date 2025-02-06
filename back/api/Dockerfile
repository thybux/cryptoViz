FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk && \
    apt-get clean

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./api/app.py .

CMD ["python", "api_service.py"]
