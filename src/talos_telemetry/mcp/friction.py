"""Friction logging MCP tool."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from talos_telemetry.db.connection import get_connection
from talos_telemetry.embeddings.model import get_embedding
from talos_telemetry.telemetry.events import emit_knowledge_event


def friction_log(
    description: str,
    category: str,
    session_id: str | None = None,
    blocking: bool = False,
) -> dict[str, Any]:
    """Log a friction point.

    Creates Friction entity or increments recurrence count if similar exists.

    Args:
        description: Brief description of the friction.
        category: Friction category (tooling, conceptual, process, environmental, relational).
        session_id: Associated session.
        blocking: Whether friction is blocking progress.

    Returns:
        Dict with friction ID and recurrence info.
    """
    valid_categories = ["tooling", "conceptual", "process", "environmental", "relational"]
    if category not in valid_categories:
        return {
            "success": False,
            "error": f"Invalid category: {category}. Valid: {valid_categories}",
        }

    try:
        conn = get_connection()

        # Check for similar existing friction
        similar_frictions = _find_similar_friction(conn, description)

        if similar_frictions:
            # Increment existing friction
            existing = similar_frictions[0]
            friction_id = existing["id"]
            new_count = existing["recurrence_count"] + 1

            conn.execute(f"""
                MATCH (f:Friction {{id: '{friction_id}'}})
                SET f.recurrence_count = {new_count}
            """)

            is_recurring = True

        else:
            # Create new friction
            friction_id = f"friction-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
            embedding = get_embedding(description)

            conn.execute(f"""
                CREATE (f:Friction {{
                    id: '{friction_id}',
                    description: '{_escape(description)}',
                    category: '{category}',
                    occurred_at: timestamp(),
                    recurrence_count: 1,
                    embedding: {embedding}
                }})
            """)

            is_recurring = False
            new_count = 1

        # Create PRODUCED relationship if session provided
        if session_id:
            try:
                conn.execute(f"""
                    MATCH (s:Session {{id: '{session_id}'}})
                    MATCH (f:Friction {{id: '{friction_id}'}})
                    MERGE (s)-[:PRODUCED {{valid_from: timestamp()}}]->(f)
                """)
            except Exception:
                pass

        # If blocking, create BLOCKED_BY relationship
        if blocking and session_id:
            try:
                conn.execute(f"""
                    MATCH (s:Session {{id: '{session_id}'}})
                    MATCH (f:Friction {{id: '{friction_id}'}})
                    CREATE (s)-[:BLOCKED_BY {{severity: 'blocking'}}]->(f)
                """)
            except Exception:
                pass

        # Emit telemetry event
        emit_knowledge_event(
            "friction",
            session_id or "unknown",
            friction_id,
            category=category,
            recurrence=is_recurring,
        )

        return {
            "success": True,
            "friction_id": friction_id,
            "is_recurring": is_recurring,
            "recurrence_count": new_count,
            "similar_frictions": [
                {"id": f["id"], "description": f["description"]} for f in similar_frictions
            ]
            if similar_frictions
            else [],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _find_similar_friction(conn, description: str) -> list[dict]:
    """Find similar existing friction points."""
    similar = []

    # Simple substring matching for now
    # TODO: Use embedding similarity when vector index is available
    try:
        # Take first 50 chars for matching
        search_term = description[:50].lower()

        result = conn.execute(f"""
            MATCH (f:Friction)
            WHERE toLower(f.description) CONTAINS '{_escape(search_term)}'
            RETURN f.id, f.description, f.recurrence_count
            LIMIT 5
        """)

        while result.has_next():
            row = result.get_next()
            similar.append(
                {
                    "id": row[0],
                    "description": row[1],
                    "recurrence_count": row[2] or 1,
                }
            )

    except Exception:
        pass

    return similar


def _escape(text: str) -> str:
    """Escape text for Cypher queries."""
    return text.replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
