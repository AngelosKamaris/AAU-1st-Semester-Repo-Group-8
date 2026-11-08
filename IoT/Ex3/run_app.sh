#!/usr/bin/env bash
# Builds and starts the whole system: 3 cameras, 2 fog nodes, cloud, logger.
set -e
cd "$(dirname "$0")"

# Camera tokens live in .env, which is not committed. Create it from the template if missing.
[ -f .env ] || cp ".env copy" .env

docker compose up --build -d
docker compose ps
echo
echo "System started. Follow a fog node with:  docker logs -f fog_a"
