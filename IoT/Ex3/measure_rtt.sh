#!/usr/bin/env bash
# Task 1.5: show the configured WAN delay and measure the fog<->cloud round-trip time.
# fog_a/fog_b (eth1) and cloud (eth0) each add 200 ms, so RTT is about 400 ms.
cd "$(dirname "$0")"
mkdir -p evidence
OUT=evidence/rtt.txt
{
    echo "=== Configured delay (tc netem) ==="
    echo "fog_a eth1: $(docker exec fog_a tc qdisc show dev eth1)"
    echo "fog_b eth1: $(docker exec fog_b tc qdisc show dev eth1)"
    echo "cloud eth0: $(docker exec cloud tc qdisc show dev eth0)"
    echo
    echo "=== fog_a -> cloud (10 pings) ==="
    docker exec fog_a ping -c 10 cloud
    echo
    echo "=== fog_b -> cloud (10 pings) ==="
    docker exec fog_b ping -c 10 cloud
} | tee "$OUT"
echo
echo "Saved to $OUT"
