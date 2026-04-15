import logging
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


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


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s service=api-app trace_id=%(trace_id)s span_id=%(span_id)s %(name)s %(message)s",
        force=True,
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(TraceContextFilter())


def configure_telemetry(app):
    configure_logging()
    resource = Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "api-app"),
            "service.namespace": "python-otel-lab",
            "deployment.environment": "local",
        }
    )
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=f"{os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318')}/v1/traces"
    )
    provider.add_span_processor(BatchSpanProcessor(exporter, schedule_delay_millis=1000))
    trace.set_tracer_provider(provider)

    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()
    LoggingInstrumentor().instrument(set_logging_format=False)
    logging.getLogger(__name__).info("API app telemetry configured")


def get_tracer():
    return trace.get_tracer("api-app")
