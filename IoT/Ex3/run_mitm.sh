#!/usr/bin/env bash
# Task 5.5: man-in-the-middle attack between the fog nodes and the cloud.
#
# An attacker container takes over the cloud's IP (1.1.1.4) and name ("cloud") on
# backbone_net and presents a certificate for "cloud" signed by its own CA (Evil-CA).
# The fog nodes trust only our IoT-CA, so they must reject the TLS connection.
# The script restores the real cloud at the end.
set -u
cd "$(dirname "$0")"

MITM_DIR="./mitm_attack"
mkdir -p "$MITM_DIR"

echo "===== [1/5] Baseline: fog nodes talking to the REAL cloud over mTLS ====="
docker logs --tail 10 fog_a
docker logs --tail 5 cloud
echo

echo "===== [2/5] Create the attacker certificate (Evil-CA signs a cert for 'cloud') ====="
if [ ! -f "$MITM_DIR/mitm-chain.crt" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -keyout "$MITM_DIR/evil-ca.key" \
        -out "$MITM_DIR/evil-ca.crt" -days 30 -subj "/CN=Evil-CA"
    openssl req -newkey rsa:2048 -nodes -keyout "$MITM_DIR/mitm.key" \
        -out "$MITM_DIR/mitm.csr" -subj "/CN=cloud"
    printf "subjectAltName=DNS:cloud\nextendedKeyUsage=serverAuth\n" > "$MITM_DIR/mitm.ext"
    openssl x509 -req -in "$MITM_DIR/mitm.csr" -CA "$MITM_DIR/evil-ca.crt" \
        -CAkey "$MITM_DIR/evil-ca.key" -CAcreateserial -out "$MITM_DIR/mitm.crt" \
        -days 30 -extfile "$MITM_DIR/mitm.ext"
    cat "$MITM_DIR/mitm.crt" "$MITM_DIR/evil-ca.crt" > "$MITM_DIR/mitm-chain.crt"
fi
openssl x509 -in "$MITM_DIR/mitm.crt" -noout -subject -issuer
echo

echo "===== [3/5] Replace the real cloud with the attacker (1.1.1.4, alias 'cloud') ====="
docker compose stop cloud
docker rm -f mitm 2>/dev/null || true
ABS_MITM="$(cd "$MITM_DIR" && pwd)"
docker run -d --name mitm --network backbone_net --ip 1.1.1.4 --network-alias cloud \
    -v "$ABS_MITM":/mitm:ro alpine:3.20 \
    sh -c "apk add --no-cache openssl >/dev/null && openssl s_server -accept 8000 -cert /mitm/mitm-chain.crt -key /mitm/mitm.key -www"

echo -n "    waiting for the fake server to start"
for _ in $(seq 1 40); do
    if docker exec mitm sh -c "netstat -ltn 2>/dev/null | grep -q ':8000'"; then break; fi
    echo -n "."; sleep 1
done
echo
docker exec fog_a python -c "import socket; print('cloud ->', socket.gethostbyname('cloud'))"
echo

echo "===== [4/5] Force fresh requests so the fog nodes contact the attacker ====="
docker compose restart fog_a fog_b camera-1 camera-2 camera-3
sleep 25
echo "----- fog_a (expect CERTIFICATE_VERIFY_FAILED) -----"
docker logs --tail 25 fog_a
echo "----- fog_b (same CA, same rejection) -----"
docker logs --tail 25 fog_b
echo "----- attacker / mitm (expect: tlsv1 alert unknown ca) -----"
docker logs mitm
echo

echo "===== [5/5] Restore the real cloud ====="
docker rm -f mitm
docker compose start cloud
docker compose restart fog_a fog_b camera-1 camera-2 camera-3
docker compose ps
echo
echo "System restored. Attacker files are in $MITM_DIR (safe to delete)."
