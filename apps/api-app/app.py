import logging
import os
import random
import time

import requests
from flask import Flask, jsonify, request

from telemetry import configure_telemetry, get_tracer


app = Flask(__name__)
configure_telemetry(app)
tracer = get_tracer()
logger = logging.getLogger("api-app")
sdk_app_url = os.getenv("SDK_APP_URL", "http://localhost:8003/compute")


@app.get("/health")
def health():
    return jsonify(status="ok", service="api-app")


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
        logger.info("served weather lookup for city=%s user_id=%s", city, user_id)
        return jsonify(
            service="api-app",
            city=city,
            temperature_f=temperature_f,
            recommendation=compute_payload,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8002")))

