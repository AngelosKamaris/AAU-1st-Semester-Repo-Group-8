#!/usr/bin/env bash
# Task 5.4: ID spoofing.
# Adds a new container, "camera-spoof" (1.1.2.5), to zone_a_net that sends
# requests claiming to be "camera-1", but it only has its own token, not camera-1's 
# real one, exactly like a real outside attacker who doesn't know the secret. 

set -u
cd "$(dirname "$0")"
WAIT="${WAIT:-20}"
mkdir -p evidence

echo "===== Task 5.4: ID spoofing (${WAIT}s) ====="
docker compose -f compose.yaml -f spoof_attack.override.yaml up -d --build camera-spoof
START=$(date +%s)
sleep "$WAIT"

docker logs --since "$START" camera-spoof 2>&1 | tee evidence/spoof_camera_spoof.txt || true
docker logs --since "$START" fog_a 2>&1 | grep -iE "reject|401" > evidence/spoof_fog_a.txt || true
docker logs --since "$START" camera-1 2>&1 | grep latency_ms > evidence/spoof_camera1_legit.txt || true

echo
echo "--- rogue container camera-spoof (1.1.2.5), claiming to be camera-1 (1.1.2.3) ---"
tail -n 6 evidence/spoof_camera_spoof.txt
echo
echo "--- fog_a's reaction (expect a rejection logged for 1.1.2.5, NOT camera-1's real 1.1.2.3) ---"
if [ -s evidence/spoof_fog_a.txt ]; then
    tail -n 10 evidence/spoof_fog_a.txt
else
    echo "(nothing matched 'reject'/'401' in fog_a's log in this window - try a longer WAIT)"
fi
echo
echo "--- real camera-1 (1.1.2.3), should be completely unaffected ---"
tail -n 6 evidence/spoof_camera1_legit.txt

echo
echo "Saved to evidence/spoof_camera_spoof.txt, evidence/spoof_fog_a.txt, evidence/spoof_camera1_legit.txt"
echo "Removing the rogue container (the rest of the system was never touched)..."
docker compose -f compose.yaml -f spoof_attack.override.yaml rm -sf camera-spoof >/dev/null