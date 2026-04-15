import logging
import os
import random
import time

import requests
from flask import Flask, jsonify, request
from opentelemetry import trace

from telemetry import configure_telemetry, get_tracer


app = Flask(__name__)
configure_telemetry(app)
tracer = get_tracer()
logger = logging.getLogger("api-app")
sdk_app_url = os.getenv("SDK_APP_URL", "http://localhost:8003/compute")


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
    logger.info("api root hit")
    return jsonify(
        service="api-app",
        message="Use /health or /weather?city=chicago&user_id=42 to generate traces",
        telemetry=trace_context_payload(),
    )


@app.get("/health")
def health():
    return jsonify(status="ok", service="api-app", telemetry=trace_context_payload())


@app.get("/weather")
def weather():
    city = request.args.get("city", "chicago")
    user_id = request.args.get("user_id", "anonymous")

    with tracer.start_as_current_span("api.fetch_weather") as span:
        temperature_f = random.randint(55, 85)
        span.set_attribute("app.city", city)
        span.set_attribute("app.user_id", user_id)

        with tracer.start_as_current_span("api.lookup_recommendation"):
            compute_response = requests.get(
                sdk_app_url,
                params={"items": "2,4,6"},
                timeout=5,
            )
            compute_payload = compute_response.json()

        time.sleep(0.05)
        telemetry = trace_context_payload()
        logger.info(
            "served weather lookup city=%s user_id=%s trace_id=%s span_id=%s",
            city,
            user_id,
            telemetry["trace_id"],
            telemetry["span_id"],
        )
        return jsonify(
            service="api-app",
            city=city,
            temperature_f=temperature_f,
            recommendation=compute_payload,
            telemetry=telemetry,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8002")))
