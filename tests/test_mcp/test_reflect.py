"""Tests for reflect MCP tool."""

from datetime import datetime, timezone

from talos_telemetry.db.connection import get_connection
from talos_telemetry.mcp.reflect import get_recent_reflections, reflect
from talos_telemetry.mcp.session import session_open


def _now_iso() -> str:
    """Return current UTC time as ISO format string for Kuzu timestamp()."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class TestReflect:
    """Tests for reflect tool."""

    def test_reflect_creates_reflection(self, fresh_db):
        """reflect creates Reflection entity."""
        result = reflect("I notice I'm approaching this problem too narrowly")

        assert result["success"] is True
        assert "reflection_id" in result

        # Verify in graph
        conn = get_connection()
        query_result = conn.execute(f"""
            MATCH (r:Reflection {{id: '{result["reflection_id"]}'}})
            RETURN r.content
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert "approaching this problem" in row[0]

    def test_reflect_with_trigger(self, fresh_db):
        """reflect stores trigger information."""
        result = reflect(
            "Realized I need to step back",
            trigger="friction",
        )

        assert result["success"] is True

        # Verify trigger stored
        conn = get_connection()
        query_result = conn.execute(f"""
            MATCH (r:Reflection {{id: '{result["reflection_id"]}'}})
            RETURN r.trigger
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] == "friction"

    def test_reflect_with_session(self, fresh_db):
        """reflect creates PRODUCED_REFLECTION relationship to session."""
        # Create session first
        session_result = session_open("test-session-reflect", goal="Test reflection")
        assert session_result["success"] is True

        result = reflect(
            "Noticing a pattern in my approach",
            session_id="test-session-reflect",
        )

        assert result["success"] is True

        # Verify relationship
        conn = get_connection()
        rel_result = conn.execute(f"""
            MATCH (s:Session {{id: 'test-session-reflect'}})-[:PRODUCED_REFLECTION]->(r:Reflection {{id: '{result["reflection_id"]}'}})
            RETURN r.id
        """)
        assert rel_result.has_next()

    def test_reflect_extracts_insight_from_realized(self, fresh_db):
        """reflect extracts Insight when 'realized' appears in content."""
        result = reflect("I realized that TDD forces better design decisions")

        assert result["success"] is True
        assert len(result["extracted_entities"]) == 1
        assert result["extracted_entities"][0]["type"] == "Insight"

        # Verify insight created
        conn = get_connection()
        insight_id = result["extracted_entities"][0]["id"]
        query_result = conn.execute(f"""
            MATCH (i:Insight {{id: '{insight_id}'}})
            RETURN i.content, i.domain
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert "TDD" in row[0]
        assert row[1] == "meta-cognitive"

    def test_reflect_extracts_insight_from_learned(self, fresh_db):
        """reflect extracts Insight when 'learned' appears in content."""
        result = reflect("I learned that context windows are finite")

        assert result["success"] is True
        assert len(result["extracted_entities"]) == 1

    def test_reflect_no_insight_from_plain_text(self, fresh_db):
        """reflect does not extract Insight from plain observations."""
        result = reflect("The code is complex here")

        assert result["success"] is True
        assert len(result["extracted_entities"]) == 0


class TestGetRecentReflections:
    """Tests for get_recent_reflections."""

    def test_get_recent_reflections_empty(self, fresh_db):
        """get_recent_reflections handles empty database."""
        result = get_recent_reflections()

        assert result["success"] is True
        assert result["count"] == 0
        assert result["reflections"] == []

    def test_get_recent_reflections_returns_reflections(self, fresh_db):
        """get_recent_reflections returns stored reflections."""
        # Create some reflections
        reflect("First reflection")
        reflect("Second reflection", trigger="test")

        result = get_recent_reflections()

        assert result["success"] is True
        assert result["count"] >= 2

    def test_get_recent_reflections_by_session(self, fresh_db):
        """get_recent_reflections filters by session."""
        # Create session
        session_open("test-session-filter", goal="Filter test")

        # Create reflection in session
        reflect("Session reflection", session_id="test-session-filter")

        # Create reflection without session
        reflect("General reflection")

        # Query by session
        result = get_recent_reflections(session_id="test-session-filter")

        assert result["success"] is True
        assert result["count"] >= 1
        # All returned should be from this session (content contains "Session")
        for r in result["reflections"]:
            assert "Session" in r["content"]

    def test_get_recent_reflections_respects_limit(self, fresh_db):
        """get_recent_reflections respects limit parameter."""
        # Create several reflections
        for i in range(5):
            reflect(f"Reflection number {i}")

        result = get_recent_reflections(limit=2)

        assert result["success"] is True
        assert result["count"] <= 2
