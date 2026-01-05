"""Session lifecycle MCP tools."""

from datetime import datetime, timezone
from typing import Any

from talos_telemetry.db.connection import get_connection
from talos_telemetry.telemetry.events import emit_session_end, emit_session_start


def _now_iso() -> str:
    """Return current UTC time as ISO format string for Kuzu timestamp()."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def session_open(
    session_id: str,
    goal: str,
    persona: str = "Talos",
    protocol: str = "LBRP",
    human: str = "Robbie",
) -> dict[str, Any]:
    """Initialize a telemetry session.

    Creates Session node, captures inherited knowledge state, emits session.start event.

    Args:
        session_id: Unique session identifier (format: YYYY-MM-DD-slug).
        goal: Declared session goal.
        persona: Active persona.
        protocol: Opening protocol used.
        human: Human collaborator.

    Returns:
        Dict with session details and inherited count.
    """
    try:
        conn = get_connection()

        # Create Session node
        conn.execute(f"""
            CREATE (s:Session {{
                id: '{session_id}',
                started_at: timestamp('{_now_iso()}'),
                goal: '{_escape(goal)}'
            }})
        """)

        # Capture inherited knowledge
        inherited_count = _capture_inherited(session_id)

        # Emit telemetry event
        emit_session_start(
            session_id=session_id,
            goal=goal,
            persona=persona,
            protocol=protocol,
            human=human,
            inherited_count=inherited_count,
        )

        # Create WORKED_WITH relationship
        try:
            conn.execute(f"""
                MATCH (s:Session {{id: '{session_id}'}})
                MATCH (h:Human {{name: '{human}'}})
                CREATE (s)-[:WORKED_WITH {{role: 'collaborator'}}]->(h)
            """)
        except Exception:
            pass  # Human might not exist yet

        # Create ACTIVATED relationship for persona
        try:
            conn.execute(f"""
                MATCH (s:Session {{id: '{session_id}'}})
                MATCH (p:Persona {{name: '{persona}'}})
                CREATE (s)-[:ACTIVATED {{duration_fraction: 1.0}}]->(p)
            """)
        except Exception:
            pass  # Persona might not exist yet

        # Create FOLLOWED relationship for protocol
        try:
            conn.execute(f"""
                MATCH (s:Session {{id: '{session_id}'}})
                MATCH (p:Protocol {{name: '{protocol}'}})
                CREATE (s)-[:FOLLOWED {{completed: true}}]->(p)
            """)
        except Exception:
            pass  # Protocol might not exist yet

        return {
            "success": True,
            "session_id": session_id,
            "inherited_count": inherited_count,
        }

    except Exception as e:
        return {
            "success": False,
            "degraded": True,
            "message": str(e),
            "session_id": session_id,
        }


def session_close(
    session_id: str,
    goal_achieved: bool | None = None,
    summary: str | None = None,
    skip_reflection: bool = False,
) -> dict[str, Any]:
    """Finalize a telemetry session.

    Updates Session node, aggregates metrics, emits session.end event.

    Args:
        session_id: Session identifier to close.
        goal_achieved: Whether session goal was achieved.
        summary: Brief session summary.
        skip_reflection: Skip mandatory reflection.

    Returns:
        Dict with session statistics and reflection prompt.
    """
    try:
        conn = get_connection()

        # Get session start time for duration calculation
        result = conn.execute(f"""
            MATCH (s:Session {{id: '{session_id}'}})
            RETURN s.started_at as started_at
        """)

        row = result.get_next()
        if not row:
            return {"success": False, "error": f"Session not found: {session_id}"}

        started_at = row[0]
        duration_seconds = int((datetime.now() - started_at).total_seconds()) if started_at else 0

        # Update Session node
        update_parts = [
            f"s.ended_at = timestamp('{_now_iso()}')",
            f"s.duration_seconds = {duration_seconds}",
        ]
        if summary:
            update_parts.append(f"s.summary = '{_escape(summary)}'")

        conn.execute(f"""
            MATCH (s:Session {{id: '{session_id}'}})
            SET {", ".join(update_parts)}
        """)

        # Count produced entities
        insight_count = _count_produced(session_id, "Insight")
        friction_count = _count_produced(session_id, "Friction")

        # Count tool usage
        tool_result = conn.execute(f"""
            MATCH (s:Session {{id: '{session_id}'}})-[u:USED]->(t:Tool)
            RETURN sum(u.count) as total
        """)
        tool_row = tool_result.get_next()
        tool_count = tool_row[0] if tool_row and tool_row[0] else 0

        # Emit telemetry event
        emit_session_end(
            session_id=session_id,
            duration_seconds=duration_seconds,
            goal_achieved=goal_achieved,
            insights_produced=insight_count,
            frictions_logged=friction_count,
        )

        response = {
            "success": True,
            "session_id": session_id,
            "duration_seconds": duration_seconds,
            "tool_calls": tool_count,
            "insights_produced": insight_count,
            "frictions_logged": friction_count,
        }

        if not skip_reflection:
            response["requires_reflection"] = True
            response["reflection_prompt"] = _get_reflection_prompt()

        return response

    except Exception as e:
        return {
            "success": False,
            "degraded": True,
            "message": str(e),
            "session_id": session_id,
        }


def _capture_inherited(session_id: str) -> int:
    """Capture inherited knowledge state at session start."""
    conn = get_connection()

    entity_types = ["Belief", "Insight", "Pattern", "Sutra", "Protocol", "Limitation", "Capability"]

    total = 0
    for entity_type in entity_types:
        try:
            result = conn.execute(f"MATCH (e:{entity_type}) RETURN e.id")
            while result.has_next():
                entity_id = result.get_next()[0]
                try:
                    conn.execute(f"""
                        MATCH (s:Session {{id: '{session_id}'}})
                        MATCH (e:{entity_type} {{id: '{entity_id}'}})
                        CREATE (s)-[:INHERITED]->(e)
                    """)
                    total += 1
                except Exception:
                    pass  # Relationship might already exist
        except Exception:
            pass  # Entity type might not exist yet

    return total


def _count_produced(session_id: str, entity_type: str) -> int:
    """Count entities produced by session."""
    conn = get_connection()
    try:
        result = conn.execute(f"""
            MATCH (s:Session {{id: '{session_id}'}})-[:PRODUCED]->(e:{entity_type})
            RETURN count(e) as count
        """)
        row = result.get_next()
        return row[0] if row else 0
    except Exception:
        return 0


def _get_reflection_prompt() -> str:
    """Get mandatory reflection prompt."""
    return """Session closing. Mandatory reflection:

1. What friction points occurred? (will create Friction entities)
2. What insights emerged? (will create Insight entities)
3. What patterns were noticed? (will update Pattern entities)
4. What operational states were experienced? (will create EXPERIENCED_STATE relationships)

Respond with natural language; the system will extract entities."""


def _escape(text: str) -> str:
    """Escape text for Cypher queries."""
    return text.replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
