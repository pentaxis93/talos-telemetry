"""Telemetry sink - JSONL file writer."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Default telemetry path
DEFAULT_TELEMETRY_PATH = Path.home() / ".talos" / "telemetry"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Module-level sink
_sink: Optional["TelemetrySink"] = None


class TelemetrySink:
    """Telemetry event sink that writes to JSONL files."""

    def __init__(self, path: Optional[Path] = None):
        """Initialize telemetry sink.

        Args:
            path: Path to telemetry directory.
        """
        self.path = path or self._get_default_path()
        self.path.mkdir(parents=True, exist_ok=True)
        self.events_file = self.path / "events.jsonl"

    @staticmethod
    def _get_default_path() -> Path:
        """Get default telemetry path."""
        env_path = os.environ.get("TALOS_TELEMETRY_PATH")
        if env_path:
            return Path(env_path)
        return DEFAULT_TELEMETRY_PATH

    def _should_rotate(self) -> bool:
        """Check if file should be rotated."""
        if not self.events_file.exists():
            return False
        return self.events_file.stat().st_size >= MAX_FILE_SIZE

    def _rotate(self) -> None:
        """Rotate events file."""
        if not self.events_file.exists():
            return

        # Find next rotation number
        rotation = 1
        while (self.path / f"events.jsonl.{rotation}").exists():
            rotation += 1

        # Rename current file
        self.events_file.rename(self.path / f"events.jsonl.{rotation}")

    def write(self, event: dict[str, Any]) -> None:
        """Write event to sink.

        Args:
            event: Event dictionary to write.
        """
        # Check for rotation
        if self._should_rotate():
            self._rotate()

        # Add timestamp if not present
        if "timestamp" not in event:
            event["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Append to file
        with open(self.events_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def read_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Read events from sink.

        Args:
            start_time: Filter events after this time.
            end_time: Filter events before this time.
            event_type: Filter by event type.
            limit: Maximum events to return.

        Returns:
            List of matching events.
        """
        events = []

        if not self.events_file.exists():
            return events

        with open(self.events_file) as f:
            for line in f:
                if len(events) >= limit:
                    break

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Apply filters
                if event_type and event.get("event_type") != event_type:
                    continue

                if start_time or end_time:
                    event_time = datetime.fromisoformat(event.get("timestamp", "").rstrip("Z"))
                    if start_time and event_time < start_time:
                        continue
                    if end_time and event_time > end_time:
                        continue

                events.append(event)

        return events


def get_sink(path: Optional[Path] = None) -> TelemetrySink:
    """Get or create telemetry sink.

    Args:
        path: Optional path to telemetry directory.

    Returns:
        TelemetrySink instance.
    """
    global _sink

    if _sink is None:
        _sink = TelemetrySink(path)

    return _sink
