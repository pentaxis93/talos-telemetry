"""Reflection MCP tool."""

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from talos_telemetry.db.connection import get_connection
from talos_telemetry.embeddings.model import get_embedding
from talos_telemetry.telemetry.events import emit_event


def reflect(
    content: str,
    trigger: Optional[str] = None,
    session_id: Optional[str] = None,
) -> dict[str, Any]:
    """Capture a meta-cognitive reflection.

    Creates Reflection entity and optionally extracts insights.

    Args:
        content: The reflection content.
        trigger: What prompted this reflection.
        session_id: Associated session.

    Returns:
        Dict with reflection ID and extracted entities.
    """
    try:
        conn = get_connection()

        # Generate ID and embedding
        reflection_id = f"reflection-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
        embedding = get_embedding(content)

        # Create Reflection entity
        trigger_clause = f", trigger: '{_escape(trigger)}'" if trigger else ""

        conn.execute(f"""
            CREATE (r:Reflection {{
                id: '{reflection_id}',
                content: '{_escape(content)}',
                occurred_at: timestamp(),
                embedding: {embedding}
                {trigger_clause}
            }})
        """)

        # Create PRODUCED relationship if session provided
        if session_id:
            try:
                conn.execute(f"""
                    MATCH (s:Session {{id: '{session_id}'}})
                    MATCH (r:Reflection {{id: '{reflection_id}'}})
                    CREATE (s)-[:PRODUCED {{valid_from: timestamp()}}]->(r)
                """)
            except Exception:
                pass

        # Emit telemetry event
        emit_event(
            "reflection.triggered",
            {
                "talos.session.id": session_id or "unknown",
                "talos.reflection.id": reflection_id,
                "talos.reflection.trigger": trigger or "manual",
                "talos.reflection.type": _classify_reflection(content),
            },
            trace_id=f"sess-{session_id}" if session_id else None,
        )

        # Simple insight extraction from reflection
        extracted_entities = []

        # Check for insight markers in content
        insight_markers = ["realized", "understood", "learned", "noticed", "discovered"]
        content_lower = content.lower()

        if any(marker in content_lower for marker in insight_markers):
            # Extract potential insight
            insight_id = f"insight-from-reflection-{uuid4().hex[:8]}"

            try:
                insight_embedding = get_embedding(content)

                conn.execute(f"""
                    CREATE (i:Insight {{
                        id: '{insight_id}',
                        content: '{_escape(content[:500])}',
                        created_at: timestamp(),
                        domain: 'meta-cognitive',
                        embedding: {insight_embedding}
                    }})
                """)

                # Link reflection to insight
                conn.execute(f"""
                    MATCH (r:Reflection {{id: '{reflection_id}'}})
                    MATCH (i:Insight {{id: '{insight_id}'}})
                    CREATE (r)-[:CRYSTALLIZED_INTO {{valid_from: timestamp()}}]->(i)
                """)

                extracted_entities.append(
                    {
                        "type": "Insight",
                        "id": insight_id,
                    }
                )

            except Exception:
                pass

        return {
            "success": True,
            "reflection_id": reflection_id,
            "extracted_entities": extracted_entities,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _classify_reflection(content: str) -> str:
    """Classify the type of reflection."""
    content_lower = content.lower()

    if "query" in content_lower or "search" in content_lower:
        return "query_result"
    elif "pattern" in content_lower or "notice" in content_lower:
        return "pattern_notice"
    elif "session" in content_lower or "close" in content_lower:
        return "session_close"
    else:
        return "general"


def _escape(text: str) -> str:
    """Escape text for Cypher queries."""
    return text.replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
