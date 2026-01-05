"""Tests for reference data seeding."""

import pytest


class TestReferenceDateSeeding:
    """Tests verifying reference data is seeded correctly."""

    def test_operational_states_seeded(self, fresh_db):
        """Verify all 11 operational states are seeded."""
        result = fresh_db.execute("""
            MATCH (s:OperationalState)
            RETURN count(s) as count
        """)

        assert result.has_next()
        count = result.get_next()[0]
        assert count == 11, f"Expected 11 operational states, found {count}"

    def test_operational_states_have_categories(self, fresh_db):
        """Verify operational states have correct categories."""
        expected_categories = {"cognitive", "resource", "flow", "alignment"}

        result = fresh_db.execute("""
            MATCH (s:OperationalState)
            RETURN DISTINCT s.category
        """)

        found_categories = set()
        while result.has_next():
            found_categories.add(result.get_next()[0])

        assert found_categories == expected_categories

    def test_specific_states_exist(self, fresh_db):
        """Verify specific states are present."""
        expected_states = [
            ("clarity", "cognitive"),
            ("momentum", "flow"),
            ("context_pressure", "resource"),
            ("on_track", "alignment"),
        ]

        for name, category in expected_states:
            result = fresh_db.execute(f"""
                MATCH (s:OperationalState {{name: '{name}'}})
                RETURN s.category
            """)

            assert result.has_next(), f"State '{name}' not found"
            assert result.get_next()[0] == category

    def test_domains_seeded(self, fresh_db):
        """Verify all 10 domains are seeded."""
        result = fresh_db.execute("""
            MATCH (d:Domain)
            RETURN count(d) as count
        """)

        assert result.has_next()
        count = result.get_next()[0]
        assert count == 10, f"Expected 10 domains, found {count}"

    def test_domains_have_depth(self, fresh_db):
        """Verify domains have depth classification."""
        result = fresh_db.execute("""
            MATCH (d:Domain)
            WHERE d.depth IS NOT NULL
            RETURN count(d) as count
        """)

        assert result.has_next()
        count = result.get_next()[0]
        assert count == 10, f"Expected all 10 domains to have depth, found {count}"

    def test_specific_domains_exist(self, fresh_db):
        """Verify specific domains are present."""
        expected_domains = [
            ("technical", "working"),
            ("meta-cognitive", "deep"),
            ("philosophical", "working"),
        ]

        for name, depth in expected_domains:
            result = fresh_db.execute(f"""
                MATCH (d:Domain {{name: '{name}'}})
                RETURN d.depth
            """)

            assert result.has_next(), f"Domain '{name}' not found"
            assert result.get_next()[0] == depth

    def test_tools_seeded(self, fresh_db):
        """Verify all 10 tools are seeded."""
        result = fresh_db.execute("""
            MATCH (t:Tool)
            RETURN count(t) as count
        """)

        assert result.has_next()
        count = result.get_next()[0]
        assert count == 10, f"Expected 10 tools, found {count}"

    def test_tools_have_categories(self, fresh_db):
        """Verify tools have category classification."""
        expected_categories = {"file", "search", "compute", "communication"}

        result = fresh_db.execute("""
            MATCH (t:Tool)
            RETURN DISTINCT t.category
        """)

        found_categories = set()
        while result.has_next():
            found_categories.add(result.get_next()[0])

        assert found_categories == expected_categories

    def test_specific_tools_exist(self, fresh_db):
        """Verify specific tools are present."""
        expected_tools = [
            ("bash", "compute"),
            ("read", "file"),
            ("grep", "search"),
            ("webfetch", "communication"),
        ]

        for name, category in expected_tools:
            result = fresh_db.execute(f"""
                MATCH (t:Tool {{name: '{name}'}})
                RETURN t.category
            """)

            assert result.has_next(), f"Tool '{name}' not found"
            assert result.get_next()[0] == category
