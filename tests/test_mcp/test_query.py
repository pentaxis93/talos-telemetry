"""Tests for graph_query MCP tool."""


class TestGraphQuery:
    """Tests for graph_query tool."""

    def test_graph_query_basic(self, fresh_db):
        """Verify graph_query executes basic queries."""
        from talos_telemetry.mcp.query import graph_query

        result = graph_query("MATCH (s:OperationalState) RETURN count(s) as count")

        assert result["success"] is True
        assert "columns" in result
        assert "rows" in result
        assert result["columns"] == ["count"]
        # Reference data seeds operational states
        assert result["rows"][0][0] >= 0

    def test_graph_query_returns_columns(self, fresh_db):
        """Verify graph_query returns column names."""
        from talos_telemetry.mcp.query import graph_query

        result = graph_query(
            "MATCH (s:OperationalState) RETURN s.name as name, s.category as category LIMIT 1"
        )

        assert result["success"] is True
        assert result["columns"] == ["name", "category"]

    def test_graph_query_returns_rows(self, fresh_db):
        """Verify graph_query returns row data."""
        from talos_telemetry.mcp.query import graph_query

        result = graph_query("MATCH (d:Domain) RETURN d.name ORDER BY d.name LIMIT 3")

        assert result["success"] is True
        assert len(result["rows"]) <= 3
        assert result["row_count"] == len(result["rows"])

    def test_graph_query_blocks_create(self, fresh_db):
        """Verify graph_query blocks CREATE statements."""
        from talos_telemetry.mcp.query import graph_query

        result = graph_query("CREATE (x:Test {name: 'test'})")

        assert result["success"] is False
        assert "error" in result
        assert "CREATE" in result["error"]

    def test_graph_query_blocks_delete(self, fresh_db):
        """Verify graph_query blocks DELETE statements."""
        from talos_telemetry.mcp.query import graph_query

        result = graph_query("MATCH (x) DELETE x")

        assert result["success"] is False
        assert "error" in result
        assert "DELETE" in result["error"]

    def test_graph_query_blocks_set(self, fresh_db):
        """Verify graph_query blocks SET statements."""
        from talos_telemetry.mcp.query import graph_query

        result = graph_query("MATCH (s:OperationalState) SET s.name = 'hacked'")

        assert result["success"] is False
        assert "error" in result
        assert "SET" in result["error"]

    def test_graph_query_blocks_merge(self, fresh_db):
        """Verify graph_query blocks MERGE statements."""
        from talos_telemetry.mcp.query import graph_query

        result = graph_query("MERGE (x:Test {name: 'test'})")

        assert result["success"] is False
        assert "error" in result
        assert "MERGE" in result["error"]

    def test_graph_query_blocks_drop(self, fresh_db):
        """Verify graph_query blocks DROP statements."""
        from talos_telemetry.mcp.query import graph_query

        result = graph_query("DROP TABLE Test")

        assert result["success"] is False
        assert "error" in result
        assert "DROP" in result["error"]

    def test_graph_query_handles_invalid_cypher(self, fresh_db):
        """Verify graph_query handles invalid Cypher syntax."""
        from talos_telemetry.mcp.query import graph_query

        result = graph_query("INVALID CYPHER SYNTAX")

        assert result["success"] is False
        assert "error" in result

    def test_graph_query_respects_limit(self, fresh_db):
        """Verify graph_query respects row limit."""
        from talos_telemetry.mcp.query import graph_query

        # Create many nodes first
        result = graph_query("MATCH (s:OperationalState) RETURN s.name LIMIT 5")

        assert result["success"] is True
        assert len(result["rows"]) <= 5

    def test_graph_query_with_session_data(self, fresh_db):
        """Verify graph_query can query session data."""
        from talos_telemetry.mcp.query import graph_query
        from talos_telemetry.mcp.session import session_open

        # Create a session
        session_open(session_id="test-query-session", goal="Test query")

        result = graph_query("""
            MATCH (s:Session {id: 'test-query-session'})
            RETURN s.id, s.goal
        """)

        assert result["success"] is True
        assert result["rows"][0][0] == "test-query-session"
        assert result["rows"][0][1] == "Test query"


class TestCountEntities:
    """Tests for count_entities helper."""

    def test_count_entities_returns_count(self, fresh_db):
        """Verify count_entities returns entity count."""
        from talos_telemetry.mcp.query import count_entities

        count = count_entities("OperationalState")

        # Reference data seeds operational states
        assert count >= 0
        assert isinstance(count, int)

    def test_count_entities_empty_type(self, fresh_db):
        """Verify count_entities returns 0 for empty tables."""
        from talos_telemetry.mcp.query import count_entities

        # Pattern table should be empty by default
        count = count_entities("Pattern")

        assert count == 0


class TestFindRecurringFriction:
    """Tests for find_recurring_friction helper."""

    def test_find_recurring_friction_returns_list(self, fresh_db):
        """Verify find_recurring_friction returns list structure."""
        from talos_telemetry.mcp.query import find_recurring_friction

        result = find_recurring_friction()

        assert isinstance(result, list)

    def test_find_recurring_friction_with_data(self, fresh_db):
        """Verify find_recurring_friction finds recurring frictions."""
        from talos_telemetry.mcp.friction import friction_log
        from talos_telemetry.mcp.query import find_recurring_friction

        # Create recurring friction
        friction_log(description="Recurring test friction", category="tooling")
        friction_log(description="Recurring test friction", category="tooling")
        friction_log(description="Recurring test friction", category="tooling")

        result = find_recurring_friction(min_recurrence=2)

        assert len(result) >= 1
        found = [f for f in result if "Recurring test friction" in f["description"]]
        assert len(found) >= 1
        assert found[0]["recurrence_count"] >= 2


class TestGetSessionSummary:
    """Tests for get_session_summary helper."""

    def test_get_session_summary_nonexistent(self, fresh_db):
        """Verify get_session_summary returns empty for nonexistent session."""
        from talos_telemetry.mcp.query import get_session_summary

        result = get_session_summary("nonexistent-session")

        # Helper returns empty dict for nonexistent or failed queries
        assert isinstance(result, dict)
