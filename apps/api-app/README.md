# API App

This service uses the OpenTelemetry tracing API to create business spans around application work.

## Endpoints

- `GET /health`
- `GET /weather?city=chicago&user_id=42`

## Purpose

- demonstrate manual span creation with OTEL API calls
- show custom span attributes
- propagate context to `sdk-app`

## Run Locally

```bash
cd /home/vgunti/chatgpt/otel-python-projects/apps/api-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PORT=8002
export SDK_APP_URL=http://localhost:8003/compute
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_SERVICE_NAME=api-app

python app.py
```

If Docker Compose is already running this stack, use an alternate port:

```bash
export PORT=8102
export SDK_APP_URL=http://localhost:8103/compute
python app.py
```
