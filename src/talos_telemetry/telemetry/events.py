"""Telemetry event emission."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from talos_telemetry.telemetry.sink import get_sink


def emit_event(
    event_type: str,
    attributes: dict[str, Any],
    trace_id: str | None = None,
    span_id: str | None = None,
) -> dict[str, Any]:
    """Emit a telemetry event.

    Args:
        event_type: Type of event (e.g., "session.start", "session.tool_call").
        attributes: Event attributes.
        trace_id: Optional trace ID for correlation.
        span_id: Optional span ID.

    Returns:
        The emitted event.
    """
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "trace_id": trace_id or str(uuid4()),
        "attributes": attributes,
    }

    if span_id:
        event["span_id"] = span_id

    sink = get_sink()
    sink.write(event)

    return event


# Convenience functions for common events


def emit_session_start(
    session_id: str,
    goal: str | None = None,
    persona: str | None = None,
    protocol: str | None = None,
    human: str | None = None,
    inherited_count: int | None = None,
) -> dict[str, Any]:
    """Emit session.start event."""
    attributes = {
        "talos.session.id": session_id,
    }
    if goal:
        attributes["talos.session.goal"] = goal
    if persona:
        attributes["talos.session.persona"] = persona
    if protocol:
        attributes["talos.session.protocol"] = protocol
    if human:
        attributes["talos.session.human"] = human
    if inherited_count is not None:
        attributes["talos.session.inherited_count"] = inherited_count

    return emit_event("session.start", attributes, trace_id=f"sess-{session_id}")


def emit_session_end(
    session_id: str,
    duration_seconds: int,
    token_count: int | None = None,
    goal_achieved: bool | None = None,
    insights_produced: int | None = None,
    frictions_logged: int | None = None,
) -> dict[str, Any]:
    """Emit session.end event."""
    attributes = {
        "talos.session.id": session_id,
        "talos.session.duration_seconds": duration_seconds,
    }
    if token_count is not None:
        attributes["talos.session.token_count"] = token_count
    if goal_achieved is not None:
        attributes["talos.session.goal_achieved"] = goal_achieved
    if insights_produced is not None:
        attributes["talos.session.insights_produced"] = insights_produced
    if frictions_logged is not None:
        attributes["talos.session.frictions_logged"] = frictions_logged

    return emit_event("session.end", attributes, trace_id=f"sess-{session_id}")


def emit_tool_call(
    session_id: str,
    tool_name: str,
    success: bool,
    duration_ms: int | None = None,
    error_type: str | None = None,
) -> dict[str, Any]:
    """Emit session.tool_call event."""
    attributes = {
        "talos.session.id": session_id,
        "talos.tool.name": tool_name,
        "talos.tool.success": success,
    }
    if duration_ms is not None:
        attributes["talos.tool.duration_ms"] = duration_ms
    if error_type:
        attributes["talos.tool.error_type"] = error_type

    return emit_event(
        "session.tool_call",
        attributes,
        trace_id=f"sess-{session_id}",
        span_id=f"tool-{tool_name}-{uuid4().hex[:8]}",
    )


def emit_knowledge_event(
    event_subtype: str, session_id: str, entity_id: str, **kwargs
) -> dict[str, Any]:
    """Emit knowledge.* event."""
    attributes = {
        "talos.session.id": session_id,
        f"talos.{event_subtype}.id": entity_id,
    }

    for key, value in kwargs.items():
        if value is not None:
            attributes[f"talos.{event_subtype}.{key}"] = value

    return emit_event(f"knowledge.{event_subtype}", attributes, trace_id=f"sess-{session_id}")
