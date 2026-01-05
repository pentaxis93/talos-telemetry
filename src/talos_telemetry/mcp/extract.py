"""Intelligent journal extraction MCP tool - LLM-powered entity extraction."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from talos_telemetry.db.connection import get_connection
from talos_telemetry.embeddings.model import get_embedding
from talos_telemetry.telemetry.events import emit_knowledge_event


def _now_iso() -> str:
    """Return current UTC time as ISO format string for Kuzu timestamp()."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _escape(text: str) -> str:
    """Escape text for Cypher queries."""
    return text.replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")


def journal_extract(
    content: str,
    session_id: str | None = None,
    provider: str = "openai",
    model: str | None = None,
) -> dict[str, Any]:
    """Extract and store entities from free-form text using LLM.

    This is the intelligent alternative to journal_write - it uses LLM
    to automatically classify and extract structured entities from natural
    language input.

    Args:
        content: Free-form text to extract entities from.
        session_id: Associated session for PRODUCED relationships.
        provider: LLM provider ("openai" or "anthropic").
        model: Model to use (defaults to gpt-4o-mini or claude-3-haiku).

    Returns:
        Dict with extraction results and stored entity IDs.
    """
    try:
        # Import extraction module (lazy to avoid requiring openai/anthropic)
        try:
            from talos_telemetry.extraction.extractor import extract_entities
        except ImportError as e:
            return {
                "success": False,
                "error": f"Extraction requires LLM package. Install with: pip install talos-telemetry[extraction]. Details: {e}",
            }

        # Extract entities using LLM
        extraction_result = extract_entities(content, provider=provider, model=model)

        if not extraction_result.entities:
            return {
                "success": True,
                "message": "No entities extracted from content",
                "stored_entities": [],
                "stored_relationships": [],
            }

        conn = get_connection()
        stored_entities = []
        entity_id_map = {}  # Map extraction index to stored entity ID

        # Store each extracted entity
        for i, entity in enumerate(extraction_result.entities):
            entity_id = _store_entity(
                conn=conn,
                entity_type=entity.entity_type,
                content=entity.content,
                confidence=entity.confidence,
                domain=entity.domain,
                session_id=session_id,
            )

            if entity_id:
                entity_id_map[i] = (entity_id, entity.entity_type)
                stored_entities.append(
                    {
                        "id": entity_id,
                        "type": entity.entity_type,
                        "content": entity.content,
                        "confidence": entity.confidence,
                        "domain": entity.domain,
                    }
                )

                # Emit telemetry
                emit_knowledge_event(
                    entity.entity_type.lower(),
                    session_id or "unknown",
                    entity_id,
                    domain=entity.domain,
                    confidence=entity.confidence,
                )

        # Store relationships between entities
        stored_relationships = []
        for rel in extraction_result.relationships:
            from_idx = rel.get("from_index")
            to_idx = rel.get("to_index")
            rel_type = rel.get("relationship_type")

            if from_idx in entity_id_map and to_idx in entity_id_map:
                from_id, from_type = entity_id_map[from_idx]
                to_id, to_type = entity_id_map[to_idx]

                rel_table = _get_relationship_table(from_type, to_type, rel_type)
                if rel_table:
                    try:
                        conn.execute(f"""
                            MATCH (a:{from_type} {{id: '{from_id}'}})
                            MATCH (b:{to_type} {{id: '{to_id}'}})
                            CREATE (a)-[:{rel_table} {{valid_from: timestamp('{_now_iso()}')}}]->(b)
                        """)
                        stored_relationships.append(
                            {
                                "from_id": from_id,
                                "to_id": to_id,
                                "type": rel_table,
                            }
                        )
                    except Exception:
                        pass  # Relationship creation failed

        return {
            "success": True,
            "stored_entities": stored_entities,
            "stored_relationships": stored_relationships,
            "extraction_count": len(extraction_result.entities),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _store_entity(
    conn,
    entity_type: str,
    content: str,
    confidence: float,
    domain: str | None,
    session_id: str | None,
) -> str | None:
    """Store a single entity in the graph.

    Returns:
        Entity ID if stored successfully, None otherwise.
    """
    entity_id = (
        f"{entity_type.lower()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
    )
    embedding = get_embedding(content)

    try:
        if entity_type == "Insight":
            props = _build_props(
                id=entity_id,
                content=content,
                created_at="timestamp()",
                embedding=embedding,
                confidence=confidence,
                domain=domain,
            )
            conn.execute(f"CREATE (e:Insight {{{props}}})")

        elif entity_type == "Observation":
            props = _build_props(
                id=entity_id,
                content=content,
                observed_at="timestamp()",
                embedding=embedding,
                domain=domain,
            )
            conn.execute(f"CREATE (e:Observation {{{props}}})")

        elif entity_type == "Friction":
            props = _build_props(
                id=entity_id,
                description=content,
                occurred_at="timestamp()",
                embedding=embedding,
                category="extracted",
                recurrence_count=1,
            )
            conn.execute(f"CREATE (e:Friction {{{props}}})")

        elif entity_type == "Pattern":
            props = _build_props(
                id=entity_id,
                name=content[:50],
                description=content,
                first_noticed="timestamp()",
                embedding=embedding,
                occurrence_count=1,
                status="emerging",
            )
            conn.execute(f"CREATE (e:Pattern {{{props}}})")

        elif entity_type == "Belief":
            props = _build_props(
                id=entity_id,
                content=content,
                adopted_at="timestamp()",
                embedding=embedding,
                confidence=confidence,
                domain=domain,
                source="extracted",
            )
            conn.execute(f"CREATE (e:Belief {{{props}}})")

        elif entity_type == "Decision":
            props = _build_props(
                id=entity_id,
                content=content,
                made_at="timestamp()",
                embedding=embedding,
            )
            conn.execute(f"CREATE (e:Decision {{{props}}})")

        elif entity_type == "Experience":
            props = _build_props(
                id=entity_id,
                description=content,
                occurred_at="timestamp()",
                embedding=embedding,
            )
            conn.execute(f"CREATE (e:Experience {{{props}}})")

        elif entity_type == "Reflection":
            props = _build_props(
                id=entity_id,
                content=content,
                occurred_at="timestamp()",
                embedding=embedding,
            )
            conn.execute(f"CREATE (e:Reflection {{{props}}})")

        else:
            return None

        # Create PRODUCED relationship if session provided
        if session_id:
            rel_type = f"PRODUCED_{entity_type.upper()}"
            try:
                conn.execute(f"""
                    MATCH (s:Session {{id: '{session_id}'}})
                    MATCH (e:{entity_type} {{id: '{entity_id}'}})
                    CREATE (s)-[:{rel_type} {{valid_from: timestamp('{_now_iso()}')}}]->(e)
                """)
            except Exception:
                pass

        return entity_id

    except Exception:
        return None


def _build_props(**kwargs) -> str:
    """Build property string for Cypher CREATE."""
    parts = []
    for key, value in kwargs.items():
        if value is None:
            continue
        if key == "embedding":
            parts.append(f"{key}: {value}")
        elif value == "timestamp()":
            parts.append(f"{key}: timestamp('{_now_iso()}')")
        elif isinstance(value, str):
            parts.append(f"{key}: '{_escape(value)}'")
        elif isinstance(value, (int, float)):
            parts.append(f"{key}: {value}")
        elif isinstance(value, bool):
            parts.append(f"{key}: {'true' if value else 'false'}")
    return ", ".join(parts)


def _get_relationship_table(from_type: str, to_type: str, rel_type: str) -> str | None:
    """Get the correct relationship table name for entity types.

    Kuzu requires specific table names for each FROM-TO pair.
    """
    # Map common extracted relationships to Kuzu tables
    rel_map = {
        ("Friction", "Insight", "LED_TO"): "FRICTION_LED_TO_INSIGHT",
        ("Insight", "Insight", "LED_TO"): "LED_TO",
        ("Insight", "Belief", "LED_TO"): "INSIGHT_LED_TO_BELIEF",
        ("Insight", "Decision", "LED_TO"): "INSIGHT_LED_TO_DECISION",
        ("Experience", "Insight", "LED_TO"): "EXPERIENCE_LED_TO_INSIGHT",
        ("Belief", "Belief", "CONTRADICTS"): "CONTRADICTS",
        ("Belief", "Belief", "REFINES"): "BELIEF_REFINES",
        ("Insight", "Insight", "REFINES"): "INSIGHT_REFINES",
        ("Friction", "Limitation", "REVEALED"): "FRICTION_REVEALED_LIMITATION",
        ("Friction", "Capability", "REVEALED"): "FRICTION_REVEALED_CAPABILITY",
        ("Experience", "Limitation", "REVEALED"): "EXPERIENCE_REVEALED_LIMITATION",
        ("Experience", "Capability", "REVEALED"): "EXPERIENCE_REVEALED_CAPABILITY",
    }

    return rel_map.get((from_type, to_type, rel_type))
