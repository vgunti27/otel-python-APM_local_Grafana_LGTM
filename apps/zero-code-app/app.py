import logging
import os
import random
import time

import requests
from flask import Flask, jsonify, request


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("zero-code-app")

app = Flask(__name__)
downstream_api_url = os.getenv("DOWNSTREAM_API_URL", "http://localhost:8002/weather")


@app.get("/health")
def health():
    logger.info("zero-code health check")
    return jsonify(status="ok", service="zero-code-app")


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
    logger.info("processed request", extra={"user_id": user_id, "delay_ms": delay_ms})
    return jsonify(service="zero-code-app", delay_ms=delay_ms, downstream=payload)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8001")))

