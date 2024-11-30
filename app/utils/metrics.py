# app/utils/metrics.py

import logging
from prometheus_client import start_http_server, Summary, Counter, Histogram
from typing import Dict, Any

from app.utils.logging import setup_logger

# Setup logger for metrics
logger = setup_logger("metrics", log_file="metrics.log", level=logging.INFO)

# Metric definitions
REQUEST_TIME = Summary("request_processing_seconds", "Time spent processing requests")
REQUEST_COUNT = Counter("request_count", "Total number of requests processed")
REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Request latency in seconds",
    buckets=[0.1, 0.5, 1, 5, 10],
)

# Dynamic metric registration
METRICS_REGISTRY: Dict[str, Any] = {
    "request_time": REQUEST_TIME,
    "request_count": REQUEST_COUNT,
    "request_latency": REQUEST_LATENCY,
}


def record_request_metrics(process_time: float) -> None:
    """
    Records metrics for a single request.

    Args:
        process_time (float): Time taken to process the request.
    """
    try:
        REQUEST_TIME.observe(process_time)
        REQUEST_COUNT.inc()
        REQUEST_LATENCY.observe(process_time)
        logger.debug(f"Recorded metrics: process_time={process_time}s")
    except Exception as e:
        logger.error(f"Failed to record metrics: {e}")


def start_metrics_server(port: int = 8001) -> None:
    """
    Starts a Prometheus metrics server.

    Args:
        port (int): Port on which the metrics server runs.
    """
    try:
        start_http_server(port)
        logger.info(f"Metrics server running on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
        raise
