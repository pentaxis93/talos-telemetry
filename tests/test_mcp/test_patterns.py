"""Tests for pattern_check MCP tool."""

import os
import tempfile
from datetime import datetime, timezone

from talos_telemetry.db.connection import get_connection
from talos_telemetry.mcp.patterns import (
    FRICTION_RECURRENCE_THRESHOLD,
    PATTERN_CONFIRMATION_THRESHOLD,
    PATTERN_EMERGENCE_THRESHOLD,
    _calculate_significance,
    _find_confirmed_patterns,
    _find_emerging_patterns,
    _find_recurring_friction,
    _generate_summary,
    pattern_check,
)


def _now_iso() -> str:
    """Return current UTC time as ISO format string for Kuzu timestamp()."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class TestFindRecurringFriction:
    """Tests for recurring friction detection."""

    def test_finds_recurring_friction(self, fresh_db):
        """Find friction that recurs at threshold."""
        conn = get_connection()

        # Create friction with high recurrence
        conn.execute(f"""
            CREATE (f:Friction {{
                id: 'friction-recurring-001',
                description: 'Database connection issues',
                category: 'technical',
                recurrence_count: {FRICTION_RECURRENCE_THRESHOLD + 2},
                occurred_at: timestamp('{_now_iso()}')
            }})
        """)

        result = _find_recurring_friction()

        assert len(result) >= 1
        found = next((f for f in result if f["id"] == "friction-recurring-001"), None)
        assert found is not None
        assert found["recurrence_count"] >= FRICTION_RECURRENCE_THRESHOLD
        assert found["severity"] == "high"  # 5+ is high

    def test_ignores_low_recurrence(self, fresh_db):
        """Ignore friction below threshold."""
        conn = get_connection()

        # Create friction with low recurrence
        conn.execute(f"""
            CREATE (f:Friction {{
                id: 'friction-low-001',
                description: 'One-off issue',
                category: 'technical',
                recurrence_count: 1,
                occurred_at: timestamp('{_now_iso()}')
            }})
        """)

        result = _find_recurring_friction()

        found = next((f for f in result if f["id"] == "friction-low-001"), None)
        assert found is None


class TestFindEmergingPatterns:
    """Tests for emerging pattern detection."""

    def test_finds_emerging_patterns(self, fresh_db):
        """Find patterns in emerging state."""
        conn = get_connection()

        # Create emerging pattern
        conn.execute(f"""
            CREATE (p:Pattern {{
                id: 'pattern-emerging-001',
                name: 'Over-engineering tendency',
                description: 'I tend to build more than needed',
                occurrence_count: {PATTERN_EMERGENCE_THRESHOLD + 1},
                status: 'emerging',
                first_noticed: timestamp('{_now_iso()}')
            }})
        """)

        result = _find_emerging_patterns()

        assert len(result) >= 1
        found = next((p for p in result if p["id"] == "pattern-emerging-001"), None)
        assert found is not None
        assert found["status"] == "emerging"

    def test_excludes_confirmed_patterns(self, fresh_db):
        """Exclude patterns that are already confirmed."""
        conn = get_connection()

        # Create confirmed pattern (should not appear in emerging)
        conn.execute(f"""
            CREATE (p:Pattern {{
                id: 'pattern-confirmed-001',
                name: 'Well-established pattern',
                description: 'This is confirmed',
                occurrence_count: {PATTERN_CONFIRMATION_THRESHOLD + 1},
                status: 'confirmed',
                first_noticed: timestamp('{_now_iso()}')
            }})
        """)

        result = _find_emerging_patterns()

        found = next((p for p in result if p["id"] == "pattern-confirmed-001"), None)
        assert found is None


class TestFindConfirmedPatterns:
    """Tests for confirmed pattern detection."""

    def test_finds_confirmed_patterns(self, fresh_db):
        """Find patterns that meet confirmation threshold."""
        conn = get_connection()

        conn.execute(f"""
            CREATE (p:Pattern {{
                id: 'pattern-confirmed-002',
                name: 'Confirmed behavioral pattern',
                description: 'This pattern is well-established',
                occurrence_count: {PATTERN_CONFIRMATION_THRESHOLD},
                first_noticed: timestamp('{_now_iso()}')
            }})
        """)

        result = _find_confirmed_patterns()

        assert len(result) >= 1
        found = next((p for p in result if p["id"] == "pattern-confirmed-002"), None)
        assert found is not None
        assert found["occurrence_count"] >= PATTERN_CONFIRMATION_THRESHOLD


class TestCalculateSignificance:
    """Tests for significance calculation."""

    def test_high_severity_triggers_evolution(self):
        """High severity friction triggers evolution recommendation."""
        findings = {
            "recurring_friction": [{"severity": "high"}],
            "emerging_patterns": [],
            "confirmed_patterns": [],
            "belief_contradictions": [],
            "unresolved_questions": [],
            "friction_insight_chains": [],
        }

        result = _calculate_significance(findings)

        assert result["warrants_evolution"] is True
        assert result["high_severity_friction"] == 1

    def test_multiple_recurring_friction_triggers_evolution(self):
        """Multiple recurring friction triggers evolution."""
        findings = {
            "recurring_friction": [{"severity": "medium"}, {"severity": "medium"}],
            "emerging_patterns": [],
            "confirmed_patterns": [],
            "belief_contradictions": [],
            "unresolved_questions": [],
            "friction_insight_chains": [],
        }

        result = _calculate_significance(findings)

        assert result["warrants_evolution"] is True
        assert result["recurring_friction_count"] == 2

    def test_unresolved_contradictions_trigger_evolution(self):
        """Unresolved belief contradictions trigger evolution."""
        findings = {
            "recurring_friction": [],
            "emerging_patterns": [],
            "confirmed_patterns": [],
            "belief_contradictions": [{"resolved": False}],
            "unresolved_questions": [],
            "friction_insight_chains": [],
        }

        result = _calculate_significance(findings)

        assert result["warrants_evolution"] is True
        assert result["unresolved_contradictions"] == 1

    def test_stable_findings_no_evolution(self):
        """Empty findings don't trigger evolution."""
        findings = {
            "recurring_friction": [],
            "emerging_patterns": [],
            "confirmed_patterns": [],
            "belief_contradictions": [],
            "unresolved_questions": [],
            "friction_insight_chains": [],
        }

        result = _calculate_significance(findings)

        assert result["warrants_evolution"] is False
        assert result["score"] == 0
        assert "STABLE" in result["recommendation"]


class TestGenerateSummary:
    """Tests for summary generation."""

    def test_generates_readable_summary(self):
        """Generate human-readable summary."""
        findings = {
            "recurring_friction": [{"severity": "high"}],
            "emerging_patterns": [{}],
            "confirmed_patterns": [],
            "belief_contradictions": [],
            "unresolved_questions": [],
            "friction_insight_chains": [{}],
        }
        significance = _calculate_significance(findings)

        summary = _generate_summary(findings, significance)

        assert "high-severity recurring friction" in summary
        assert "emerging pattern" in summary
        assert "learning chain" in summary

    def test_stable_summary(self):
        """Generate stable summary when no patterns found."""
        findings = {
            "recurring_friction": [],
            "emerging_patterns": [],
            "confirmed_patterns": [],
            "belief_contradictions": [],
            "unresolved_questions": [],
            "friction_insight_chains": [],
        }
        significance = _calculate_significance(findings)

        summary = _generate_summary(findings, significance)

        assert "stable" in summary.lower()


class TestPatternCheck:
    """Tests for full pattern_check tool."""

    def test_pattern_check_returns_structure(self, fresh_db):
        """pattern_check returns expected structure."""
        result = pattern_check(generate_proposals=False)

        assert result["success"] is True
        assert "findings" in result
        assert "significance" in result
        assert "summary" in result
        assert "recurring_friction" in result["findings"]
        assert "emerging_patterns" in result["findings"]
        assert "belief_contradictions" in result["findings"]

    def test_pattern_check_with_data(self, fresh_db):
        """pattern_check finds seeded data."""
        conn = get_connection()

        # Seed recurring friction
        conn.execute(f"""
            CREATE (f:Friction {{
                id: 'friction-test-001',
                description: 'Test recurring friction',
                category: 'test',
                recurrence_count: 5,
                occurred_at: timestamp('{_now_iso()}')
            }})
        """)

        result = pattern_check(generate_proposals=False)

        assert result["success"] is True
        assert result["significance"]["high_severity_friction"] >= 1
        assert result["significance"]["warrants_evolution"] is True

    def test_pattern_check_generates_proposals(self, fresh_db):
        """pattern_check generates proposal files when warranted."""
        conn = get_connection()

        # Create high-severity friction
        conn.execute(f"""
            CREATE (f:Friction {{
                id: 'friction-proposal-001',
                description: 'Critical recurring issue that needs addressing',
                category: 'critical',
                recurrence_count: 6,
                occurred_at: timestamp('{_now_iso()}')
            }})
        """)

        # Use temp directory for proposals
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["TALOS_EVOLUTION_DIR"] = tmpdir

            result = pattern_check(session_id="test-session", generate_proposals=True)

            assert result["success"] is True
            assert len(result["proposals_generated"]) >= 1

            # Verify file was created
            proposal_path = result["proposals_generated"][0]
            assert os.path.exists(proposal_path)

            # Verify content
            with open(proposal_path) as f:
                content = f.read()
            assert "Evolution Request" in content
            assert "Critical recurring issue" in content
            assert "test-session" in content

    def test_pattern_check_no_proposals_when_stable(self, fresh_db):
        """pattern_check doesn't generate proposals when system is stable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["TALOS_EVOLUTION_DIR"] = tmpdir

            result = pattern_check(generate_proposals=True)

            assert result["success"] is True
            # No significant patterns = no proposals
            if not result["significance"]["warrants_evolution"]:
                assert len(result["proposals_generated"]) == 0


class TestFrictionInsightChains:
    """Tests for friction->insight learning chains."""

    def test_finds_friction_insight_chains(self, fresh_db):
        """Find friction that led to insights."""
        conn = get_connection()

        # Create friction and insight with relationship
        conn.execute(f"""
            CREATE (f:Friction {{
                id: 'friction-chain-001',
                description: 'Initial friction',
                category: 'learning',
                recurrence_count: 1,
                occurred_at: timestamp('{_now_iso()}')
            }})
        """)

        conn.execute(f"""
            CREATE (i:Insight {{
                id: 'insight-chain-001',
                content: 'Learned from friction',
                created_at: timestamp('{_now_iso()}')
            }})
        """)

        conn.execute(f"""
            MATCH (f:Friction {{id: 'friction-chain-001'}})
            MATCH (i:Insight {{id: 'insight-chain-001'}})
            CREATE (f)-[:FRICTION_LED_TO_INSIGHT {{valid_from: timestamp('{_now_iso()}')}}]->(i)
        """)

        result = pattern_check(generate_proposals=False)

        assert result["success"] is True
        chains = result["findings"]["friction_insight_chains"]
        assert len(chains) >= 1

        found = next((c for c in chains if c["friction"]["id"] == "friction-chain-001"), None)
        assert found is not None
        assert found["insight"]["id"] == "insight-chain-001"
