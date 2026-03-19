# dispatcher/Dockerfile
# ─────────────────────
# Dispatcher servisini calistirmak icin Docker imaji.

FROM python:3.11-slim

# Calisma dizinini ayarla
WORKDIR /app

# Bagimliliklari once kopyala (layer cache optimizasyonu)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kaynak kodu kopyala
COPY src/ ./src/

# Flask uygulamasi icin cevre degiskenleri
ENV FLASK_APP=src/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV PYTHONUNBUFFERED=1

# Uygulamayi calistir
EXPOSE 5000
CMD ["flask", "run"]
