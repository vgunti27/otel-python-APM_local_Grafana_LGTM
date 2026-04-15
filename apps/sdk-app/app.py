import logging
import os
import time

from flask import Flask, jsonify, request
from opentelemetry import trace

from telemetry import configure_telemetry


app = Flask(__name__)
telemetry = configure_telemetry(app)
tracer = telemetry["tracer"]
meter = telemetry["meter"]
logger = logging.getLogger("sdk-app")

request_counter = meter.create_counter(
    "sdk_app_requests_total",
    unit="1",
    description="Total requests handled by sdk-app",
)
work_histogram = meter.create_histogram(
    "sdk_app_compute_duration_ms",
    unit="ms",
    description="Compute duration for sdk-app operations",
)


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
    logger.info("sdk root hit")
    return jsonify(
        service="sdk-app",
        message="Use /health or /compute?items=3,5,8 to generate traces",
        telemetry=trace_context_payload(),
    )


@app.get("/health")
def health():
    return jsonify(status="ok", service="sdk-app", telemetry=trace_context_payload())


@app.get("/compute")
def compute():
    raw_items = request.args.get("items", "1,2,3")
    values = [int(value.strip()) for value in raw_items.split(",") if value.strip()]

    with tracer.start_as_current_span("sdk.compute") as span:
        span.set_attribute("app.item_count", len(values))
        started = time.perf_counter()
        result = sum(v * v for v in values)
        duration_ms = round((time.perf_counter() - started) * 1000, 3)

        request_counter.add(1, {"endpoint": "/compute"})
        work_histogram.record(duration_ms, {"endpoint": "/compute"})
        telemetry = trace_context_payload()
        logger.info(
            "computed values=%s result=%s duration_ms=%s trace_id=%s span_id=%s",
            values,
            result,
            duration_ms,
            telemetry["trace_id"],
            telemetry["span_id"],
        )
        return jsonify(
            service="sdk-app",
            items=values,
            square_sum=result,
            duration_ms=duration_ms,
            telemetry=telemetry,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8003")))
