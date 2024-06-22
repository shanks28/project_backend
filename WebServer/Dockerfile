FROM python:3.12.3
LABEL authors="BRIDGES"

# Install PostgreSQL client
RUN apt-get update && apt-get install -y postgresql-client

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080

CMD bash -c '\
    until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "\q"; do \
        >&2 echo "Postgres is unavailable - sleeping"; \
        sleep 1; \
    done && \
    >&2 echo "Postgres is up - executing command" && \
    exec fastapi dev app.py --port 8080 --host 0.0.0.0 \
'