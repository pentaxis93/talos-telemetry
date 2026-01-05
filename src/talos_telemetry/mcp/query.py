"""Graph query MCP tool."""

import re
from typing import Any, Optional

from talos_telemetry.db.connection import get_connection


# Query timeout in seconds
QUERY_TIMEOUT = 30

# Maximum rows to return
MAX_ROWS = 1000

# Disallowed keywords for safety
DISALLOWED_KEYWORDS = ["CREATE", "DELETE", "SET", "REMOVE", "MERGE", "DROP", "ALTER"]


def graph_query(
    cypher: str,
    parameters: Optional[dict] = None,
    explain: bool = False,
) -> dict[str, Any]:
    """Execute a Cypher query against the knowledge graph.

    Args:
        cypher: Cypher query string (read-only).
        parameters: Optional query parameters.
        explain: Return query plan instead of results.

    Returns:
        Dict with query results.
    """
    # Validate query is read-only
    validation_error = _validate_query(cypher)
    if validation_error:
        return {
            "success": False,
            "error": validation_error,
        }

    try:
        conn = get_connection()

        if explain:
            # Return query plan
            plan_result = conn.execute(f"EXPLAIN {cypher}")
            return {
                "success": True,
                "explain": True,
                "plan": str(plan_result),
            }

        # Execute query
        if parameters:
            result = conn.execute(cypher, parameters)
        else:
            result = conn.execute(cypher)

        # Collect results
        columns = result.get_column_names()
        rows = []

        while result.has_next() and len(rows) < MAX_ROWS:
            row = result.get_next()
            rows.append(list(row))

        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": len(rows) == MAX_ROWS,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _validate_query(cypher: str) -> Optional[str]:
    """Validate that query is read-only.

    Returns error message if invalid, None if valid.
    """
    upper_query = cypher.upper()

    for keyword in DISALLOWED_KEYWORDS:
        # Match keyword as whole word
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, upper_query):
            return f"Query contains disallowed keyword: {keyword}. Only read queries are allowed."

    return None


# Convenience functions for common queries


def count_entities(entity_type: str) -> int:
    """Count entities of a given type."""
    result = graph_query(f"MATCH (e:{entity_type}) RETURN count(e) as count")
    if result["success"] and result["rows"]:
        return result["rows"][0][0]
    return 0


def find_patterns(min_occurrences: int = 3) -> list[dict]:
    """Find confirmed patterns by occurrence count."""
    result = graph_query(f"""
        MATCH (p:Pattern)
        WHERE p.occurrence_count >= {min_occurrences}
        RETURN p.id, p.name, p.description, p.occurrence_count, p.status
        ORDER BY p.occurrence_count DESC
    """)

    if not result["success"]:
        return []

    patterns = []
    for row in result["rows"]:
        patterns.append(
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "occurrence_count": row[3],
                "status": row[4],
            }
        )

    return patterns


def find_recurring_friction(min_recurrence: int = 2) -> list[dict]:
    """Find recurring friction points."""
    result = graph_query(f"""
        MATCH (f:Friction)
        WHERE f.recurrence_count >= {min_recurrence}
        RETURN f.id, f.description, f.category, f.recurrence_count
        ORDER BY f.recurrence_count DESC
    """)

    if not result["success"]:
        return []

    frictions = []
    for row in result["rows"]:
        frictions.append(
            {
                "id": row[0],
                "description": row[1],
                "category": row[2],
                "recurrence_count": row[3],
            }
        )

    return frictions


def get_session_summary(session_id: str) -> dict:
    """Get summary of a session."""
    result = graph_query(f"""
        MATCH (s:Session {{id: '{session_id}'}})
        OPTIONAL MATCH (s)-[:PRODUCED]->(i:Insight)
        OPTIONAL MATCH (s)-[:PRODUCED]->(f:Friction)
        OPTIONAL MATCH (s)-[:EXPERIENCED_STATE]->(st:OperationalState)
        RETURN s.goal, s.summary, s.duration_seconds,
               count(DISTINCT i) as insights,
               count(DISTINCT f) as frictions,
               collect(DISTINCT st.name) as states
    """)

    if not result["success"] or not result["rows"]:
        return {}

    row = result["rows"][0]
    return {
        "goal": row[0],
        "summary": row[1],
        "duration_seconds": row[2],
        "insights": row[3],
        "frictions": row[4],
        "states": row[5],
    }
