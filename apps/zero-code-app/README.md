# Zero Code App

This service contains no OpenTelemetry setup in application code.

Instrumentation is applied by:

```bash
opentelemetry-instrument python app.py
```

## Endpoints

- `GET /health`
- `GET /work?user_id=42`

## Purpose

- demonstrate no-code OTEL enablement
- capture inbound Flask requests
- capture outbound `requests` calls to `api-app`

## Run Locally

```bash
cd /home/vgunti/chatgpt/otel-python-projects/apps/zero-code-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PORT=8001
export DOWNSTREAM_API_URL=http://localhost:8002/weather
export OTEL_SERVICE_NAME=zero-code-app
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_LOGS_EXPORTER=otlp
export OTEL_METRICS_EXPORTER=otlp
export OTEL_TRACES_EXPORTER=otlp

opentelemetry-instrument python app.py
```

If Docker Compose is already running this stack, use an alternate port:

```bash
export PORT=8101
export DOWNSTREAM_API_URL=http://localhost:8102/weather
opentelemetry-instrument python app.py
```
