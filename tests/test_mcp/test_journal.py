"""Tests for journal MCP tools."""


class TestJournalWrite:
    """Tests for journal_write tool."""

    def test_journal_write_creates_insight(self, fresh_db):
        """Verify journal_write creates Insight entity for insight category."""
        from talos_telemetry.mcp.journal import journal_write

        result = journal_write(
            content="Test insight content",
            category="insight",
        )

        assert result["success"] is True, f"journal_write failed: {result}"
        assert "entry_id" in result
        assert result["entity_type"] == "Insight"

        # Verify entity exists in graph
        query_result = fresh_db.execute(f"""
            MATCH (i:Insight {{id: '{result["entry_id"]}'}})
            RETURN i.content
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] == "Test insight content"

    def test_journal_write_creates_observation(self, fresh_db):
        """Verify journal_write creates Observation entity for observation category."""
        from talos_telemetry.mcp.journal import journal_write

        result = journal_write(
            content="Test observation content",
            category="observation",
        )

        assert result["success"] is True, f"journal_write failed: {result}"
        assert result["entity_type"] == "Observation"

        # Verify entity exists
        query_result = fresh_db.execute(f"""
            MATCH (o:Observation {{id: '{result["entry_id"]}'}})
            RETURN o.content
        """)
        assert query_result.has_next()

    def test_journal_write_creates_reflection(self, fresh_db):
        """Verify journal_write creates Reflection entity for reflection category."""
        from talos_telemetry.mcp.journal import journal_write

        result = journal_write(
            content="Test reflection content",
            category="reflection",
        )

        assert result["success"] is True, f"journal_write failed: {result}"
        assert result["entity_type"] == "Reflection"

    def test_journal_write_creates_decision(self, fresh_db):
        """Verify journal_write creates Decision entity for decision category."""
        from talos_telemetry.mcp.journal import journal_write

        result = journal_write(
            content="Test decision content",
            category="decision",
        )

        assert result["success"] is True, f"journal_write failed: {result}"
        assert result["entity_type"] == "Decision"

    def test_journal_write_creates_experience(self, fresh_db):
        """Verify journal_write creates Experience entity for experience category."""
        from talos_telemetry.mcp.journal import journal_write

        result = journal_write(
            content="Test experience content",
            category="experience",
        )

        assert result["success"] is True, f"journal_write failed: {result}"
        assert result["entity_type"] == "Experience"

    def test_journal_write_with_session(self, fresh_db):
        """Verify journal_write creates PRODUCED_INSIGHT relationship when session provided."""
        from talos_telemetry.mcp.journal import journal_write
        from talos_telemetry.mcp.session import session_open

        # Create session first
        session_open(session_id="test-journal-session", goal="Test journal")

        result = journal_write(
            content="Test insight with session",
            category="insight",
            session_id="test-journal-session",
        )

        assert result["success"] is True

        # Verify PRODUCED_INSIGHT relationship exists
        query_result = fresh_db.execute(f"""
            MATCH (s:Session {{id: 'test-journal-session'}})-[:PRODUCED_INSIGHT]->(i:Insight)
            WHERE i.id = '{result["entry_id"]}'
            RETURN i.id
        """)
        assert query_result.has_next()

    def test_journal_write_with_domain(self, fresh_db):
        """Verify journal_write sets domain property."""
        from talos_telemetry.mcp.journal import journal_write

        result = journal_write(
            content="Test insight with domain",
            category="insight",
            domain="technical",
        )

        assert result["success"] is True

        # Verify domain is set
        query_result = fresh_db.execute(f"""
            MATCH (i:Insight {{id: '{result["entry_id"]}'}})
            RETURN i.domain
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] == "technical"

    def test_journal_write_with_confidence(self, fresh_db):
        """Verify journal_write sets confidence for insights."""
        from talos_telemetry.mcp.journal import journal_write

        result = journal_write(
            content="Test insight with confidence",
            category="insight",
            confidence=0.85,
        )

        assert result["success"] is True

        # Verify confidence is set
        query_result = fresh_db.execute(f"""
            MATCH (i:Insight {{id: '{result["entry_id"]}'}})
            RETURN i.confidence
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] == 0.85

    def test_journal_write_invalid_category(self, fresh_db):
        """Verify journal_write fails for invalid category."""
        from talos_telemetry.mcp.journal import journal_write

        result = journal_write(
            content="Test content",
            category="invalid_category",
        )

        assert result["success"] is False
        assert "error" in result

    def test_journal_write_stores_embedding(self, fresh_db):
        """Verify journal_write generates and stores embedding."""
        from talos_telemetry.mcp.journal import journal_write

        result = journal_write(
            content="Test insight for embedding",
            category="insight",
        )

        assert result["success"] is True

        # Verify embedding exists and has correct dimensions
        query_result = fresh_db.execute(f"""
            MATCH (i:Insight {{id: '{result["entry_id"]}'}})
            RETURN size(i.embedding)
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] == 768  # all-mpnet-base-v2 dimensions

    def test_journal_write_handles_special_characters(self, fresh_db):
        """Verify journal_write properly escapes special characters."""
        from talos_telemetry.mcp.journal import journal_write

        result = journal_write(
            content="Test with 'quotes' and \"doubles\" and\nnewlines",
            category="insight",
        )

        assert result["success"] is True, f"journal_write failed: {result}"


class TestJournalQuery:
    """Tests for journal_query tool."""

    def test_journal_query_returns_results(self, fresh_db):
        """Verify journal_query returns results structure."""
        from talos_telemetry.mcp.journal import journal_query, journal_write

        # Create some insights first
        journal_write(content="Machine learning is about pattern recognition", category="insight")
        journal_write(content="Deep learning uses neural networks", category="insight")

        result = journal_query(query="machine learning patterns")

        assert result["success"] is True
        assert "results" in result
        assert "total_found" in result

    def test_journal_query_filters_by_entity_type(self, fresh_db):
        """Verify journal_query respects entity_types filter."""
        from talos_telemetry.mcp.journal import journal_query, journal_write

        # Create insight and observation
        journal_write(content="This is an insight about testing", category="insight")
        journal_write(content="This is an observation about testing", category="observation")

        result = journal_query(
            query="testing",
            entity_types=["Insight"],
        )

        assert result["success"] is True
        # Should only return insights
        for r in result.get("results", []):
            assert r["entity_type"] == "Insight"

    def test_journal_query_respects_limit(self, fresh_db):
        """Verify journal_query respects limit parameter."""
        from talos_telemetry.mcp.journal import journal_query, journal_write

        # Create multiple insights
        for i in range(5):
            journal_write(content=f"Test insight number {i} about software", category="insight")

        result = journal_query(query="software", limit=3)

        assert result["success"] is True
        assert len(result.get("results", [])) <= 3

    def test_journal_query_empty_results(self, fresh_db):
        """Verify journal_query handles no matches gracefully."""
        from talos_telemetry.mcp.journal import journal_query

        result = journal_query(query="xyznonexistentquery123")

        assert result["success"] is True
        assert result["total_found"] == 0
