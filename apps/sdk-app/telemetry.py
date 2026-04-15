import logging
import os

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
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


def configure_logging(logger_provider):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s service=sdk-app trace_id=%(trace_id)s span_id=%(span_id)s %(name)s %(message)s",
        force=True,
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(TraceContextFilter())

    logging_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging_handler.addFilter(TraceContextFilter())
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(logging_handler)


def build_resource():
    return Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "sdk-app"),
            "service.namespace": "python-otel-lab",
            "deployment.environment": "local",
        }
    )


def configure_telemetry(app):
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    resource = build_resource()

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces"),
            schedule_delay_millis=1000,
        )
    )
    trace.set_tracer_provider(tracer_provider)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics")
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{endpoint}/v1/logs"))
    )
    set_logger_provider(logger_provider)
    configure_logging(logger_provider)

    FlaskInstrumentor().instrument_app(app)
    LoggingInstrumentor().instrument(set_logging_format=False)

    return {
        "tracer": trace.get_tracer("sdk-app"),
        "meter": metrics.get_meter("sdk-app"),
    }
