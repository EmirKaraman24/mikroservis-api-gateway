FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

# auth-service docker-compose'da 5002 portunu kullanıyor
CMD ["flask", "--app", "src/app", "run", "--host=0.0.0.0", "--port=5002"]
