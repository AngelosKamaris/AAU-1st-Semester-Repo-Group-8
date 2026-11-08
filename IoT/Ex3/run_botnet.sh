#!/usr/bin/env bash
# Task 5.3 (Variant 1): one device that keeps changing its ID.
#
# camera-2 floods fog_a while rotating valid camera IDs, with rate limiting ON.
# Because the limiter keys on the client IP (not the ID), the attacker should
# still be blocked. We record:
#   - camera-1 (legitimate, Zone A): should stay fast  -> mitigation still works
#   - camera-3 (Zone B): should be unaffected          -> other zone not hit
#   - camera-2 (attacker): count of 429 refusals
set -u
cd "$(dirname "$0")"
WAIT="${WAIT:-200}"
mkdir -p evidence

echo "===== Task 5.3: ID-switching flood, rate limiting ON (${WAIT}s) ====="
docker compose -f compose.yaml -f dos_idswitch.override.yaml up -d --no-deps --force-recreate camera-2 fog_a
docker compose restart camera-1 camera-3 >/dev/null
START=$(date +%s)
sleep "$WAIT"

docker logs --since "$START" camera-1 2>&1 | grep latency_ms > evidence/botnet_idswitch_camera1.txt || true
docker logs --since "$START" camera-3 2>&1 | grep latency_ms > evidence/botnet_idswitch_camera3.txt || true
REFUSED=$(docker logs --since "$START" camera-2 2>&1 | grep -c "status 429" || true)

echo "--- camera-1 (Zone A legitimate) ---"; tail -n 12 evidence/botnet_idswitch_camera1.txt
echo "--- camera-3 (Zone B reference) ---";  tail -n 6  evidence/botnet_idswitch_camera3.txt
echo "camera-2 (attacker) requests refused with 429: $REFUSED"
echo
echo "Saved to evidence/botnet_idswitch_camera1.txt and _camera3.txt"
echo "Restoring normal operation..."
docker compose -f compose.yaml -f dos_normal.override.yaml up -d --no-deps --force-recreate camera-2 fog_a
docker compose restart camera-1 camera-3 >/dev/null
