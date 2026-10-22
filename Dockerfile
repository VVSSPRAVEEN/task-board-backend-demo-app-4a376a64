FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libc-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

ENV PORT=8001
ENV DB_PATH=/data/tasks.db
ENV PERSISTENT_DATA_PATH=/data

RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app /data
USER appuser

CMD ["python", "-m", "app"]
