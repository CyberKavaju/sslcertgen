#!/bin/sh
set -eu

SSL_DIR="/etc/nginx/ssl"
CERT_PATH="${SSL_DIR}/cert.pem"
KEY_PATH="${SSL_DIR}/key.pem"

mkdir -p "${SSL_DIR}"

if [ ! -f "${CERT_PATH}" ] || [ ! -f "${KEY_PATH}" ]; then
  openssl req \
    -x509 \
    -newkey rsa:2048 \
    -sha256 \
    -nodes \
    -days 365 \
    -subj "/CN=localhost" \
    -keyout "${KEY_PATH}" \
    -out "${CERT_PATH}"
fi

chmod 644 "${CERT_PATH}"
chmod 640 "${KEY_PATH}"
chown nginx:nginx "${CERT_PATH}" "${KEY_PATH}"
