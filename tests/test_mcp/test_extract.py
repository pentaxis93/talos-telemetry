"""Tests for journal_extract MCP tool."""

from unittest.mock import MagicMock, patch

from talos_telemetry.db.connection import get_connection
from talos_telemetry.mcp.extract import journal_extract
from talos_telemetry.mcp.session import session_open


class TestJournalExtract:
    """Tests for journal_extract MCP tool."""

    @patch("talos_telemetry.extraction.extractor.extract_entities")
    def test_extract_stores_insight(self, mock_extract, fresh_db):
        """Extract and store an insight from text."""
        # Mock extraction result
        mock_entity = MagicMock()
        mock_entity.entity_type = "Insight"
        mock_entity.content = "Context windows are the fundamental constraint"
        mock_entity.confidence = 0.92
        mock_entity.domain = "AI"

        mock_result = MagicMock()
        mock_result.entities = [mock_entity]
        mock_result.relationships = []
        mock_extract.return_value = mock_result

        result = journal_extract(
            "I realized context windows are the fundamental constraint for AI agents."
        )

        assert result["success"] is True
        assert len(result["stored_entities"]) == 1
        assert result["stored_entities"][0]["type"] == "Insight"
        assert "context windows" in result["stored_entities"][0]["content"].lower()

        # Verify stored in graph
        conn = get_connection()
        query_result = conn.execute(
            f"MATCH (i:Insight {{id: '{result['stored_entities'][0]['id']}'}}) RETURN i.content"
        )
        assert query_result.has_next()

    @patch("talos_telemetry.extraction.extractor.extract_entities")
    def test_extract_stores_friction(self, mock_extract, fresh_db):
        """Extract and store a friction from text."""
        mock_entity = MagicMock()
        mock_entity.entity_type = "Friction"
        mock_entity.content = "Database connections not releasing"
        mock_entity.confidence = 0.95
        mock_entity.domain = "programming"

        mock_result = MagicMock()
        mock_result.entities = [mock_entity]
        mock_result.relationships = []
        mock_extract.return_value = mock_result

        result = journal_extract("Database connections weren't releasing properly.")

        assert result["success"] is True
        assert result["stored_entities"][0]["type"] == "Friction"

        # Verify stored in graph
        conn = get_connection()
        query_result = conn.execute(
            f"MATCH (f:Friction {{id: '{result['stored_entities'][0]['id']}'}}) RETURN f.description"
        )
        assert query_result.has_next()

    @patch("talos_telemetry.extraction.extractor.extract_entities")
    def test_extract_multiple_entities(self, mock_extract, fresh_db):
        """Extract multiple entities from text."""
        mock_friction = MagicMock()
        mock_friction.entity_type = "Friction"
        mock_friction.content = "Timestamp function failed"
        mock_friction.confidence = 0.9
        mock_friction.domain = None

        mock_insight = MagicMock()
        mock_insight.entity_type = "Insight"
        mock_insight.content = "Kuzu requires string argument for timestamp"
        mock_insight.confidence = 0.85
        mock_insight.domain = "database"

        mock_result = MagicMock()
        mock_result.entities = [mock_friction, mock_insight]
        mock_result.relationships = []
        mock_extract.return_value = mock_result

        result = journal_extract("Timestamp failed. Kuzu needs string arg for timestamp().")

        assert result["success"] is True
        assert len(result["stored_entities"]) == 2
        assert result["extraction_count"] == 2

    @patch("talos_telemetry.extraction.extractor.extract_entities")
    def test_extract_with_session(self, mock_extract, fresh_db):
        """Extract entities linked to session."""
        # Create session first
        session_result = session_open("test-session-extract", goal="Test extraction")
        assert session_result["success"] is True

        mock_entity = MagicMock()
        mock_entity.entity_type = "Insight"
        mock_entity.content = "Test insight content"
        mock_entity.confidence = 0.9
        mock_entity.domain = None

        mock_result = MagicMock()
        mock_result.entities = [mock_entity]
        mock_result.relationships = []
        mock_extract.return_value = mock_result

        result = journal_extract("Test insight content", session_id="test-session-extract")

        assert result["success"] is True

        # Verify PRODUCED relationship exists
        conn = get_connection()
        entity_id = result["stored_entities"][0]["id"]
        rel_result = conn.execute(f"""
            MATCH (s:Session {{id: 'test-session-extract'}})-[r:PRODUCED_INSIGHT]->(i:Insight {{id: '{entity_id}'}})
            RETURN r
        """)
        assert rel_result.has_next()

    @patch("talos_telemetry.extraction.extractor.extract_entities")
    def test_extract_with_relationship(self, mock_extract, fresh_db):
        """Extract entities with LED_TO relationship."""
        mock_friction = MagicMock()
        mock_friction.entity_type = "Friction"
        mock_friction.content = "API timeout"
        mock_friction.confidence = 0.95
        mock_friction.domain = None

        mock_insight = MagicMock()
        mock_insight.entity_type = "Insight"
        mock_insight.content = "Need retry logic"
        mock_insight.confidence = 0.85
        mock_insight.domain = None

        mock_result = MagicMock()
        mock_result.entities = [mock_friction, mock_insight]
        mock_result.relationships = [
            {"from_index": 0, "to_index": 1, "relationship_type": "LED_TO"}
        ]
        mock_extract.return_value = mock_result

        result = journal_extract("API timeout. Led me to realize we need retry logic.")

        assert result["success"] is True
        assert len(result["stored_entities"]) == 2
        assert len(result["stored_relationships"]) == 1
        assert result["stored_relationships"][0]["type"] == "FRICTION_LED_TO_INSIGHT"

    @patch("talos_telemetry.extraction.extractor.extract_entities")
    def test_extract_empty_result(self, mock_extract, fresh_db):
        """Handle extraction returning no entities."""
        mock_result = MagicMock()
        mock_result.entities = []
        mock_result.relationships = []
        mock_extract.return_value = mock_result

        result = journal_extract("Hello world")

        assert result["success"] is True
        assert result["stored_entities"] == []
        assert "No entities extracted" in result["message"]

    @patch("talos_telemetry.extraction.extractor.extract_entities")
    def test_extract_stores_belief(self, mock_extract, fresh_db):
        """Extract and store a belief."""
        mock_entity = MagicMock()
        mock_entity.entity_type = "Belief"
        mock_entity.content = "Testing is essential for quality"
        mock_entity.confidence = 0.88
        mock_entity.domain = "engineering"

        mock_result = MagicMock()
        mock_result.entities = [mock_entity]
        mock_result.relationships = []
        mock_extract.return_value = mock_result

        result = journal_extract("I believe testing is essential for quality software.")

        assert result["success"] is True
        assert result["stored_entities"][0]["type"] == "Belief"

        # Verify stored
        conn = get_connection()
        query_result = conn.execute(
            f"MATCH (b:Belief {{id: '{result['stored_entities'][0]['id']}'}}) RETURN b.content"
        )
        assert query_result.has_next()

    @patch("talos_telemetry.extraction.extractor.extract_entities")
    def test_extract_stores_pattern(self, mock_extract, fresh_db):
        """Extract and store a pattern."""
        mock_entity = MagicMock()
        mock_entity.entity_type = "Pattern"
        mock_entity.content = "I tend to over-engineer solutions"
        mock_entity.confidence = 0.75
        mock_entity.domain = "behavior"

        mock_result = MagicMock()
        mock_result.entities = [mock_entity]
        mock_result.relationships = []
        mock_extract.return_value = mock_result

        result = journal_extract("I notice I keep over-engineering solutions.")

        assert result["success"] is True
        assert result["stored_entities"][0]["type"] == "Pattern"

        # Verify stored
        conn = get_connection()
        query_result = conn.execute(
            f"MATCH (p:Pattern {{id: '{result['stored_entities'][0]['id']}'}}) RETURN p.description"
        )
        assert query_result.has_next()
