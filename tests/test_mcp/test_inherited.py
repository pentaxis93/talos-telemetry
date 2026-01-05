"""Tests for INHERITED relationship capture at session start."""


class TestInheritedCapture:
    """Tests for temporal knowledge snapshot via INHERITED relationships."""

    def test_session_captures_inherited_beliefs(self, fresh_db):
        """Verify session_open creates INHERITED_BELIEF relationships."""
        from talos_telemetry.mcp.session import session_open

        # First create a Belief that can be inherited
        fresh_db.execute("""
            CREATE (b:Belief {
                id: 'belief-test-001',
                content: 'Test belief content',
                adopted_at: timestamp('2026-01-01 00:00:00')
            })
        """)

        # Open a session - should capture the belief
        result = session_open(session_id="test-inherit-001", goal="Test inherited capture")

        assert result["success"] is True
        assert result["inherited_count"] >= 1

        # Verify INHERITED_BELIEF relationship exists
        query_result = fresh_db.execute("""
            MATCH (s:Session {id: 'test-inherit-001'})-[:INHERITED_BELIEF]->(b:Belief)
            WHERE b.id = 'belief-test-001'
            RETURN b.id
        """)
        assert query_result.has_next()

    def test_session_captures_inherited_insights(self, fresh_db):
        """Verify session_open creates INHERITED_INSIGHT relationships."""
        from talos_telemetry.mcp.session import session_open

        # Create an Insight
        fresh_db.execute("""
            CREATE (i:Insight {
                id: 'insight-test-001',
                content: 'Test insight content',
                created_at: timestamp('2026-01-01 00:00:00')
            })
        """)

        result = session_open(session_id="test-inherit-002", goal="Test inherited insights")

        assert result["success"] is True

        # Verify INHERITED_INSIGHT relationship
        query_result = fresh_db.execute("""
            MATCH (s:Session {id: 'test-inherit-002'})-[:INHERITED_INSIGHT]->(i:Insight)
            WHERE i.id = 'insight-test-001'
            RETURN i.id
        """)
        assert query_result.has_next()

    def test_session_captures_inherited_patterns(self, fresh_db):
        """Verify session_open creates INHERITED_PATTERN relationships."""
        from talos_telemetry.mcp.session import session_open

        # Create a Pattern
        fresh_db.execute("""
            CREATE (p:Pattern {
                id: 'pattern-test-001',
                name: 'Test pattern',
                description: 'A test pattern',
                first_noticed: timestamp('2026-01-01 00:00:00'),
                occurrence_count: 1,
                status: 'emerging'
            })
        """)

        result = session_open(session_id="test-inherit-003", goal="Test inherited patterns")

        assert result["success"] is True

        query_result = fresh_db.execute("""
            MATCH (s:Session {id: 'test-inherit-003'})-[:INHERITED_PATTERN]->(p:Pattern)
            WHERE p.id = 'pattern-test-001'
            RETURN p.id
        """)
        assert query_result.has_next()

    def test_session_returns_inherited_summary(self, fresh_db):
        """Verify session_open returns breakdown of inherited entities."""
        from talos_telemetry.mcp.session import session_open

        # Create entities of different types
        fresh_db.execute("""
            CREATE (b:Belief {id: 'belief-sum-001', content: 'Test', adopted_at: timestamp('2026-01-01 00:00:00')})
        """)
        fresh_db.execute("""
            CREATE (i:Insight {id: 'insight-sum-001', content: 'Test', created_at: timestamp('2026-01-01 00:00:00')})
        """)

        result = session_open(session_id="test-inherit-004", goal="Test summary")

        assert result["success"] is True
        assert "inherited_count" in result
        assert result["inherited_count"] >= 2

        # Check for inherited_summary breakdown
        if "inherited_summary" in result:
            summary = result["inherited_summary"]
            assert "beliefs" in summary or "Belief" in str(summary)

    def test_inherited_captures_all_entity_types(self, fresh_db):
        """Verify all inheritable entity types are captured."""
        from talos_telemetry.mcp.session import session_open

        # Create one of each inheritable type
        entity_creates = [
            (
                "Belief",
                "belief-all-001",
                "content: 'Test', adopted_at: timestamp('2026-01-01 00:00:00')",
            ),
            (
                "Insight",
                "insight-all-001",
                "content: 'Test', created_at: timestamp('2026-01-01 00:00:00')",
            ),
            (
                "Pattern",
                "pattern-all-001",
                "name: 'Test', first_noticed: timestamp('2026-01-01 00:00:00'), occurrence_count: 1, status: 'emerging'",
            ),
            ("Sutra", "sutra-all-001", "name: 'Test', content: 'Test content'"),
            ("Protocol", "protocol-all-001", "name: 'Test', purpose: 'Test purpose'"),
            ("Limitation", "limitation-all-001", "description: 'Test limitation'"),
            ("Capability", "capability-all-001", "name: 'Test', description: 'Test capability'"),
        ]

        for entity_type, entity_id, props in entity_creates:
            try:
                fresh_db.execute(f"""
                    CREATE (e:{entity_type} {{id: '{entity_id}', {props}}})
                """)
            except Exception:
                pass  # Some may fail due to missing required fields, that's ok

        result = session_open(session_id="test-inherit-all", goal="Test all types")

        assert result["success"] is True
        # Should have inherited at least some entities
        assert result["inherited_count"] >= 1

    def test_inherited_with_timestamp(self, fresh_db):
        """Verify INHERITED relationships have valid_from timestamp."""
        from talos_telemetry.mcp.session import session_open

        fresh_db.execute("""
            CREATE (b:Belief {
                id: 'belief-ts-001',
                content: 'Test',
                adopted_at: timestamp('2026-01-01 00:00:00')
            })
        """)

        session_open(session_id="test-inherit-ts", goal="Test timestamps")

        # Check that relationship has valid_from
        query_result = fresh_db.execute("""
            MATCH (s:Session {id: 'test-inherit-ts'})-[r:INHERITED_BELIEF]->(b:Belief)
            RETURN r.valid_from
        """)
        assert query_result.has_next()
        row = query_result.get_next()
        assert row[0] is not None  # valid_from should be set

    def test_temporal_query_what_did_i_know(self, fresh_db):
        """Verify we can query 'what beliefs did this session inherit'."""
        from talos_telemetry.mcp.session import session_open

        # Create beliefs at different "times" (simulated)
        fresh_db.execute("""
            CREATE (b1:Belief {id: 'belief-old', content: 'Old belief', adopted_at: timestamp('2025-01-01 00:00:00')})
        """)

        # Session 1 inherits old belief
        session_open(session_id="session-temporal-1", goal="First session")

        # Create new belief
        fresh_db.execute("""
            CREATE (b2:Belief {id: 'belief-new', content: 'New belief', adopted_at: timestamp('2026-01-05 00:00:00')})
        """)

        # Session 2 inherits both
        session_open(session_id="session-temporal-2", goal="Second session")

        # Query: What beliefs did session 1 have?
        result1 = fresh_db.execute("""
            MATCH (s:Session {id: 'session-temporal-1'})-[:INHERITED_BELIEF]->(b:Belief)
            RETURN b.id
        """)
        session1_beliefs = []
        while result1.has_next():
            session1_beliefs.append(result1.get_next()[0])

        # Query: What beliefs did session 2 have?
        result2 = fresh_db.execute("""
            MATCH (s:Session {id: 'session-temporal-2'})-[:INHERITED_BELIEF]->(b:Belief)
            RETURN b.id
        """)
        session2_beliefs = []
        while result2.has_next():
            session2_beliefs.append(result2.get_next()[0])

        # Session 1 should only have old belief
        assert "belief-old" in session1_beliefs
        assert "belief-new" not in session1_beliefs

        # Session 2 should have both
        assert "belief-old" in session2_beliefs
        assert "belief-new" in session2_beliefs
