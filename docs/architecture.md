# Architecture

## Overview

The stack uses a single OTEL Collector as the aggregation point for traces, metrics, and logs from three Python services.

```mermaid
flowchart LR
    Z[zero-code-app\nFlask + auto instrumentation] --> C[OTEL Collector]
    A[api-app\nFlask + OTEL API spans] --> C
    S[sdk-app\nFlask + explicit OTEL SDK] --> C
    Z --> A
    A --> S
    C --> T[Tempo]
    C --> P[Prometheus scrape endpoint]
    C --> L[Loki]
    G[Grafana] --> T
    G --> P
    G --> L
```

## Request Path

```mermaid
sequenceDiagram
    participant Client
    participant Z as zero-code-app
    participant A as api-app
    participant S as sdk-app
    participant C as OTEL Collector
    participant T as Tempo
    participant P as Prometheus
    participant L as Loki

    Client->>Z: GET /work?user_id=42
    Z->>A: GET /weather?city=chicago&user_id=42
    A->>S: GET /compute?items=2,4,6
    S-->>A: JSON result
    A-->>Z: JSON result
    Z-->>Client: JSON result
    Z->>C: traces, metrics, logs
    A->>C: traces, metrics, logs
    S->>C: traces, metrics, logs
    C->>T: traces
    C->>P: Prometheus scrape target
    C->>L: logs
```

## Design Notes

- The zero-code service proves that useful telemetry can be collected without modifying application code.
- The API service adds business spans to improve trace readability.
- The SDK service demonstrates precise control over metrics, logs, and trace export.
- Grafana data sources are provisioned at startup, so no manual setup is required.

