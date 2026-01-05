"""The Synthesizer (Alchemist) - consolidates and synthesizes understanding."""

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from talos_telemetry.db.connection import get_connection
from talos_telemetry.embeddings.model import cosine_similarity, get_embedding


class Synthesizer:
    """The Alchemist librarian - synthesizes new understanding from accumulated data.

    Responsibilities:
    - Consolidate similar Observations into crystallized Insights
    - Detect emerging Patterns from session clusters
    - Surface connections across Domains
    - Generate weekly synthesis reports
    """

    # Thresholds
    SIMILARITY_THRESHOLD = 0.85  # For consolidation
    OBSERVATION_AGE_THRESHOLD = 7  # Days before observation should crystallize
    MIN_OBSERVATIONS_FOR_INSIGHT = 2  # Minimum similar observations to merge

    def __init__(self):
        self.conn = get_connection()
        self.report = []

    def run(self) -> dict[str, Any]:
        """Run the synthesizer.

        Returns:
            Dict with synthesis results.
        """
        self.report = []

        # Run synthesis tasks
        consolidated = self._consolidate_observations()
        patterns = self._detect_emerging_patterns()
        connections = self._surface_cross_domain_connections()

        return {
            "success": True,
            "consolidated_observations": consolidated,
            "patterns_detected": patterns,
            "cross_domain_connections": connections,
            "report": self.report,
        }

    def _consolidate_observations(self) -> int:
        """Consolidate similar observations into insights."""
        consolidated = 0

        try:
            # Find old observations
            cutoff = datetime.now() - timedelta(days=self.OBSERVATION_AGE_THRESHOLD)

            result = self.conn.execute(f"""
                MATCH (o:Observation)
                WHERE o.observed_at < datetime('{cutoff.isoformat()}')
                RETURN o.id, o.content, o.embedding, o.domain
            """)

            observations = []
            while result.has_next():
                row = result.get_next()
                observations.append(
                    {
                        "id": row[0],
                        "content": row[1],
                        "embedding": row[2],
                        "domain": row[3],
                    }
                )

            # Group similar observations
            groups = self._group_by_similarity(observations)

            for group in groups:
                if len(group) >= self.MIN_OBSERVATIONS_FOR_INSIGHT:
                    self._merge_into_insight(group)
                    consolidated += len(group)
                    self.report.append(f"Merged {len(group)} observations into insight")

        except Exception as e:
            self.report.append(f"Error consolidating observations: {e}")

        return consolidated

    def _group_by_similarity(self, observations: list[dict]) -> list[list[dict]]:
        """Group observations by embedding similarity."""
        if not observations:
            return []

        groups = []
        used = set()

        for i, obs1 in enumerate(observations):
            if obs1["id"] in used:
                continue

            group = [obs1]
            used.add(obs1["id"])

            for j, obs2 in enumerate(observations[i + 1 :], i + 1):
                if obs2["id"] in used:
                    continue

                if obs1["embedding"] and obs2["embedding"]:
                    similarity = cosine_similarity(obs1["embedding"], obs2["embedding"])
                    if similarity >= self.SIMILARITY_THRESHOLD:
                        group.append(obs2)
                        used.add(obs2["id"])

            if len(group) > 1:
                groups.append(group)

        return groups

    def _merge_into_insight(self, observations: list[dict]) -> str:
        """Merge observations into a single insight."""
        # Combine content
        contents = [o["content"] for o in observations]
        combined_content = " | ".join(contents[:3])  # Limit to avoid huge content
        if len(contents) > 3:
            combined_content += f" | (+{len(contents) - 3} more)"

        # Use domain from first observation
        domain = observations[0].get("domain", "general")

        # Create insight
        insight_id = f"insight-synthesized-{uuid4().hex[:8]}"
        embedding = get_embedding(combined_content)

        self.conn.execute(f"""
            CREATE (i:Insight {{
                id: '{insight_id}',
                content: '{_escape(combined_content)}',
                created_at: timestamp(),
                domain: '{domain}',
                confidence: 0.7,
                embedding: {embedding}
            }})
        """)

        # Create MERGED_INTO relationships
        for obs in observations:
            try:
                self.conn.execute(f"""
                    MATCH (o:Observation {{id: '{obs["id"]}'}})
                    MATCH (i:Insight {{id: '{insight_id}'}})
                    CREATE (o)-[:MERGED_INTO {{merged_at: timestamp()}}]->(i)
                """)
            except Exception:
                pass

        return insight_id

    def _detect_emerging_patterns(self) -> int:
        """Detect emerging patterns from session data."""
        patterns_created = 0

        try:
            # Find friction that recurs but isn't a pattern yet
            result = self.conn.execute("""
                MATCH (f:Friction)
                WHERE f.recurrence_count >= 3
                AND NOT EXISTS {
                    MATCH (f)-[:MANIFESTATION_OF]->(:Pattern)
                }
                RETURN f.id, f.description, f.category, f.recurrence_count
            """)

            while result.has_next():
                row = result.get_next()
                pattern_id = self._create_pattern_from_friction(row[0], row[1], row[2], row[3])
                if pattern_id:
                    patterns_created += 1
                    self.report.append(f"Created pattern from recurring friction: {row[1][:50]}")

        except Exception as e:
            self.report.append(f"Error detecting patterns: {e}")

        return patterns_created

    def _create_pattern_from_friction(
        self, friction_id: str, description: str, category: str, count: int
    ) -> str:
        """Create a pattern from recurring friction."""
        pattern_id = f"pattern-from-friction-{uuid4().hex[:8]}"
        embedding = get_embedding(description)

        try:
            self.conn.execute(f"""
                CREATE (p:Pattern {{
                    id: '{pattern_id}',
                    name: 'Recurring {category} friction',
                    description: '{_escape(description)}',
                    first_noticed: timestamp(),
                    occurrence_count: {count},
                    status: 'emerging',
                    embedding: {embedding}
                }})
            """)

            # Link friction to pattern
            self.conn.execute(f"""
                MATCH (f:Friction {{id: '{friction_id}'}})
                MATCH (p:Pattern {{id: '{pattern_id}'}})
                CREATE (f)-[:MANIFESTATION_OF {{valid_from: timestamp()}}]->(p)
            """)

            return pattern_id

        except Exception:
            return ""

    def _surface_cross_domain_connections(self) -> int:
        """Surface connections across domains."""
        connections = 0

        try:
            # Find insights in different domains with high similarity
            result = self.conn.execute("""
                MATCH (i1:Insight)-[:OPERATES_IN]->(d1:Domain)
                MATCH (i2:Insight)-[:OPERATES_IN]->(d2:Domain)
                WHERE d1 <> d2
                AND NOT EXISTS {
                    MATCH (i1)-[:LED_TO|EVOLVED_FROM]-(i2)
                }
                RETURN i1.id, i1.embedding, d1.name, i2.id, i2.embedding, d2.name
                LIMIT 100
            """)

            pairs_to_connect = []
            while result.has_next():
                row = result.get_next()
                if row[1] and row[4]:  # Both have embeddings
                    similarity = cosine_similarity(row[1], row[4])
                    if similarity >= 0.8:
                        pairs_to_connect.append((row[0], row[3], similarity))

            # Create LED_TO relationships for similar cross-domain insights
            for id1, id2, similarity in pairs_to_connect[:10]:  # Limit to 10
                try:
                    self.conn.execute(f"""
                        MATCH (i1:Insight {{id: '{id1}'}})
                        MATCH (i2:Insight {{id: '{id2}'}})
                        CREATE (i1)-[:LED_TO {{
                            valid_from: timestamp(),
                            contribution: 'contextual'
                        }}]->(i2)
                    """)
                    connections += 1
                except Exception:
                    pass

        except Exception as e:
            self.report.append(f"Error surfacing connections: {e}")

        return connections


def _escape(text: str) -> str:
    """Escape text for Cypher queries."""
    return text.replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
