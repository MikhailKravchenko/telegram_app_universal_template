#!/bin/bash
source .env

debug=$(cat config.yaml | shyaml get-value DEBUG)

echo "Starting server, debug mode: $debug"

if [ $debug = "True" ]; then
  python manage.py runserver 0.0.0.0:$DJANGO_PORT
else
  # Daphne для ASGI (WebSocket + HTTP)
  # --bind - привязка к порту
  daphne --bind 0.0.0.0 --port $DJANGO_PORT src.asgi:application
fi