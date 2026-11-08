#!/usr/bin/env bash
# Stops and removes all containers and the networks created by compose.
cd "$(dirname "$0")"
docker rm -f mitm 2>/dev/null || true     # in case a MITM run was interrupted
docker compose down
