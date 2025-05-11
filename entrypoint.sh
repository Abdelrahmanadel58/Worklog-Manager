#!/bin/sh

echo "Waiting for Postgres..."
while ! nc -z db 5432; do
  sleep 1
done

echo "Postgres is up."

echo "Running database migrations..."
flask db upgrade

echo "Starting Flask app..."
exec flask run --host=0.0.0.0