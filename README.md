# Python OTEL Instrumentation Lab

This workspace provides three Python services that demonstrate OpenTelemetry instrumentation using:

1. Zero code changes
2. OTEL API-based manual spans
3. OTEL SDK-based full manual configuration

It also includes a local observability stack with Docker Compose:

- OpenTelemetry Collector
- Grafana
- Tempo
- Prometheus
- Loki
- Promtail

## Layout

- `apps/zero-code-app`: Plain Flask app with no OpenTelemetry code
- `apps/api-app`: Flask app with OTEL API manual spans and log correlation hooks
- `apps/sdk-app`: Flask app with explicit OTEL SDK configuration for traces, metrics, and logs
- `observability/`: Collector, Grafana, Prometheus, Tempo, Loki, and Promtail configuration
- `docs/`: Architecture and failure-case documentation
- `scripts/`: Validation helpers

## Quick Start

Prerequisites:

- Docker Engine with Compose plugin
- Python 3.11+ if you want to run the apps without containers

Start the stack:

```bash
docker compose up --build -d
```

If the running containers do not reflect the latest local source changes, rebuild without cache and force recreation:

```bash
docker compose down --remove-orphans
docker compose build --no-cache zero-code-app api-app sdk-app
docker compose up -d --force-recreate zero-code-app api-app sdk-app otel-collector tempo loki promtail grafana prometheus
```

## Run The Python Apps Without Docker

You can also run each app directly with Python.

Create a virtual environment inside each app directory, install dependencies, then start the app.

If `docker compose up` is already running, ports `8001`, `8002`, and `8003` are already occupied by the containers.

In that case, either:

1. stop the containers before running the apps directly, or
2. run the Python apps on alternate ports such as `8101`, `8102`, and `8103`

Stop the containers:

```bash
cd /home/vgunti/chatgpt/otel-python-projects
docker compose down
```

### Zero Code App

```bash
cd /home/vgunti/chatgpt/otel-python-projects/apps/zero-code-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PORT=8101
export DOWNSTREAM_API_URL=http://localhost:8102/weather
export OTEL_SERVICE_NAME=zero-code-app
export OTEL_RESOURCE_ATTRIBUTES=deployment.environment=local,service.namespace=python-otel-lab
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_PYTHON_LOG_CORRELATION=true
export OTEL_LOGS_EXPORTER=otlp
export OTEL_METRICS_EXPORTER=otlp
export OTEL_TRACES_EXPORTER=otlp

opentelemetry-instrument python app.py
```

### API App

```bash
cd /home/vgunti/chatgpt/otel-python-projects/apps/api-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PORT=8102
export SDK_APP_URL=http://localhost:8103/compute
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_SERVICE_NAME=api-app

python app.py
```

### SDK App

```bash
cd /home/vgunti/chatgpt/otel-python-projects/apps/sdk-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PORT=8103
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_SERVICE_NAME=sdk-app

python app.py
```

Run order for local development:

1. Start the OTEL Collector and backends with Docker if available.
2. Start `sdk-app`.
3. Start `api-app`.
4. Start `zero-code-app`.

If you do not start the collector, the apps can still serve requests, but telemetry export will fail and observability data will not appear in Grafana.

Services:

- Zero code app: `http://localhost:8001`
- API app: `http://localhost:8002`
- SDK app: `http://localhost:8003`
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`
- Tempo: `http://localhost:3200`
- Loki: `http://localhost:3100`
- Promtail: internal-only log shipper for Docker container stdout/stderr

Grafana credentials:

- Username: `admin`
- Password: `admin`

## What Each App Demonstrates

### Zero Code Changes

The app itself contains no OTEL imports or configuration. Instrumentation is injected by the `opentelemetry-instrument` launcher in the container entrypoint.

### API App

The app adds custom spans using the OpenTelemetry tracing API while keeping setup minimal and conventional.

### SDK App

The app explicitly configures:

- tracer provider
- meter provider
- logger provider
- OTLP exporters
- metric readers
- resource attributes

## Testing With Curl

Generate traffic:

```bash
curl -s http://localhost:8001/health
curl -s "http://localhost:8001/work?user_id=42"
curl -s http://localhost:8002/
curl -s "http://localhost:8002/weather?city=chicago"
curl -s http://localhost:8003/
curl -s "http://localhost:8003/compute?items=3,5,8"
```

Inspect raw telemetry backends:

```bash
curl -s http://localhost:9090/api/v1/label/__name__/values | jq
curl -s http://localhost:3100/loki/api/v1/labels | jq
curl -s http://localhost:3200/ready
```

## Verification Flow

1. Start the stack with `docker compose up --build -d`
2. Run the curl commands above a few times
3. Open Grafana and verify data sources are healthy
4. In Grafana Explore:
   - inspect traces in Tempo
   - inspect logs in Loki
   - inspect metrics in Prometheus

## Trace Verification

Do not use Flask startup logs or `werkzeug` access logs as the primary signal for tracing. Those lines may legitimately show `trace_id=0` outside an active request span.

Instead, verify tracing with real request endpoints and response payloads:

```bash
curl -s "http://localhost:8001/work?user_id=42" | jq
curl -s "http://localhost:8002/weather?city=chicago&user_id=42" | jq
curl -s "http://localhost:8003/compute?items=3,5,8" | jq
```

Each response should include:

- `telemetry.trace_id`
- `telemetry.span_id`

The `trace_id` should be a 32-character hex string. The same trace should propagate end to end across the nested service calls.

Useful runtime checks:

```bash
docker compose logs --tail=100 zero-code-app
docker compose logs --tail=100 api-app
docker compose logs --tail=100 sdk-app
docker compose logs --tail=200 otel-collector
docker compose logs --tail=200 tempo
docker compose logs --tail=200 promtail
```

If you suspect stale containers, verify that the updated source is present inside the container:

```bash
docker compose exec zero-code-app sh -lc "grep -n 'trace_context_payload' /app/app.py"
docker compose exec api-app sh -lc "grep -n 'trace_context_payload' /app/app.py"
docker compose exec sdk-app sh -lc "grep -n 'trace_context_payload' /app/app.py"
```

## Data Sources Provisioned Automatically

- `Prometheus`
- `Loki`
- `Tempo`

## Docs

- Architecture: [docs/architecture.md](/home/vgunti/chatgpt/otel-python-projects/docs/architecture.md)
- API testing: [docs/api-testing.md](/home/vgunti/chatgpt/otel-python-projects/docs/api-testing.md)
- Failure cases: [docs/failure-cases.md](/home/vgunti/chatgpt/otel-python-projects/docs/failure-cases.md)
- Local test notes: [docs/test-results.md](/home/vgunti/chatgpt/otel-python-projects/docs/test-results.md)


## Notes About This Environment

This workspace was generated in a host environment where Docker was not installed and the originally requested `python_projects` directory was OS-blocked. The full container stack is included and ready to run on a Docker-enabled host, but container startup could not be executed here.
