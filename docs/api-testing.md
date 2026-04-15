# API Testing

## Health Checks

```bash
curl -s http://localhost:8001/health | jq
curl -s http://localhost:8002/health | jq
curl -s http://localhost:8003/health | jq
```

Expected:

- each response returns `status=ok`
- service name matches the endpoint target

## End-To-End Trace Generation

```bash
curl -s "http://localhost:8001/work?user_id=42" | jq
```

Expected:

- the request fans out from `zero-code-app` to `api-app` and then `sdk-app`
- a distributed trace appears in Tempo
- logs appear in Loki

## API App Direct Test

```bash
curl -s "http://localhost:8002/weather?city=chicago&user_id=42" | jq
```

Expected:

- JSON includes `city`, `temperature_f`, and nested `recommendation`
- a custom span named `api.fetch_weather` appears in the trace

## SDK App Direct Test

```bash
curl -s "http://localhost:8003/compute?items=3,5,8" | jq
```

Expected:

- JSON includes `square_sum`
- custom metrics `sdk_app_requests_total` and `sdk_app_compute_duration_ms` update in Prometheus

## Backend Checks

```bash
curl -s http://localhost:3200/ready
curl -s http://localhost:3100/ready
curl -s http://localhost:9090/api/v1/targets | jq
curl -s http://localhost:9090/api/v1/query --data-urlencode 'query=sdk_app_requests_total' | jq
```

## Failure Simulation Ideas

Stop the collector and retry a request:

```bash
docker compose stop otel-collector
curl -s "http://localhost:8001/work?user_id=99" | jq
docker compose start otel-collector
```

Expected:

- app request still returns business JSON
- telemetry is delayed or dropped during collector downtime
- exporter errors appear in service logs

