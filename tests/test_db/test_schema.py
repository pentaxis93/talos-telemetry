"""Tests for Kuzu schema deployment."""


class TestSchemaDeployment:
    """Tests verifying schema is deployed correctly."""

    def test_all_node_tables_exist(self, fresh_db):
        """Verify all 20 node tables are created."""
        expected_tables = {
            "Session",
            "Insight",
            "Observation",
            "Pattern",
            "Belief",
            "Decision",
            "Experience",
            "OperationalState",
            "Friction",
            "Tool",
            "Question",
            "Sutra",
            "Human",
            "Goal",
            "Capability",
            "Limitation",
            "Persona",
            "Protocol",
            "Domain",
            "Reflection",
        }

        result = fresh_db.execute("CALL show_tables() RETURN *")
        found_nodes = set()

        while result.has_next():
            row = result.get_next()
            table_name = row[1]
            table_type = row[2]
            if table_type == "NODE":
                found_nodes.add(table_name)

        missing = expected_tables - found_nodes
        assert not missing, f"Missing node tables: {missing}"
        assert len(found_nodes) >= 20, f"Expected at least 20 node tables, found {len(found_nodes)}"

    def test_relationship_tables_exist(self, fresh_db):
        """Verify relationship tables are created."""
        result = fresh_db.execute("CALL show_tables() RETURN *")
        rel_count = 0

        while result.has_next():
            row = result.get_next()
            if row[2] == "REL":
                rel_count += 1

        # We expect at least 50 relationship tables
        assert rel_count >= 50, f"Expected at least 50 rel tables, found {rel_count}"

    def test_session_table_has_required_columns(self, fresh_db):
        """Verify Session table has all required columns."""
        # Insert a test session
        fresh_db.execute("""
            CREATE (s:Session {
                id: 'test-session-001',
                started_at: timestamp('2026-01-05 12:00:00'),
                goal: 'Test session'
            })
        """)

        # Query it back
        result = fresh_db.execute("""
            MATCH (s:Session {id: 'test-session-001'})
            RETURN s.id, s.goal
        """)

        assert result.has_next()
        row = result.get_next()
        assert row[0] == "test-session-001"
        assert row[1] == "Test session"

    def test_insight_table_supports_embeddings(self, fresh_db):
        """Verify Insight table can store embeddings."""
        # Create a fake embedding (768 dimensions)
        embedding = [0.1] * 768

        fresh_db.execute(f"""
            CREATE (i:Insight {{
                id: 'test-insight-001',
                content: 'Test insight content',
                created_at: timestamp('2026-01-05 12:00:00'),
                embedding: {embedding}
            }})
        """)

        # Query it back
        result = fresh_db.execute("""
            MATCH (i:Insight {id: 'test-insight-001'})
            RETURN i.content, size(i.embedding)
        """)

        assert result.has_next()
        row = result.get_next()
        assert row[0] == "Test insight content"
        assert row[1] == 768

    def test_crud_operations_work(self, fresh_db):
        """Verify basic CRUD operations on nodes."""
        # Create
        fresh_db.execute("""
            CREATE (b:Belief {
                id: 'test-belief-001',
                content: 'Test belief',
                adopted_at: timestamp('2026-01-05 12:00:00')
            })
        """)

        # Read
        result = fresh_db.execute("""
            MATCH (b:Belief {id: 'test-belief-001'})
            RETURN b.content
        """)
        assert result.has_next()
        assert result.get_next()[0] == "Test belief"

        # Update
        fresh_db.execute("""
            MATCH (b:Belief {id: 'test-belief-001'})
            SET b.content = 'Updated belief'
        """)

        result = fresh_db.execute("""
            MATCH (b:Belief {id: 'test-belief-001'})
            RETURN b.content
        """)
        assert result.has_next()
        assert result.get_next()[0] == "Updated belief"

        # Delete
        fresh_db.execute("""
            MATCH (b:Belief {id: 'test-belief-001'})
            DELETE b
        """)

        result = fresh_db.execute("""
            MATCH (b:Belief {id: 'test-belief-001'})
            RETURN b
        """)
        assert not result.has_next()

    def test_relationship_creation_works(self, fresh_db):
        """Verify relationships can be created between nodes."""
        # Create session and insight
        fresh_db.execute("""
            CREATE (s:Session {id: 'test-session-rel', started_at: timestamp('2026-01-05 12:00:00')})
        """)
        fresh_db.execute("""
            CREATE (i:Insight {id: 'test-insight-rel', content: 'Test', created_at: timestamp('2026-01-05 12:00:00')})
        """)

        # Create PRODUCED_INSIGHT relationship
        fresh_db.execute("""
            MATCH (s:Session {id: 'test-session-rel'})
            MATCH (i:Insight {id: 'test-insight-rel'})
            CREATE (s)-[:PRODUCED_INSIGHT {valid_from: timestamp('2026-01-05 12:00:00')}]->(i)
        """)

        # Verify relationship exists
        result = fresh_db.execute("""
            MATCH (s:Session {id: 'test-session-rel'})-[:PRODUCED_INSIGHT]->(i:Insight)
            RETURN i.id
        """)

        assert result.has_next()
        assert result.get_next()[0] == "test-insight-rel"
