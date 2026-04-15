# Test Results

## Executed In This Environment

- Python syntax compilation for all application modules
- Static configuration review for Docker Compose, OTEL Collector, Grafana, Prometheus, Tempo, and Loki files

## Blocked In This Environment

- `docker compose up --build -d`
- live Grafana, Tempo, Loki, and Prometheus validation
- curl tests against running containers

Reason:

- Docker is not installed on this host

## Expected Runtime Validation

After Docker is installed, run:

```bash
docker compose up --build -d
curl -s http://localhost:8001/work?user_id=42 | jq
curl -s http://localhost:8002/weather?city=chicago | jq
curl -s http://localhost:8003/compute?items=3,5,8 | jq
```

Then verify:

- Grafana data sources show green status
- Tempo contains end-to-end traces from zero-code -> api -> sdk
- Prometheus contains `sdk_app_requests_total` and `sdk_app_compute_duration_ms`
- Loki contains logs from all three services
- responses include `telemetry.trace_id` and `telemetry.span_id`

## Runtime Debug Notes

- `trace_id=0` in startup logs is not sufficient evidence that request tracing is broken
- validate tracing using request endpoints and response payloads
- if runtime behavior differs from source code, rebuild without cache and inspect `/app/app.py` inside the container
