#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 DOMAIN EMAIL" >&2
  exit 2
fi

DOMAIN="$1"
EMAIL="$2"

set +e
docker run --rm -it \
  -v certbot-certs:/etc/letsencrypt \
  -v certbot-var:/var/lib/letsencrypt \
  certbot/certbot certonly \
  --manual \
  --preferred-challenges dns \
  --agree-tos \
  --manual-public-ip-logging-ok \
  --email "${EMAIL}" \
  -d "${DOMAIN}"
status=$?
set -e

if [ "$status" -ne 0 ]; then
  echo "TXT record verification failed. Check propagation with: dig +short TXT _acme-challenge.${DOMAIN}" >&2
  exit "$status"
fi
