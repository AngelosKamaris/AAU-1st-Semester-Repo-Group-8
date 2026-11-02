FROM python:3-alpine AS build
WORKDIR /src
COPY run.py .
RUN chmod +x run.py

FROM python:3-alpine
RUN apk add --no-cache iproute2 iputils
COPY --from=build /src/run.py /run.py
CMD ["python", "/run.py"]
