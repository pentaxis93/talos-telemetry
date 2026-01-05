"""Journal MCP tools - write and query journal entries."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from talos_telemetry.db.connection import get_connection
from talos_telemetry.embeddings.model import get_embedding
from talos_telemetry.telemetry.events import emit_knowledge_event


def _now_iso() -> str:
    """Return current UTC time as ISO format string for Kuzu timestamp()."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def journal_write(
    content: str,
    category: str,
    session_id: str | None = None,
    domain: str | None = None,
    confidence: float | None = None,
) -> dict[str, Any]:
    """Write a journal entry.

    Creates appropriate entity (Insight, Observation, etc.) with embedding.

    Args:
        content: The journal entry text.
        category: Primary category (insight, observation, friction, reflection, experience, decision).
        session_id: Associated session for PRODUCED relationship.
        domain: Domain classification.
        confidence: Confidence level for insights (0.0-1.0).

    Returns:
        Dict with entity ID and extraction results.
    """
    try:
        conn = get_connection()

        # Generate ID and embedding
        entity_id = f"{category}-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
        embedding = get_embedding(content)

        # Map category to entity type
        entity_map = {
            "insight": "Insight",
            "observation": "Observation",
            "friction": "Friction",
            "reflection": "Reflection",
            "experience": "Experience",
            "decision": "Decision",
        }

        entity_type = entity_map.get(category)
        if not entity_type:
            return {
                "success": False,
                "error": f"Unknown category: {category}. Valid: {list(entity_map.keys())}",
            }

        # Build CREATE statement based on entity type
        if entity_type == "Insight":
            props = {
                "id": entity_id,
                "content": content,
                "created_at": "timestamp()",
                "embedding": embedding,
            }
            if domain:
                props["domain"] = domain
            if confidence is not None:
                props["confidence"] = confidence

            _create_entity(conn, entity_type, props)

        elif entity_type == "Observation":
            props = {
                "id": entity_id,
                "content": content,
                "observed_at": "timestamp()",
                "embedding": embedding,
            }
            if domain:
                props["domain"] = domain

            _create_entity(conn, entity_type, props)

        elif entity_type == "Friction":
            # For friction, use friction_log instead
            from talos_telemetry.mcp.friction import friction_log

            result = friction_log(content, "conceptual", session_id)
            return result

        elif entity_type == "Reflection":
            props = {
                "id": entity_id,
                "content": content,
                "occurred_at": "timestamp()",
                "embedding": embedding,
            }
            _create_entity(conn, entity_type, props)

        elif entity_type == "Experience":
            props = {
                "id": entity_id,
                "description": content,
                "occurred_at": "timestamp()",
                "embedding": embedding,
            }
            _create_entity(conn, entity_type, props)

        elif entity_type == "Decision":
            props = {
                "id": entity_id,
                "content": content,
                "made_at": "timestamp()",
                "embedding": embedding,
            }
            _create_entity(conn, entity_type, props)

        # Create PRODUCED_* relationship if session provided
        # Relationship table names are typed: PRODUCED_INSIGHT, PRODUCED_OBSERVATION, etc.
        if session_id:
            rel_type = f"PRODUCED_{entity_type.upper()}"
            try:
                conn.execute(f"""
                    MATCH (s:Session {{id: '{session_id}'}})
                    MATCH (e:{entity_type} {{id: '{entity_id}'}})
                    CREATE (s)-[:{rel_type} {{valid_from: timestamp('{_now_iso()}')}}]->(e)
                """)
            except Exception:
                pass  # Session might not exist

        # Create OPERATES_IN relationship if domain provided
        if domain:
            try:
                conn.execute(f"""
                    MATCH (e:{entity_type} {{id: '{entity_id}'}})
                    MATCH (d:Domain {{name: '{domain}'}})
                    CREATE (e)-[:OPERATES_IN]->(d)
                """)
            except Exception:
                pass  # Domain might not exist

        # Emit telemetry event
        emit_knowledge_event(
            category,
            session_id or "unknown",
            entity_id,
            domain=domain,
            confidence=confidence,
        )

        return {
            "success": True,
            "entry_id": entity_id,
            "entity_type": entity_type,
            "extracted_entities": [{"type": entity_type, "id": entity_id}],
            "extracted_relationships": [],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def journal_query(
    query: str,
    entity_types: list[str] | None = None,
    domains: list[str] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Semantic search over journal entries.

    Args:
        query: Natural language query.
        entity_types: Filter to specific entity types.
        domains: Filter to specific domains.
        limit: Maximum results.

    Returns:
        Dict with search results.
    """
    try:
        conn = get_connection()

        # Generate query embedding
        query_embedding = get_embedding(query)

        # Entity types to search
        search_types = entity_types or ["Insight", "Observation", "Pattern", "Belief"]

        results = []

        for entity_type in search_types:
            try:
                # Get content field name
                content_field = "content"
                if entity_type == "Experience":
                    content_field = "description"
                elif entity_type == "Pattern":
                    content_field = "description"

                # Vector search
                vector_results = conn.execute(f"""
                    CALL QUERY_VECTOR_INDEX('{entity_type}',
                        '{entity_type.lower()}_embedding_idx',
                        {query_embedding},
                        {limit})
                    YIELD node, score
                    RETURN node.id as id, node.{content_field} as content, score
                """)

                while vector_results.has_next():
                    row = vector_results.get_next()
                    results.append(
                        {
                            "entity_type": entity_type,
                            "id": row[0],
                            "content": row[1],
                            "score": row[2],
                        }
                    )

            except Exception:
                # Vector index might not exist, fall back to FTS
                try:
                    fts_results = conn.execute(f"""
                        CALL QUERY_FTS_INDEX('{entity_type}',
                            '{entity_type.lower()}_fts_idx',
                            '{_escape(query)}')
                        YIELD node, score
                        RETURN node.id as id, node.{content_field} as content, score
                        LIMIT {limit}
                    """)

                    while fts_results.has_next():
                        row = fts_results.get_next()
                        results.append(
                            {
                                "entity_type": entity_type,
                                "id": row[0],
                                "content": row[1],
                                "score": row[2],
                            }
                        )
                except Exception:
                    pass  # Index not available

        # Sort by score and limit
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        results = results[:limit]

        return {
            "success": True,
            "results": results,
            "total_found": len(results),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _create_entity(conn, entity_type: str, props: dict) -> None:
    """Create entity with given properties."""
    # Build property string
    prop_parts = []
    for key, value in props.items():
        if key == "embedding":
            prop_parts.append(f"{key}: {value}")
        elif value == "timestamp()":
            # Kuzu requires timestamp string argument
            prop_parts.append(f"{key}: timestamp('{_now_iso()}')")
        elif isinstance(value, str):
            prop_parts.append(f"{key}: '{_escape(value)}'")
        elif isinstance(value, (int, float)):
            prop_parts.append(f"{key}: {value}")
        elif isinstance(value, bool):
            prop_parts.append(f"{key}: {'true' if value else 'false'}")

    prop_string = ", ".join(prop_parts)
    conn.execute(f"CREATE (e:{entity_type} {{{prop_string}}})")


def _escape(text: str) -> str:
    """Escape text for Cypher queries."""
    return text.replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
