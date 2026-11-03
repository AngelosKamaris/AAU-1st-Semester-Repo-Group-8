FROM python:3-alpine

RUN apk add --no-cache iproute2 && pip install --no-cache-dir Pillow psutil

COPY scripts/ /scripts/
