"""Tests for telemetry module."""

import json
import tempfile
from pathlib import Path

import pytest

from talos_telemetry.telemetry.sink import TelemetrySink
from talos_telemetry.telemetry.events import emit_event


class TestTelemetrySink:
    """Tests for TelemetrySink."""

    def test_write_event(self):
        """Test writing an event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sink = TelemetrySink(Path(tmpdir))

            event = {"event_type": "test.event", "attributes": {"key": "value"}}

            sink.write(event)

            # Read back
            with open(sink.events_file) as f:
                line = f.readline()
                written = json.loads(line)

            assert written["event_type"] == "test.event"
            assert written["attributes"]["key"] == "value"
            assert "timestamp" in written

    def test_read_events(self):
        """Test reading events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sink = TelemetrySink(Path(tmpdir))

            # Write multiple events
            for i in range(5):
                sink.write({"event_type": f"test.event.{i}", "attributes": {"index": i}})

            # Read all
            events = sink.read_events()
            assert len(events) == 5

    def test_read_events_filtered(self):
        """Test reading events with filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sink = TelemetrySink(Path(tmpdir))

            # Write different event types
            sink.write({"event_type": "session.start", "attributes": {}})
            sink.write({"event_type": "session.end", "attributes": {}})
            sink.write({"event_type": "session.start", "attributes": {}})

            # Filter by type
            events = sink.read_events(event_type="session.start")
            assert len(events) == 2


class TestEmitEvent:
    """Tests for emit_event function."""

    def test_emit_event(self):
        """Test emitting an event."""
        # Note: This will write to actual telemetry path
        # In production, would mock the sink
        event = emit_event("test.event", {"key": "value"}, trace_id="test-trace")

        assert event["event_type"] == "test.event"
        assert event["attributes"]["key"] == "value"
        assert event["trace_id"] == "test-trace"
        assert "timestamp" in event
