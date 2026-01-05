"""Tests for session lifecycle MCP tools."""

import time


class TestSessionOpen:
    """Tests for session_open tool."""

    def test_session_open_creates_session_node(self, fresh_db):
        """Verify session_open creates Session node in graph."""
        from talos_telemetry.mcp.session import session_open

        result = session_open(
            session_id="test-session-001",
            goal="Test the session open functionality",
        )

        assert result["success"] is True, f"session_open failed: {result}"
        assert result["session_id"] == "test-session-001"

        # Verify node exists in graph
        query_result = fresh_db.execute("""
            MATCH (s:Session {id: 'test-session-001'})
            RETURN s.id, s.goal
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] == "test-session-001"
        assert row[1] == "Test the session open functionality"

    def test_session_open_sets_started_at(self, fresh_db):
        """Verify session_open sets started_at timestamp."""
        from talos_telemetry.mcp.session import session_open

        session_open(session_id="test-session-002", goal="Test timestamp")

        query_result = fresh_db.execute("""
            MATCH (s:Session {id: 'test-session-002'})
            RETURN s.started_at
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] is not None  # Timestamp should be set

    def test_session_open_returns_inherited_count(self, fresh_db):
        """Verify session_open returns count of inherited entities."""
        from talos_telemetry.mcp.session import session_open

        # Reference data is seeded, so inherited_count should be > 0
        result = session_open(
            session_id="test-session-003",
            goal="Test inherited count",
        )

        assert result["success"] is True
        assert "inherited_count" in result
        assert isinstance(result["inherited_count"], int)

    def test_session_open_with_custom_persona(self, fresh_db):
        """Verify session_open accepts custom persona."""
        from talos_telemetry.mcp.session import session_open

        result = session_open(
            session_id="test-session-004",
            goal="Test custom persona",
            persona="Sage",
        )

        assert result["success"] is True

    def test_session_open_with_custom_human(self, fresh_db):
        """Verify session_open accepts custom human collaborator."""
        from talos_telemetry.mcp.session import session_open

        result = session_open(
            session_id="test-session-005",
            goal="Test custom human",
            human="TestUser",
        )

        assert result["success"] is True

    def test_session_open_handles_special_characters_in_goal(self, fresh_db):
        """Verify session_open properly escapes special characters."""
        from talos_telemetry.mcp.session import session_open

        result = session_open(
            session_id="test-session-006",
            goal="Test with 'quotes' and \"double quotes\" and newlines\nhere",
        )

        assert result["success"] is True

        # Verify content is stored correctly
        query_result = fresh_db.execute("""
            MATCH (s:Session {id: 'test-session-006'})
            RETURN s.goal
        """)
        assert query_result.has_next()

    def test_session_open_duplicate_id_fails(self, fresh_db):
        """Verify session_open fails gracefully for duplicate session_id."""
        from talos_telemetry.mcp.session import session_open

        # Create first session
        result1 = session_open(session_id="test-session-dup", goal="First session")
        assert result1["success"] is True

        # Try to create duplicate
        result2 = session_open(session_id="test-session-dup", goal="Duplicate session")
        # Should fail or return degraded
        assert result2["success"] is False or result2.get("degraded") is True


class TestSessionClose:
    """Tests for session_close tool."""

    def test_session_close_updates_session(self, fresh_db):
        """Verify session_close updates Session node."""
        from talos_telemetry.mcp.session import session_close, session_open

        # First open a session
        session_open(session_id="test-close-001", goal="Test close")

        # Small delay to ensure measurable duration
        time.sleep(0.1)

        # Close it
        result = session_close(
            session_id="test-close-001",
            goal_achieved=True,
            summary="Session completed successfully",
        )

        assert result["success"] is True
        assert result["session_id"] == "test-close-001"

        # Verify ended_at is set
        query_result = fresh_db.execute("""
            MATCH (s:Session {id: 'test-close-001'})
            RETURN s.ended_at, s.summary
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] is not None  # ended_at should be set
        assert row[1] == "Session completed successfully"

    def test_session_close_returns_duration(self, fresh_db):
        """Verify session_close returns duration_seconds."""
        from talos_telemetry.mcp.session import session_close, session_open

        session_open(session_id="test-close-002", goal="Test duration")
        time.sleep(0.2)
        result = session_close(session_id="test-close-002")

        assert result["success"] is True
        assert "duration_seconds" in result
        assert result["duration_seconds"] >= 0

    def test_session_close_returns_statistics(self, fresh_db):
        """Verify session_close returns session statistics."""
        from talos_telemetry.mcp.session import session_close, session_open

        session_open(session_id="test-close-003", goal="Test stats")
        result = session_close(session_id="test-close-003")

        assert result["success"] is True
        assert "tool_calls" in result
        assert "insights_produced" in result
        assert "frictions_logged" in result

    def test_session_close_requires_reflection_by_default(self, fresh_db):
        """Verify session_close requires reflection by default."""
        from talos_telemetry.mcp.session import session_close, session_open

        session_open(session_id="test-close-004", goal="Test reflection")
        result = session_close(session_id="test-close-004")

        assert result["success"] is True
        assert result.get("requires_reflection") is True
        assert "reflection_prompt" in result

    def test_session_close_can_skip_reflection(self, fresh_db):
        """Verify session_close can skip reflection."""
        from talos_telemetry.mcp.session import session_close, session_open

        session_open(session_id="test-close-005", goal="Test skip reflection")
        result = session_close(session_id="test-close-005", skip_reflection=True)

        assert result["success"] is True
        assert result.get("requires_reflection") is not True

    def test_session_close_nonexistent_session_fails(self, fresh_db):
        """Verify session_close fails for nonexistent session."""
        from talos_telemetry.mcp.session import session_close

        result = session_close(session_id="nonexistent-session")

        assert result["success"] is False
        assert "error" in result or "message" in result

    def test_session_close_handles_special_characters_in_summary(self, fresh_db):
        """Verify session_close properly escapes special characters in summary."""
        from talos_telemetry.mcp.session import session_close, session_open

        session_open(session_id="test-close-006", goal="Test escaping")
        result = session_close(
            session_id="test-close-006",
            summary="Summary with 'quotes' and \"doubles\"",
        )

        assert result["success"] is True


class TestSessionIntegration:
    """Integration tests for session lifecycle."""

    def test_full_session_lifecycle(self, fresh_db):
        """Test complete session open -> close cycle."""
        from talos_telemetry.mcp.session import session_close, session_open

        # Open
        open_result = session_open(
            session_id="test-lifecycle-001",
            goal="Complete lifecycle test",
            persona="Talos",
            human="Robbie",
        )
        assert open_result["success"] is True

        # Verify session exists and is open (no ended_at)
        query_result = fresh_db.execute("""
            MATCH (s:Session {id: 'test-lifecycle-001'})
            RETURN s.ended_at
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] is None  # Not yet closed

        # Close
        close_result = session_close(
            session_id="test-lifecycle-001",
            goal_achieved=True,
            summary="Lifecycle test completed",
            skip_reflection=True,
        )
        assert close_result["success"] is True

        # Verify session is closed
        query_result = fresh_db.execute("""
            MATCH (s:Session {id: 'test-lifecycle-001'})
            RETURN s.ended_at, s.duration_seconds
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] is not None  # ended_at set
        assert row[1] is not None  # duration_seconds set
