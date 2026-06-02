#!/bin/sh
set -eu

docker run --rm \
  -v certbot-certs:/etc/letsencrypt \
  -v certbot-var:/var/lib/letsencrypt \
  certbot/certbot renew

docker compose -f deployment/docker-compose.prod.yml kill -s HUP nginx
