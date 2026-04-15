import logging
import os
import time

from flask import Flask, jsonify, request

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


@app.get("/health")
def health():
    return jsonify(status="ok", service="sdk-app")


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
        logger.info("computed values=%s result=%s duration_ms=%s", values, result, duration_ms)
        return jsonify(service="sdk-app", items=values, square_sum=result, duration_ms=duration_ms)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8003")))

