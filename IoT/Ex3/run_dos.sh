#!/usr/bin/env bash
# Task 5.1 + 5.2: DoS attack and per-client rate-limiting mitigation.
#
# Runs three phases and records camera-1 (legitimate, Zone A) latency each time:
#   1) normal     - camera-2 is a normal camera, no rate limit (baseline)
#   2) attack     - camera-2 floods fog_a with 20 processes, no rate limit
#   3) mitigated  - same flood, but fog_a rate limiting is ON
# camera-3 (Zone B) is recorded in the baseline as an unaffected reference.
#
# Each phase runs for WAIT seconds (default 200). Raise it if a full 10-image
# run doesn't finish, e.g.  WAIT=300 ./run_dos.sh
set -u
cd "$(dirname "$0")"
WAIT="${WAIT:-200}"
mkdir -p evidence

phase() {
    local name=$1 override=$2
    echo "===== PHASE: $name (${WAIT}s) ====="
    # Recreate only camera-2 and fog_a with this phase's settings.
    docker compose -f compose.yaml -f "$override" up -d --no-deps --force-recreate camera-2 fog_a
    # Restart the legitimate cameras so each phase starts a clean image run.
    docker compose restart camera-1 camera-3 >/dev/null
    local start; start=$(date +%s)
    sleep "$WAIT"
    docker logs --since "$start" camera-1 2>&1 | grep latency_ms > "evidence/dos_${name}_camera1.txt" || true
    echo "camera-1 latency lines saved to evidence/dos_${name}_camera1.txt"
    tail -n 12 "evidence/dos_${name}_camera1.txt"
    if [ "$name" = "normal" ]; then
        docker logs --since "$start" camera-3 2>&1 | grep latency_ms > "evidence/dos_normal_camera3.txt" || true
        echo "(camera-3 Zone B reference saved to evidence/dos_normal_camera3.txt)"
    fi
    if [ "$name" = "mitigated" ]; then
        docker logs --since "$start" camera-2 2>&1 | grep -c "status 429" \
            | xargs -I{} echo "camera-2 requests refused with 429: {}"
    fi
    echo
}

phase normal    dos_normal.override.yaml
phase attack    dos_attack.override.yaml
phase mitigated dos_mitigated.override.yaml

echo "Done. Restoring normal operation (camera-2 normal, rate limit off)..."
docker compose -f compose.yaml -f dos_normal.override.yaml up -d --no-deps --force-recreate camera-2 fog_a
docker compose restart camera-1 camera-3 >/dev/null
echo "Compare: evidence/dos_normal_camera1.txt  vs  dos_attack_camera1.txt  vs  dos_mitigated_camera1.txt"
