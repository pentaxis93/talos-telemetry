"""The Protector (Guardian) - protects integrity and prunes entropy."""

from datetime import datetime, timedelta
from typing import Any

from talos_telemetry.db.connection import get_connection


class Protector:
    """The Guardian librarian - protects integrity and prunes entropy.

    Responsibilities:
    - Deduplicate entities (same content, different IDs)
    - Resolve stale Questions (mark abandoned after threshold)
    - Archive old Sessions to cold storage
    - Validate graph consistency (orphan nodes, broken relationships)
    - Prune low-confidence entities that never crystallized
    """

    # Thresholds
    QUESTION_STALE_DAYS = 30  # Days before question is considered stale
    SESSION_ARCHIVE_DAYS = 90  # Days before session can be archived
    MIN_CONFIDENCE_THRESHOLD = 0.3  # Below this, consider pruning
    OBSERVATION_MAX_AGE_DAYS = 60  # Observations older than this without crystallization

    def __init__(self):
        self.conn = get_connection()
        self.report = []

    def run(self) -> dict[str, Any]:
        """Run the protector.

        Returns:
            Dict with protection results.
        """
        self.report = []

        # Run protection tasks
        duplicates = self._deduplicate_entities()
        stale_questions = self._mark_stale_questions()
        archived = self._archive_old_sessions()
        orphans = self._find_orphan_nodes()
        pruned = self._prune_low_value_entities()

        return {
            "success": True,
            "duplicates_merged": duplicates,
            "stale_questions_marked": stale_questions,
            "sessions_archived": archived,
            "orphan_nodes": orphans,
            "entities_pruned": pruned,
            "report": self.report,
        }

    def _deduplicate_entities(self) -> int:
        """Find and merge duplicate entities."""
        merged = 0

        # Check for duplicate Beliefs (same content)
        try:
            result = self.conn.execute("""
                MATCH (b1:Belief), (b2:Belief)
                WHERE b1.id < b2.id
                AND b1.content = b2.content
                RETURN b1.id, b2.id
            """)

            while result.has_next():
                row = result.get_next()
                self._merge_entities("Belief", row[0], row[1])
                merged += 1
                self.report.append(f"Merged duplicate beliefs: {row[0]}, {row[1]}")

        except Exception as e:
            self.report.append(f"Error deduplicating beliefs: {e}")

        # Check for duplicate Insights
        try:
            result = self.conn.execute("""
                MATCH (i1:Insight), (i2:Insight)
                WHERE i1.id < i2.id
                AND i1.content = i2.content
                RETURN i1.id, i2.id
            """)

            while result.has_next():
                row = result.get_next()
                self._merge_entities("Insight", row[0], row[1])
                merged += 1
                self.report.append(f"Merged duplicate insights: {row[0]}, {row[1]}")

        except Exception as e:
            self.report.append(f"Error deduplicating insights: {e}")

        return merged

    def _merge_entities(self, entity_type: str, keep_id: str, remove_id: str) -> None:
        """Merge two entities, keeping the first and removing the second."""
        try:
            # Redirect all relationships to the kept entity
            self.conn.execute(f"""
                MATCH (e:{entity_type} {{id: '{remove_id}'}})-[r]->(target)
                MATCH (keep:{entity_type} {{id: '{keep_id}'}})
                CREATE (keep)-[r2:{{type(r)}}]->(target)
                DELETE r
            """)

            self.conn.execute(f"""
                MATCH (source)-[r]->(e:{entity_type} {{id: '{remove_id}'}})
                MATCH (keep:{entity_type} {{id: '{keep_id}'}})
                CREATE (source)-[r2:{{type(r)}}]->(keep)
                DELETE r
            """)

            # Delete the duplicate
            self.conn.execute(f"""
                MATCH (e:{entity_type} {{id: '{remove_id}'}})
                DELETE e
            """)

        except Exception as e:
            self.report.append(f"Error merging entities: {e}")

    def _mark_stale_questions(self) -> int:
        """Mark old unresolved questions as stale."""
        marked = 0

        try:
            cutoff = datetime.now() - timedelta(days=self.QUESTION_STALE_DAYS)

            result = self.conn.execute(f"""
                MATCH (q:Question)
                WHERE q.resolved_at IS NULL
                AND q.raised_at < datetime('{cutoff.isoformat()}')
                AND (q.urgency IS NULL OR q.urgency <> 'abandoned')
                SET q.urgency = 'abandoned'
                RETURN count(q) as count
            """)

            row = result.get_next()
            marked = row[0] if row else 0

            if marked > 0:
                self.report.append(f"Marked {marked} questions as abandoned")

        except Exception as e:
            self.report.append(f"Error marking stale questions: {e}")

        return marked

    def _archive_old_sessions(self) -> int:
        """Archive old sessions (mark for cold storage)."""
        archived = 0

        try:
            cutoff = datetime.now() - timedelta(days=self.SESSION_ARCHIVE_DAYS)

            # Just mark sessions as archived for now
            # Actual cold storage migration would be separate
            result = self.conn.execute(f"""
                MATCH (s:Session)
                WHERE s.ended_at IS NOT NULL
                AND s.ended_at < datetime('{cutoff.isoformat()}')
                AND (s.archived IS NULL OR s.archived = false)
                SET s.archived = true
                RETURN count(s) as count
            """)

            row = result.get_next()
            archived = row[0] if row else 0

            if archived > 0:
                self.report.append(f"Archived {archived} old sessions")

        except Exception as e:
            self.report.append(f"Error archiving sessions: {e}")

        return archived

    def _find_orphan_nodes(self) -> list[dict]:
        """Find nodes with no relationships."""
        orphans = []

        entity_types = ["Insight", "Observation", "Pattern", "Belief", "Friction"]

        for entity_type in entity_types:
            try:
                result = self.conn.execute(f"""
                    MATCH (e:{entity_type})
                    WHERE NOT EXISTS {{
                        MATCH (e)-[]-()
                    }}
                    RETURN e.id, e.content
                    LIMIT 10
                """)

                while result.has_next():
                    row = result.get_next()
                    orphans.append(
                        {
                            "type": entity_type,
                            "id": row[0],
                            "content": row[1][:50] if row[1] else "",
                        }
                    )

            except Exception:
                pass

        if orphans:
            self.report.append(f"Found {len(orphans)} orphan nodes")

        return orphans

    def _prune_low_value_entities(self) -> int:
        """Prune low-confidence entities that never crystallized."""
        pruned = 0

        try:
            cutoff = datetime.now() - timedelta(days=self.OBSERVATION_MAX_AGE_DAYS)

            # Find old observations that never crystallized
            result = self.conn.execute(f"""
                MATCH (o:Observation)
                WHERE o.observed_at < datetime('{cutoff.isoformat()}')
                AND NOT EXISTS {{
                    MATCH (o)-[:MERGED_INTO|CRYSTALLIZED_INTO]->()
                }}
                RETURN o.id
            """)

            to_delete = []
            while result.has_next():
                row = result.get_next()
                to_delete.append(row[0])

            # Delete orphaned observations
            for obs_id in to_delete[:50]:  # Limit to 50 per run
                try:
                    self.conn.execute(f"""
                        MATCH (o:Observation {{id: '{obs_id}'}})
                        DETACH DELETE o
                    """)
                    pruned += 1
                except Exception:
                    pass

            if pruned > 0:
                self.report.append(f"Pruned {pruned} stale observations")

        except Exception as e:
            self.report.append(f"Error pruning entities: {e}")

        return pruned
