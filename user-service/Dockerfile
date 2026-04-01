FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

# user-service docker-compose'da 5001 portunu kullanıyor
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5001"]
