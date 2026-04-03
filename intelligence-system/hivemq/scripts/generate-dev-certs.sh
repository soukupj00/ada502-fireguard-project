#!/usr/bin/env zsh
set -euo pipefail

CERT_DIR="${1:-./intelligence-system/hivemq/certs}"
mkdir -p "$CERT_DIR"

openssl req -x509 -newkey rsa:4096 -sha256 -days 365 \
  -nodes \
  -keyout "$CERT_DIR/server.key" \
  -out "$CERT_DIR/server.crt" \
  -subj "/CN=hivemq"

echo "Generated $CERT_DIR/server.crt and $CERT_DIR/server.key"
