"""The Pathfinder (Navigator) - maps pathways and optimizes retrieval."""

from typing import Any

from talos_telemetry.db.connection import get_connection


class Pathfinder:
    """The Navigator librarian - maps pathways and facilitates retrieval.

    Responsibilities:
    - Maintain and optimize vector indices
    - Generate pathway maps (how concepts connect)
    - Surface underutilized knowledge
    - Create retrieval shortcuts for common query patterns
    - Build semantic clusters for faster search
    """

    def __init__(self):
        self.conn = get_connection()
        self.report = []

    def run(self) -> dict[str, Any]:
        """Run the pathfinder.

        Returns:
            Dict with pathfinding results.
        """
        self.report = []

        # Run pathfinding tasks
        index_status = self._check_index_health()
        pathway_map = self._generate_pathway_map()
        underutilized = self._find_underutilized_knowledge()
        clusters = self._identify_semantic_clusters()

        return {
            "success": True,
            "index_status": index_status,
            "pathway_map": pathway_map,
            "underutilized_knowledge": underutilized,
            "semantic_clusters": clusters,
            "report": self.report,
        }

    def _check_index_health(self) -> dict:
        """Check health of vector and FTS indices."""
        status = {
            "vector_indices": [],
            "fts_indices": [],
            "needs_rebuild": [],
        }

        entity_types_with_embeddings = [
            "Insight",
            "Observation",
            "Pattern",
            "Belief",
            "Decision",
            "Experience",
            "Friction",
            "Question",
            "Sutra",
            "Goal",
            "Capability",
            "Limitation",
            "Protocol",
            "Reflection",
        ]

        for entity_type in entity_types_with_embeddings:
            # Check if entities exist without embeddings
            try:
                result = self.conn.execute(f"""
                    MATCH (e:{entity_type})
                    WHERE e.embedding IS NULL
                    RETURN count(e) as count
                """)

                row = result.get_next()
                missing = row[0] if row else 0

                if missing > 0:
                    status["needs_rebuild"].append(
                        {
                            "entity_type": entity_type,
                            "missing_embeddings": missing,
                        }
                    )
                    self.report.append(f"{entity_type}: {missing} entities missing embeddings")

            except Exception:
                pass

        return status

    def _generate_pathway_map(self) -> dict:
        """Generate a map of how concepts connect."""
        pathway_map = {
            "domains": {},
            "high_connectivity_nodes": [],
        }

        try:
            # Find domains and their connections
            result = self.conn.execute("""
                MATCH (d:Domain)<-[:OPERATES_IN]-(e)
                WITH d, count(e) as entity_count
                RETURN d.name, entity_count
                ORDER BY entity_count DESC
            """)

            while result.has_next():
                row = result.get_next()
                pathway_map["domains"][row[0]] = row[1]

        except Exception as e:
            self.report.append(f"Error mapping domains: {e}")

        try:
            # Find high-connectivity nodes (hubs)
            result = self.conn.execute("""
                MATCH (e)-[r]-()
                WITH e, labels(e)[0] as type, count(r) as connections
                WHERE connections > 5
                RETURN type, e.id, connections
                ORDER BY connections DESC
                LIMIT 20
            """)

            while result.has_next():
                row = result.get_next()
                pathway_map["high_connectivity_nodes"].append(
                    {
                        "type": row[0],
                        "id": row[1],
                        "connections": row[2],
                    }
                )

        except Exception as e:
            self.report.append(f"Error finding hubs: {e}")

        return pathway_map

    def _find_underutilized_knowledge(self) -> list[dict]:
        """Find knowledge entities that are never accessed."""
        underutilized = []

        try:
            # Find Beliefs never INHERITED
            result = self.conn.execute("""
                MATCH (b:Belief)
                WHERE NOT EXISTS {
                    MATCH ()-[:INHERITED]->(b)
                }
                AND b.adopted_at IS NOT NULL
                RETURN b.id, b.content
                LIMIT 10
            """)

            while result.has_next():
                row = result.get_next()
                underutilized.append(
                    {
                        "type": "Belief",
                        "id": row[0],
                        "content": row[1][:100] if row[1] else "",
                        "reason": "Never inherited by any session",
                    }
                )

        except Exception:
            pass

        try:
            # Find Insights with no outgoing relationships
            result = self.conn.execute("""
                MATCH (i:Insight)
                WHERE NOT EXISTS {
                    MATCH (i)-[:LED_TO|CRYSTALLIZED_INTO|EVOLVED_FROM]->()
                }
                RETURN i.id, i.content
                LIMIT 10
            """)

            while result.has_next():
                row = result.get_next()
                underutilized.append(
                    {
                        "type": "Insight",
                        "id": row[0],
                        "content": row[1][:100] if row[1] else "",
                        "reason": "No downstream effects",
                    }
                )

        except Exception:
            pass

        if underutilized:
            self.report.append(f"Found {len(underutilized)} underutilized knowledge entities")

        return underutilized

    def _identify_semantic_clusters(self) -> list[dict]:
        """Identify semantic clusters for faster retrieval."""
        clusters = []

        try:
            # Use domain as a natural clustering
            result = self.conn.execute("""
                MATCH (d:Domain)<-[:OPERATES_IN]-(e)
                WITH d.name as domain, collect(e.id) as entities
                WHERE size(entities) > 3
                RETURN domain, size(entities) as size
                ORDER BY size DESC
            """)

            while result.has_next():
                row = result.get_next()
                clusters.append(
                    {
                        "cluster_type": "domain",
                        "name": row[0],
                        "size": row[1],
                    }
                )

        except Exception:
            pass

        try:
            # Find naturally clustered sessions (by goal similarity)
            result = self.conn.execute("""
                MATCH (s1:Session)-[:SERVES]->(g:Goal)<-[:SERVES]-(s2:Session)
                WHERE s1.id < s2.id
                WITH g, count(DISTINCT s1) + count(DISTINCT s2) as session_count
                WHERE session_count > 2
                RETURN g.description, session_count
                ORDER BY session_count DESC
                LIMIT 10
            """)

            while result.has_next():
                row = result.get_next()
                clusters.append(
                    {
                        "cluster_type": "goal",
                        "name": row[0][:50] if row[0] else "Unknown",
                        "size": row[1],
                    }
                )

        except Exception:
            pass

        return clusters

    def get_retrieval_shortcuts(self) -> dict:
        """Get optimized queries for common retrieval patterns."""
        return {
            "recent_insights": """
                MATCH (i:Insight)
                WHERE i.created_at > datetime() - duration({days: 7})
                RETURN i.id, i.content, i.domain
                ORDER BY i.created_at DESC
                LIMIT 20
            """,
            "active_patterns": """
                MATCH (p:Pattern)
                WHERE p.status = 'confirmed'
                RETURN p.id, p.name, p.occurrence_count
                ORDER BY p.occurrence_count DESC
                LIMIT 10
            """,
            "blocking_friction": """
                MATCH (f:Friction)<-[:BLOCKED_BY {severity: 'blocking'}]-()
                WHERE f.resolution IS NULL
                RETURN f.id, f.description, f.category
            """,
            "cross_domain_insights": """
                MATCH (i:Insight)-[:OPERATES_IN]->(d1:Domain)
                MATCH (i)-[:LED_TO]->(i2:Insight)-[:OPERATES_IN]->(d2:Domain)
                WHERE d1 <> d2
                RETURN i.id, d1.name, i2.id, d2.name
                LIMIT 20
            """,
        }
