#!/bin/bash
set -e

echo "==> Running metadata DB migrations..."
superset db upgrade

echo "==> Creating admin user (${ADMIN_USERNAME:-admin})..."
superset fab create-admin \
    --username  "${ADMIN_USERNAME:-admin}" \
    --firstname "Superset" \
    --lastname  "Admin" \
    --email     "${ADMIN_EMAIL:-admin@example.com}" \
    --password  "${ADMIN_PASSWORD:-admin}" 2>&1 \
  | grep -v "already exist" || true

echo "==> Initializing roles and permissions..."
superset init

echo "==> Superset is ready."
