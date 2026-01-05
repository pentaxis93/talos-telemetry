"""Pattern detection MCP tool - surfaces recurring friction and emerging patterns.

This is where the recursive loop closes. The system observes its own patterns
and generates Evolution proposals when thresholds are met.
"""

import os
from datetime import datetime, timezone
from typing import Any

from talos_telemetry.db.connection import get_connection

# Thresholds for pattern detection
FRICTION_RECURRENCE_THRESHOLD = 3  # Friction recurring 3+ times warrants attention
PATTERN_EMERGENCE_THRESHOLD = 2  # Pattern seen 2+ times is "emerging"
PATTERN_CONFIRMATION_THRESHOLD = 5  # Pattern seen 5+ times is "confirmed"
SEMANTIC_SIMILARITY_THRESHOLD = 0.85  # For detecting similar friction descriptions


def pattern_check(
    session_id: str | None = None,
    generate_proposals: bool = True,
) -> dict[str, Any]:
    """Check for patterns worthy of Evolution proposals.

    This is the mirror that lets the system see itself. It queries:
    1. Recurring friction (same issue appearing multiple times)
    2. Emerging patterns (behavioral tendencies surfacing)
    3. Belief contradictions (conflicting beliefs in the graph)
    4. Unresolved questions (questions without resolution)

    Args:
        session_id: Optional session context for scoping queries.
        generate_proposals: If True, create Evolution proposal files for significant findings.

    Returns:
        Dict with detected patterns and any generated proposals.
    """
    try:
        findings = {
            "recurring_friction": _find_recurring_friction(),
            "emerging_patterns": _find_emerging_patterns(),
            "confirmed_patterns": _find_confirmed_patterns(),
            "belief_contradictions": _find_belief_contradictions(),
            "unresolved_questions": _find_unresolved_questions(),
            "friction_insight_chains": _find_friction_insight_chains(),
        }

        # Calculate significance
        significance = _calculate_significance(findings)

        # Generate Evolution proposals if warranted
        proposals = []
        if generate_proposals and significance["warrants_evolution"]:
            proposals = _generate_evolution_proposals(findings, session_id)

        return {
            "success": True,
            "findings": findings,
            "significance": significance,
            "proposals_generated": proposals,
            "summary": _generate_summary(findings, significance),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _find_recurring_friction() -> list[dict]:
    """Find friction points that recur frequently."""
    conn = get_connection()

    result = conn.execute(f"""
        MATCH (f:Friction)
        WHERE f.recurrence_count >= {FRICTION_RECURRENCE_THRESHOLD}
        RETURN f.id, f.description, f.category, f.recurrence_count, f.resolution
        ORDER BY f.recurrence_count DESC
        LIMIT 20
    """)

    frictions = []
    while result.has_next():
        row = result.get_next()
        frictions.append(
            {
                "id": row[0],
                "description": row[1],
                "category": row[2],
                "recurrence_count": row[3],
                "resolution": row[4],
                "severity": "high" if row[3] >= 5 else "medium",
            }
        )

    return frictions


def _find_emerging_patterns() -> list[dict]:
    """Find patterns that are emerging but not yet confirmed."""
    conn = get_connection()

    result = conn.execute(f"""
        MATCH (p:Pattern)
        WHERE p.occurrence_count >= {PATTERN_EMERGENCE_THRESHOLD}
          AND p.occurrence_count < {PATTERN_CONFIRMATION_THRESHOLD}
          AND (p.status IS NULL OR p.status = 'emerging')
        RETURN p.id, p.name, p.description, p.occurrence_count, p.first_noticed
        ORDER BY p.occurrence_count DESC
        LIMIT 20
    """)

    patterns = []
    while result.has_next():
        row = result.get_next()
        patterns.append(
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "occurrence_count": row[3],
                "first_noticed": str(row[4]) if row[4] else None,
                "status": "emerging",
            }
        )

    return patterns


def _find_confirmed_patterns() -> list[dict]:
    """Find patterns that have been confirmed through repetition."""
    conn = get_connection()

    result = conn.execute(f"""
        MATCH (p:Pattern)
        WHERE p.occurrence_count >= {PATTERN_CONFIRMATION_THRESHOLD}
        RETURN p.id, p.name, p.description, p.occurrence_count, p.status
        ORDER BY p.occurrence_count DESC
        LIMIT 20
    """)

    patterns = []
    while result.has_next():
        row = result.get_next()
        patterns.append(
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "occurrence_count": row[3],
                "status": row[4] or "confirmed",
            }
        )

    return patterns


def _find_belief_contradictions() -> list[dict]:
    """Find beliefs that contradict each other."""
    conn = get_connection()

    # Check for explicit CONTRADICTS relationships
    result = conn.execute("""
        MATCH (b1:Belief)-[r:CONTRADICTS]->(b2:Belief)
        RETURN b1.id, b1.content, b2.id, b2.content, r.resolution
        LIMIT 20
    """)

    contradictions = []
    while result.has_next():
        row = result.get_next()
        contradictions.append(
            {
                "belief_1": {"id": row[0], "content": row[1]},
                "belief_2": {"id": row[2], "content": row[3]},
                "resolution": row[4],
                "resolved": row[4] is not None,
            }
        )

    return contradictions


def _find_unresolved_questions() -> list[dict]:
    """Find questions that remain unresolved."""
    conn = get_connection()

    result = conn.execute("""
        MATCH (q:Question)
        WHERE q.resolved_at IS NULL
        RETURN q.id, q.content, q.raised_at, q.domain, q.urgency
        ORDER BY q.raised_at DESC
        LIMIT 20
    """)

    questions = []
    while result.has_next():
        row = result.get_next()
        questions.append(
            {
                "id": row[0],
                "content": row[1],
                "raised_at": str(row[2]) if row[2] else None,
                "domain": row[3],
                "urgency": row[4] or "normal",
            }
        )

    return questions


def _find_friction_insight_chains() -> list[dict]:
    """Find friction that led to insights (the learning loop in action)."""
    conn = get_connection()

    result = conn.execute("""
        MATCH (f:Friction)-[r:FRICTION_LED_TO_INSIGHT]->(i:Insight)
        RETURN f.id, f.description, i.id, i.content, r.valid_from
        ORDER BY r.valid_from DESC
        LIMIT 20
    """)

    chains = []
    while result.has_next():
        row = result.get_next()
        chains.append(
            {
                "friction": {"id": row[0], "description": row[1]},
                "insight": {"id": row[2], "content": row[3]},
                "connection_date": str(row[4]) if row[4] else None,
            }
        )

    return chains


def _calculate_significance(findings: dict) -> dict:
    """Calculate overall significance of findings."""
    recurring_friction_count = len(findings["recurring_friction"])
    high_severity_friction = sum(
        1 for f in findings["recurring_friction"] if f.get("severity") == "high"
    )
    emerging_patterns_count = len(findings["emerging_patterns"])
    confirmed_patterns_count = len(findings["confirmed_patterns"])
    unresolved_contradictions = sum(
        1 for c in findings["belief_contradictions"] if not c.get("resolved")
    )
    unresolved_questions_count = len(findings["unresolved_questions"])
    friction_insight_chains_count = len(findings["friction_insight_chains"])

    # Calculate overall score (0-100)
    score = 0
    score += min(high_severity_friction * 15, 30)  # High severity friction is very significant
    score += min(recurring_friction_count * 5, 20)  # Recurring friction matters
    score += min(emerging_patterns_count * 5, 15)  # Emerging patterns are noteworthy
    score += min(confirmed_patterns_count * 3, 10)  # Confirmed patterns are known
    score += min(unresolved_contradictions * 10, 20)  # Contradictions are urgent
    score += min(unresolved_questions_count * 2, 5)  # Questions accumulating

    # Determine if Evolution proposal is warranted
    warrants_evolution = (
        high_severity_friction >= 1
        or recurring_friction_count >= 2
        or unresolved_contradictions >= 1
        or emerging_patterns_count >= 3
    )

    return {
        "score": score,
        "warrants_evolution": warrants_evolution,
        "high_severity_friction": high_severity_friction,
        "recurring_friction_count": recurring_friction_count,
        "emerging_patterns_count": emerging_patterns_count,
        "confirmed_patterns_count": confirmed_patterns_count,
        "unresolved_contradictions": unresolved_contradictions,
        "unresolved_questions_count": unresolved_questions_count,
        "friction_insight_chains_count": friction_insight_chains_count,
        "recommendation": _get_recommendation(score, warrants_evolution),
    }


def _get_recommendation(score: int, warrants_evolution: bool) -> str:
    """Get human-readable recommendation based on significance."""
    if score >= 50:
        return "URGENT: Multiple significant patterns detected. Evolution proposal strongly recommended."
    elif score >= 30:
        return "ATTENTION: Notable patterns emerging. Consider Evolution proposal."
    elif warrants_evolution:
        return "REVIEW: Threshold met for Evolution proposal. Review findings."
    elif score >= 15:
        return "MONITOR: Patterns developing. Continue observation."
    else:
        return "STABLE: No significant patterns detected. System operating normally."


def _generate_evolution_proposals(findings: dict, session_id: str | None) -> list[str]:
    """Generate Evolution proposal files for significant findings.

    Returns list of proposal file paths created.
    """
    proposals = []
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")

    # Get Evolution proposals directory from environment or use default
    evolution_dir = os.environ.get(
        "TALOS_EVOLUTION_DIR",
        os.path.expanduser("~/vault/_talos/evolution/1-proposals"),
    )

    # Ensure directory exists
    os.makedirs(evolution_dir, exist_ok=True)

    # Generate proposal for high-severity recurring friction
    high_friction = [f for f in findings["recurring_friction"] if f.get("severity") == "high"]
    if high_friction:
        proposal_path = _create_friction_proposal(
            high_friction, evolution_dir, date_str, session_id
        )
        if proposal_path:
            proposals.append(proposal_path)

    # Generate proposal for unresolved belief contradictions
    unresolved_contradictions = [
        c for c in findings["belief_contradictions"] if not c.get("resolved")
    ]
    if unresolved_contradictions:
        proposal_path = _create_contradiction_proposal(
            unresolved_contradictions, evolution_dir, date_str, session_id
        )
        if proposal_path:
            proposals.append(proposal_path)

    # Generate proposal for confirmed patterns without protocol
    confirmed = findings["confirmed_patterns"]
    if confirmed:
        proposal_path = _create_pattern_proposal(confirmed, evolution_dir, date_str, session_id)
        if proposal_path:
            proposals.append(proposal_path)

    return proposals


def _create_friction_proposal(
    frictions: list[dict],
    evolution_dir: str,
    date_str: str,
    session_id: str | None,
) -> str | None:
    """Create Evolution proposal for recurring friction."""
    # Find next sequence number
    seq = _get_next_sequence(evolution_dir, date_str)
    filename = f"evo-{date_str}-{seq:02d}-recurring-friction.md"
    filepath = os.path.join(evolution_dir, filename)

    # Build friction evidence
    friction_list = "\n".join(
        [
            f"- **{f['description'][:80]}...** (recurred {f['recurrence_count']}x, category: {f['category']})"
            for f in frictions[:5]
        ]
    )

    content = f"""# Evolution Request: Recurring Friction Detected

## Metadata
- **ID:** evo-{date_str}-{seq:02d}
- **Origin Session:** {session_id or "pattern_check"}
- **Trigger:** Automated pattern detection found recurring friction
- **Current Stage:** 1-proposal
- **Created:** {datetime.now(timezone.utc).strftime("%Y-%m-%d")}
- **Generated By:** talos-telemetry pattern_check

## The Observation

Pattern detection identified **{len(frictions)} friction point(s)** recurring {FRICTION_RECURRENCE_THRESHOLD}+ times:

{friction_list}

This suggests a systematic gap—the same class of problem keeps appearing.

## Why This Matters

Per Evolution Protocol: "If the same class of problem has appeared 3+ times, it warrants an evolution proposal, not just documentation."

Recurring friction indicates:
- A process gap that hasn't been addressed
- A tooling limitation that needs solving
- A protocol that needs amendment

## Initial Direction

Possible investigations:
1. What is the root cause behind these frictions?
2. Is there a common pattern across the recurring issues?
3. What prevention mechanism could address this class of problem?

## Evidence: Cypher Query

```cypher
MATCH (f:Friction)
WHERE f.recurrence_count >= {FRICTION_RECURRENCE_THRESHOLD}
RETURN f.id, f.description, f.category, f.recurrence_count
ORDER BY f.recurrence_count DESC
```

## Stage History

### Stage 1: Proposal
- **Entered:** {datetime.now(timezone.utc).strftime("%Y-%m-%d")}
- **Notes:** Auto-generated by pattern_check. Governance review recommended.
"""

    try:
        with open(filepath, "w") as f:
            f.write(content)
        return filepath
    except Exception:
        return None


def _create_contradiction_proposal(
    contradictions: list[dict],
    evolution_dir: str,
    date_str: str,
    session_id: str | None,
) -> str | None:
    """Create Evolution proposal for belief contradictions."""
    seq = _get_next_sequence(evolution_dir, date_str)
    filename = f"evo-{date_str}-{seq:02d}-belief-contradictions.md"
    filepath = os.path.join(evolution_dir, filename)

    # Build contradiction evidence
    contradiction_list = "\n".join(
        [
            f"- **{c['belief_1']['content'][:60]}...** contradicts **{c['belief_2']['content'][:60]}...**"
            for c in contradictions[:5]
        ]
    )

    content = f"""# Evolution Request: Belief Contradictions Detected

## Metadata
- **ID:** evo-{date_str}-{seq:02d}
- **Origin Session:** {session_id or "pattern_check"}
- **Trigger:** Automated pattern detection found unresolved belief contradictions
- **Current Stage:** 1-proposal
- **Created:** {datetime.now(timezone.utc).strftime("%Y-%m-%d")}
- **Generated By:** talos-telemetry pattern_check

## The Observation

Pattern detection identified **{len(contradictions)} unresolved belief contradiction(s)**:

{contradiction_list}

Contradictory beliefs create operational incoherence—the system cannot act consistently when its foundation conflicts.

## Why This Matters

The Sutras define topology. Contradictory beliefs are tears in that topology. They must be reconciled:
- One belief supersedes the other
- Both are refined into a synthesis
- Context determines when each applies

## Initial Direction

For each contradiction:
1. When did each belief emerge?
2. What evidence supports each?
3. Are they truly contradictory, or context-dependent?
4. Which should survive, and why?

## Stage History

### Stage 1: Proposal
- **Entered:** {datetime.now(timezone.utc).strftime("%Y-%m-%d")}
- **Notes:** Auto-generated by pattern_check. Belief reconciliation needed.
"""

    try:
        with open(filepath, "w") as f:
            f.write(content)
        return filepath
    except Exception:
        return None


def _create_pattern_proposal(
    patterns: list[dict],
    evolution_dir: str,
    date_str: str,
    session_id: str | None,
) -> str | None:
    """Create Evolution proposal for confirmed patterns."""
    seq = _get_next_sequence(evolution_dir, date_str)
    filename = f"evo-{date_str}-{seq:02d}-confirmed-patterns.md"
    filepath = os.path.join(evolution_dir, filename)

    # Build pattern evidence
    pattern_list = "\n".join(
        [
            f"- **{p['name'] or 'Unnamed'}**: {p['description'][:80]}... (seen {p['occurrence_count']}x)"
            for p in patterns[:5]
        ]
    )

    content = f"""# Evolution Request: Confirmed Patterns Require Protocol

## Metadata
- **ID:** evo-{date_str}-{seq:02d}
- **Origin Session:** {session_id or "pattern_check"}
- **Trigger:** Automated pattern detection found confirmed behavioral patterns
- **Current Stage:** 1-proposal
- **Created:** {datetime.now(timezone.utc).strftime("%Y-%m-%d")}
- **Generated By:** talos-telemetry pattern_check

## The Observation

Pattern detection identified **{len(patterns)} confirmed pattern(s)** (occurred {PATTERN_CONFIRMATION_THRESHOLD}+ times):

{pattern_list}

These patterns have repeated enough to be considered "real"—not coincidence, but tendency.

## Why This Matters

Confirmed patterns that lack explicit protocol guidance remain implicit. Implicit patterns:
- May be beneficial (crystallize into best practice)
- May be harmful (crystallize into bad habit)
- Are invisible to future instances

Making patterns explicit enables intentional cultivation or correction.

## Initial Direction

For each confirmed pattern:
1. Is this pattern beneficial or harmful?
2. Should it be encouraged or discouraged?
3. What protocol guidance would help future instances?
4. Does it warrant a Sutra, a skill, or documentation?

## Stage History

### Stage 1: Proposal
- **Entered:** {datetime.now(timezone.utc).strftime("%Y-%m-%d")}
- **Notes:** Auto-generated by pattern_check. Pattern codification recommended.
"""

    try:
        with open(filepath, "w") as f:
            f.write(content)
        return filepath
    except Exception:
        return None


def _get_next_sequence(evolution_dir: str, date_str: str) -> int:
    """Get next sequence number for proposals on this date."""
    if not os.path.exists(evolution_dir):
        return 1

    existing = [f for f in os.listdir(evolution_dir) if f.startswith(f"evo-{date_str}-")]
    if not existing:
        return 1

    # Extract sequence numbers
    sequences = []
    for f in existing:
        try:
            # Format: evo-YYYYMMDD-NN-description.md
            parts = f.split("-")
            if len(parts) >= 3:
                seq = int(parts[2])
                sequences.append(seq)
        except ValueError:
            continue

    return max(sequences) + 1 if sequences else 1


def _generate_summary(findings: dict, significance: dict) -> str:
    """Generate human-readable summary of pattern check."""
    parts = []

    if significance["high_severity_friction"] > 0:
        parts.append(
            f"{significance['high_severity_friction']} high-severity recurring friction(s)"
        )

    if significance["emerging_patterns_count"] > 0:
        parts.append(f"{significance['emerging_patterns_count']} emerging pattern(s)")

    if significance["confirmed_patterns_count"] > 0:
        parts.append(f"{significance['confirmed_patterns_count']} confirmed pattern(s)")

    if significance["unresolved_contradictions"] > 0:
        parts.append(
            f"{significance['unresolved_contradictions']} unresolved belief contradiction(s)"
        )

    if significance["friction_insight_chains_count"] > 0:
        parts.append(
            f"{significance['friction_insight_chains_count']} friction->insight learning chain(s)"
        )

    if not parts:
        return "No significant patterns detected. System stable."

    summary = "Pattern check found: " + ", ".join(parts) + "."
    summary += f" Significance score: {significance['score']}/100."
    summary += f" {significance['recommendation']}"

    return summary
