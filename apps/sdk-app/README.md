# SDK App

This service uses explicit OpenTelemetry SDK setup for traces, metrics, and logs.

## Endpoints

- `GET /health`
- `GET /compute?items=3,5,8`

## Purpose

- demonstrate explicit provider and exporter setup
- emit custom metrics
- export application logs through OTLP

## Run Locally

```bash
cd /home/vgunti/chatgpt/otel-python-projects/apps/sdk-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PORT=8003
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_SERVICE_NAME=sdk-app

python app.py
```

If Docker Compose is already running this stack, use an alternate port:

```bash
export PORT=8103
python app.py
```
