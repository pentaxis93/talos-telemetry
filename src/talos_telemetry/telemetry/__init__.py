"""Telemetry module - OpenTelemetry event capture."""

from talos_telemetry.telemetry.events import emit_event
from talos_telemetry.telemetry.sink import TelemetrySink, get_sink

__all__ = ["emit_event", "TelemetrySink", "get_sink"]
