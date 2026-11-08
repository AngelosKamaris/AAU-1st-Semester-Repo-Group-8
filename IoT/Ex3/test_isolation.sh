#!/usr/bin/env bash
# Task 1.3: a camera reaches its own fog node but not the cloud or the other zone.
# Only the fog nodes can reach the cloud over backbone_net.
cd "$(dirname "$0")"
mkdir -p evidence
OUT=evidence/isolation_test.txt

# Try a TCP connection to port 8000 from inside a container; print REACHABLE or BLOCKED.
check() {
    local from=$1 ip=$2 label=$3
    local result
    result=$(docker exec "$from" python -c "
import socket
s = socket.socket(); s.settimeout(3)
try:
    s.connect(('$ip', 8000)); print('REACHABLE')
except Exception as e:
    print('BLOCKED (' + str(e) + ')')
")
    printf '%-9s -> %-26s %s\n' "$from" "$label ($ip)" "$result"
}

{
    echo "=== Task 1.3 network isolation test ($(date -u)) ==="
    check camera-1 1.1.2.2 "fog_a own zone"
    check camera-1 1.1.1.4 "cloud backbone"
    check camera-1 1.1.3.2 "fog_b other zone"
    check camera-3 1.1.3.2 "fog_b own zone"
    check camera-3 1.1.1.4 "cloud backbone"
    check fog_a    1.1.1.4 "cloud backbone"
} | tee "$OUT"
echo
echo "Saved to $OUT"
