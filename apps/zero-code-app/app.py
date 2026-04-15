import logging
import os
import random
import time

import requests
from flask import Flask, jsonify, request
from opentelemetry import trace


class TraceContextFilter(logging.Filter):
    def filter(self, record):
        span_context = trace.get_current_span().get_span_context()
        if span_context.is_valid:
            record.trace_id = f"{span_context.trace_id:032x}"
            record.span_id = f"{span_context.span_id:016x}"
        else:
            record.trace_id = "-"
            record.span_id = "-"
        return True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s service=zero-code-app trace_id=%(trace_id)s span_id=%(span_id)s %(name)s %(message)s",
    force=True,
)
for handler in logging.getLogger().handlers:
    handler.addFilter(TraceContextFilter())

logger = logging.getLogger("zero-code-app")

app = Flask(__name__)
downstream_api_url = os.getenv("DOWNSTREAM_API_URL", "http://localhost:8002/weather")


def trace_context_payload():
    span_context = trace.get_current_span().get_span_context()
    if not span_context.is_valid:
        return {"trace_id": None, "span_id": None}
    return {
        "trace_id": f"{span_context.trace_id:032x}",
        "span_id": f"{span_context.span_id:016x}",
    }


@app.get("/")
def index():
    logger.info("zero-code root hit")
    return jsonify(
        service="zero-code-app",
        message="Use /health or /work?user_id=42 to generate traces",
        telemetry=trace_context_payload(),
    )


@app.get("/health")
def health():
    logger.info("zero-code health check")
    return jsonify(status="ok", service="zero-code-app", telemetry=trace_context_payload())


@app.get("/work")
def work():
    user_id = request.args.get("user_id", "anonymous")
    delay_ms = random.randint(20, 120)
    time.sleep(delay_ms / 1000)

    downstream = requests.get(
        downstream_api_url,
        params={"city": "chicago", "user_id": user_id},
        timeout=5,
    )
    payload = downstream.json()
    telemetry = trace_context_payload()
    logger.info(
        "processed request user_id=%s delay_ms=%s trace_id=%s span_id=%s",
        user_id,
        delay_ms,
        telemetry["trace_id"],
        telemetry["span_id"],
    )
    return jsonify(
        service="zero-code-app",
        delay_ms=delay_ms,
        downstream=payload,
        telemetry=telemetry,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
