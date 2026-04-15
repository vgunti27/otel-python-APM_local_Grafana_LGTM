# Failure Cases

## Collector Unavailable

Symptoms:

- App requests still succeed
- telemetry export warnings appear in logs
- no new traces, metrics, or logs in Grafana

What to check:

- `docker compose ps`
- collector logs with `docker compose logs otel-collector`
- `OTEL_EXPORTER_OTLP_ENDPOINT` values in service containers

Mitigation:

- restore the collector
- keep BatchSpanProcessor defaults or increase queue sizes if outage is brief

## Stale Container Images

Symptoms:

- container behavior does not match the latest source code
- newly added endpoints still return `404`
- updated logging changes do not appear after restart

What to check:

- `docker compose exec zero-code-app sh -lc "grep -n 'trace_context_payload' /app/app.py"`
- `docker compose exec api-app sh -lc "grep -n 'trace_context_payload' /app/app.py"`
- `docker compose exec sdk-app sh -lc "grep -n 'trace_context_payload' /app/app.py"`

Mitigation:

- `docker compose down --remove-orphans`
- `docker compose build --no-cache zero-code-app api-app sdk-app`
- `docker compose up -d --force-recreate zero-code-app api-app sdk-app otel-collector tempo loki promtail grafana prometheus`

## Tempo Unavailable

Symptoms:

- traces missing from Grafana Explore
- collector logs show trace exporter failures

What to check:

- `docker compose logs tempo`
- `curl -s http://localhost:3200/ready`

Mitigation:

- restart Tempo
- verify the collector trace exporter points to `tempo:4318`

## Loki Unavailable

Symptoms:

- logs absent in Grafana Explore
- collector log pipeline export errors

What to check:

- `docker compose logs loki`
- `curl -s http://localhost:3100/ready`

Mitigation:

- restart Loki
- verify the collector logs exporter endpoint is `http://loki:3100/otlp`

## Promtail Not Shipping Docker Logs

Symptoms:

- application OTLP logs may appear, but container stdout/stderr logs are missing from Loki
- Grafana Explore shows incomplete log coverage for the running containers

What to check:

- `docker compose logs promtail`
- `docker compose ps promtail`
- ensure `/var/lib/docker/containers` is mounted into Promtail

Mitigation:

- restart `promtail`
- verify [observability/promtail/config.yml](/home/vgunti/chatgpt/otel-python-projects/observability/promtail/config.yml)
- verify Docker JSON log files exist on the host

## Prometheus Missing Metrics

Symptoms:

- no custom metrics in Grafana or Prometheus
- Tempo and Loki may still work

What to check:

- `curl -s http://localhost:9464/metrics | head`
- `http://localhost:9090/targets`

Mitigation:

- confirm Prometheus is scraping `otel-collector:9464`
- ensure apps send metrics through OTLP to the collector

## Auto-Instrumentation Not Taking Effect In Zero Code App

Symptoms:

- zero-code app works but trace count is lower than expected
- outbound requests are not linked in traces

What to check:

- container entrypoint uses `opentelemetry-instrument`
- Flask and requests instrumentation packages are installed
- `OTEL_PYTHON_LOG_CORRELATION=true` and OTLP exporters are configured

Mitigation:

- rebuild the zero-code image
- run `docker compose up --build zero-code-app`

## Trace IDs Missing In Startup Logs

Symptoms:

- startup logs show `trace_id=0` and `span_id=0`
- operators assume tracing is broken

What to check:

- whether you are reading startup/access logs instead of request-handler logs
- whether `/work`, `/weather`, and `/compute` responses include `telemetry.trace_id`

Mitigation:

- do not use startup logs alone as trace proof
- generate traced requests
- validate trace propagation from response payloads and Tempo

## Bad OTLP Endpoint

Symptoms:

- repeated exporter connection errors in application logs
- no telemetry in Grafana

What to check:

- endpoints should use the collector hostname inside Compose, not `localhost`
- HTTP OTLP endpoints should resolve to `/v1/traces`, `/v1/metrics`, `/v1/logs`

Mitigation:

- use `http://otel-collector:4318`
- rebuild and restart affected services

## Docker Not Installed On Host

Symptoms:

- `docker: command not found`

Mitigation:

- install Docker Engine and Docker Compose plugin on the host
- then run `docker compose up --build -d`
