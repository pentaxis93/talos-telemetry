"""Tests for friction_log MCP tool."""


class TestFrictionLog:
    """Tests for friction_log tool."""

    def test_friction_log_creates_friction(self, fresh_db):
        """Verify friction_log creates Friction entity."""
        from talos_telemetry.mcp.friction import friction_log

        result = friction_log(
            description="Test friction description",
            category="tooling",
        )

        assert result["success"] is True, f"friction_log failed: {result}"
        assert "friction_id" in result
        assert result["is_recurring"] is False
        assert result["recurrence_count"] == 1

        # Verify entity exists in graph
        query_result = fresh_db.execute(f"""
            MATCH (f:Friction {{id: '{result["friction_id"]}'}})
            RETURN f.description, f.category
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] == "Test friction description"
        assert row[1] == "tooling"

    def test_friction_log_stores_embedding(self, fresh_db):
        """Verify friction_log stores embedding."""
        from talos_telemetry.mcp.friction import friction_log

        result = friction_log(
            description="Test friction for embedding",
            category="conceptual",
        )

        assert result["success"] is True

        # Verify embedding exists
        query_result = fresh_db.execute(f"""
            MATCH (f:Friction {{id: '{result["friction_id"]}'}})
            RETURN size(f.embedding)
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] == 768  # all-mpnet-base-v2 dimensions

    def test_friction_log_valid_categories(self, fresh_db):
        """Verify friction_log accepts all valid categories."""
        from talos_telemetry.mcp.friction import friction_log

        valid_categories = ["tooling", "conceptual", "process", "environmental", "relational"]

        for category in valid_categories:
            result = friction_log(
                description=f"Test friction for {category}",
                category=category,
            )
            assert result["success"] is True, f"Failed for category: {category}"

    def test_friction_log_invalid_category(self, fresh_db):
        """Verify friction_log fails for invalid category."""
        from talos_telemetry.mcp.friction import friction_log

        result = friction_log(
            description="Test friction",
            category="invalid_category",
        )

        assert result["success"] is False
        assert "error" in result

    def test_friction_log_with_session(self, fresh_db):
        """Verify friction_log creates PRODUCED_FRICTION relationship."""
        from talos_telemetry.mcp.friction import friction_log
        from talos_telemetry.mcp.session import session_open

        # Create session first
        session_open(session_id="test-friction-session", goal="Test friction")

        result = friction_log(
            description="Test friction with session",
            category="tooling",
            session_id="test-friction-session",
        )

        assert result["success"] is True

        # Verify PRODUCED_FRICTION relationship exists
        query_result = fresh_db.execute(f"""
            MATCH (s:Session {{id: 'test-friction-session'}})-[:PRODUCED_FRICTION]->(f:Friction)
            WHERE f.id = '{result["friction_id"]}'
            RETURN f.id
        """)
        assert query_result.has_next()

    def test_friction_log_blocking(self, fresh_db):
        """Verify friction_log with blocking flag creates BLOCKED_BY relationship."""
        from talos_telemetry.mcp.friction import friction_log
        from talos_telemetry.mcp.session import session_open

        session_open(session_id="test-blocking-session", goal="Test blocking")

        result = friction_log(
            description="Blocking friction",
            category="process",
            session_id="test-blocking-session",
            blocking=True,
        )

        assert result["success"] is True

        # Verify SESSION_BLOCKED_BY relationship exists
        query_result = fresh_db.execute(f"""
            MATCH (s:Session {{id: 'test-blocking-session'}})-[:SESSION_BLOCKED_BY]->(f:Friction)
            WHERE f.id = '{result["friction_id"]}'
            RETURN f.id
        """)
        assert query_result.has_next()

    def test_friction_log_recurring_detection(self, fresh_db):
        """Verify friction_log detects and increments recurring frictions."""
        from talos_telemetry.mcp.friction import friction_log

        # Log first friction
        result1 = friction_log(
            description="Read tool truncates files at 2000 lines",
            category="tooling",
        )
        assert result1["success"] is True
        assert result1["is_recurring"] is False
        assert result1["recurrence_count"] == 1

        # Log same friction - should increment
        # Using same description to ensure matching
        result2 = friction_log(
            description="Read tool truncates files at 2000 lines",
            category="tooling",
        )
        assert result2["success"] is True
        assert result2["is_recurring"] is True
        assert result2["recurrence_count"] == 2
        # Should return same friction_id
        assert result2["friction_id"] == result1["friction_id"]

    def test_friction_log_handles_special_characters(self, fresh_db):
        """Verify friction_log properly escapes special characters."""
        from talos_telemetry.mcp.friction import friction_log

        result = friction_log(
            description="Friction with 'quotes' and \"doubles\" and\nnewlines",
            category="tooling",
        )

        assert result["success"] is True, f"friction_log failed: {result}"

    def test_friction_log_sets_timestamp(self, fresh_db):
        """Verify friction_log sets occurred_at timestamp."""
        from talos_telemetry.mcp.friction import friction_log

        result = friction_log(
            description="Test friction for timestamp",
            category="environmental",
        )

        assert result["success"] is True

        # Verify timestamp is set
        query_result = fresh_db.execute(f"""
            MATCH (f:Friction {{id: '{result["friction_id"]}'}})
            RETURN f.occurred_at
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] is not None
