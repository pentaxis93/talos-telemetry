"""Pattern detection MCP tool."""

from typing import Any

from talos_telemetry.db.connection import get_connection

# Thresholds for pattern detection
FRICTION_RECURRENCE_THRESHOLD = 3
PATTERN_CONFIRMATION_THRESHOLD = 3
EMERGING_SIGNAL_THRESHOLD = 2


def pattern_check(
    session_id: str,
    context: str | None = None,
    include_emerging: bool = True,
) -> dict[str, Any]:
    """Check for recurring patterns based on session context.

    Args:
        session_id: Current session identifier.
        context: Optional additional context for matching.
        include_emerging: Include patterns with status='emerging'.

    Returns:
        Dict with matching patterns and emerging signals.
    """
    try:
        conn = get_connection()

        matching_patterns = []
        emerging_signals = []

        # Check for recurring friction patterns
        friction_patterns = _check_friction_patterns(conn)
        matching_patterns.extend(friction_patterns)

        # Check for confirmed patterns
        confirmed_patterns = _check_confirmed_patterns(conn)
        matching_patterns.extend(confirmed_patterns)

        # Check for emerging patterns
        if include_emerging:
            emerging = _check_emerging_patterns(conn)
            for pattern in emerging:
                if pattern["occurrence_count"] >= PATTERN_CONFIRMATION_THRESHOLD:
                    matching_patterns.append(pattern)
                else:
                    emerging_signals.append(
                        {
                            "description": pattern["description"],
                            "occurrences": pattern["occurrence_count"],
                            "threshold_for_pattern": PATTERN_CONFIRMATION_THRESHOLD,
                        }
                    )

        # Check for belief contradictions
        contradictions = _check_contradictions(conn)
        for contradiction in contradictions:
            emerging_signals.append(
                {
                    "description": f"Unresolved contradiction: {contradiction['belief1'][:50]} vs {contradiction['belief2'][:50]}",
                    "occurrences": 1,
                    "threshold_for_pattern": 1,
                }
            )

        # Check session-specific patterns
        if session_id:
            session_signals = _check_session_patterns(conn, session_id)
            emerging_signals.extend(session_signals)

        return {
            "success": True,
            "matching_patterns": matching_patterns,
            "emerging_signals": emerging_signals,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _check_friction_patterns(conn) -> list[dict]:
    """Check for recurring friction patterns."""
    patterns = []

    try:
        result = conn.execute(f"""
            MATCH (f:Friction)
            WHERE f.recurrence_count >= {FRICTION_RECURRENCE_THRESHOLD}
            RETURN f.id, f.description, f.category, f.recurrence_count, f.resolution
            ORDER BY f.recurrence_count DESC
            LIMIT 10
        """)

        while result.has_next():
            row = result.get_next()
            patterns.append(
                {
                    "id": row[0],
                    "name": f"Recurring friction: {row[2]}",
                    "description": row[1],
                    "status": "confirmed",
                    "relevance": min(1.0, row[3] / 10.0),  # Higher recurrence = higher relevance
                    "recurrence_count": row[3],
                    "indicators": [f"Occurred {row[3]} times", f"Category: {row[2]}"],
                    "resolution": row[4],
                }
            )

    except Exception:
        pass

    return patterns


def _check_confirmed_patterns(conn) -> list[dict]:
    """Check for confirmed behavioral patterns."""
    patterns = []

    try:
        result = conn.execute("""
            MATCH (p:Pattern)
            WHERE p.status = 'confirmed'
            RETURN p.id, p.name, p.description, p.occurrence_count
            ORDER BY p.occurrence_count DESC
            LIMIT 10
        """)

        while result.has_next():
            row = result.get_next()
            patterns.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "status": "confirmed",
                    "relevance": 0.8,
                    "occurrence_count": row[3],
                    "indicators": ["Confirmed pattern", f"Observed {row[3]} times"],
                }
            )

    except Exception:
        pass

    return patterns


def _check_emerging_patterns(conn) -> list[dict]:
    """Check for emerging patterns."""
    patterns = []

    try:
        result = conn.execute("""
            MATCH (p:Pattern)
            WHERE p.status = 'emerging'
            RETURN p.id, p.name, p.description, p.occurrence_count
            ORDER BY p.occurrence_count DESC
            LIMIT 10
        """)

        while result.has_next():
            row = result.get_next()
            patterns.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "status": "emerging",
                    "occurrence_count": row[3],
                }
            )

    except Exception:
        pass

    return patterns


def _check_contradictions(conn) -> list[dict]:
    """Check for unresolved belief contradictions."""
    contradictions = []

    try:
        result = conn.execute("""
            MATCH (b1:Belief)-[c:CONTRADICTS]->(b2:Belief)
            WHERE c.resolution IS NULL
            RETURN b1.content, b2.content
            LIMIT 5
        """)

        while result.has_next():
            row = result.get_next()
            contradictions.append(
                {
                    "belief1": row[0],
                    "belief2": row[1],
                }
            )

    except Exception:
        pass

    return contradictions


def _check_session_patterns(conn, session_id: str) -> list[dict]:
    """Check for patterns specific to current session."""
    signals = []

    try:
        # Check tool usage patterns
        result = conn.execute(f"""
            MATCH (s:Session {{id: '{session_id}'}})-[u:USED]->(t:Tool)
            WHERE u.count > 20
            RETURN t.name, u.count
        """)

        while result.has_next():
            row = result.get_next()
            signals.append(
                {
                    "description": f"High tool usage: {row[0]} called {row[1]} times",
                    "occurrences": 1,
                    "threshold_for_pattern": 3,
                }
            )

    except Exception:
        pass

    try:
        # Check session duration
        result = conn.execute(f"""
            MATCH (s:Session {{id: '{session_id}'}})
            WHERE s.duration_seconds > 10800  // > 3 hours
            RETURN s.duration_seconds
        """)

        if result.has_next():
            row = result.get_next()
            hours = row[0] / 3600
            signals.append(
                {
                    "description": f"Extended session: {hours:.1f} hours",
                    "occurrences": 1,
                    "threshold_for_pattern": 3,
                }
            )

    except Exception:
        pass

    return signals
