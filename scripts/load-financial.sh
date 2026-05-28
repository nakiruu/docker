#!/bin/bash
# Streams the Financial dataset from the public CTU relational learning repository
# into the local MariaDB instance. Runs once via docker-entrypoint-initdb.d;
# subsequent starts reuse the persisted Docker volume.
set -eo pipefail

echo "==> Streaming Financial dataset from relational.fel.cvut.cz (~78 MB)..."
echo "    8 tables | 1,090,086 rows | prediction target: loan.status"

mysqldump \
    --host=relational.fel.cvut.cz \
    --port=3306 \
    --user=guest \
    --password=ctu-relational \
    --no-tablespaces \
    --no-create-db \
    --single-transaction \
    financial \
| mysql \
    --user=root \
    --password="${MARIADB_ROOT_PASSWORD}" \
    "${MARIADB_DATABASE}"

echo "==> Financial dataset loaded successfully!"
