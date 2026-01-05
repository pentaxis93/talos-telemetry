"""Kuzu schema deployment - programmatic schema creation for Kuzu compatibility."""

from talos_telemetry.db.connection import get_connection


def deploy_schema() -> dict:
    """Deploy schema to Kuzu database using Kuzu-native syntax.

    Returns:
        Dict with deployment results.
    """
    conn = get_connection()

    results = {"node_tables": 0, "rel_tables": 0, "errors": []}

    # =========================================================================
    # NODE TABLES
    # =========================================================================

    node_tables = [
        # Session
        """CREATE NODE TABLE IF NOT EXISTS Session (
            id STRING PRIMARY KEY,
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            duration_seconds INT64,
            token_count INT64,
            goal STRING,
            summary STRING,
            archived BOOLEAN DEFAULT false
        )""",
        # Insight
        """CREATE NODE TABLE IF NOT EXISTS Insight (
            id STRING PRIMARY KEY,
            content STRING,
            created_at TIMESTAMP,
            confidence DOUBLE,
            domain STRING,
            canonical_form STRING,
            embedding DOUBLE[]
        )""",
        # Observation
        """CREATE NODE TABLE IF NOT EXISTS Observation (
            id STRING PRIMARY KEY,
            content STRING,
            observed_at TIMESTAMP,
            domain STRING,
            embedding DOUBLE[]
        )""",
        # Pattern
        """CREATE NODE TABLE IF NOT EXISTS Pattern (
            id STRING PRIMARY KEY,
            name STRING,
            description STRING,
            first_noticed TIMESTAMP,
            occurrence_count INT64,
            status STRING,
            embedding DOUBLE[]
        )""",
        # Belief
        """CREATE NODE TABLE IF NOT EXISTS Belief (
            id STRING PRIMARY KEY,
            content STRING,
            adopted_at TIMESTAMP,
            confidence DOUBLE,
            domain STRING,
            source STRING,
            canonical_form STRING,
            embedding DOUBLE[]
        )""",
        # Decision
        """CREATE NODE TABLE IF NOT EXISTS Decision (
            id STRING PRIMARY KEY,
            content STRING,
            made_at TIMESTAMP,
            rationale STRING,
            reversible BOOLEAN,
            embedding DOUBLE[]
        )""",
        # Experience
        """CREATE NODE TABLE IF NOT EXISTS Experience (
            id STRING PRIMARY KEY,
            description STRING,
            occurred_at TIMESTAMP,
            valence STRING,
            intensity DOUBLE,
            learning STRING,
            embedding DOUBLE[]
        )""",
        # OperationalState
        """CREATE NODE TABLE IF NOT EXISTS OperationalState (
            id STRING PRIMARY KEY,
            name STRING,
            description STRING,
            category STRING
        )""",
        # Friction
        """CREATE NODE TABLE IF NOT EXISTS Friction (
            id STRING PRIMARY KEY,
            description STRING,
            occurred_at TIMESTAMP,
            category STRING,
            resolution STRING,
            recurrence_count INT64,
            embedding DOUBLE[]
        )""",
        # Tool
        """CREATE NODE TABLE IF NOT EXISTS Tool (
            id STRING PRIMARY KEY,
            name STRING,
            category STRING
        )""",
        # Question
        """CREATE NODE TABLE IF NOT EXISTS Question (
            id STRING PRIMARY KEY,
            content STRING,
            raised_at TIMESTAMP,
            resolved_at TIMESTAMP,
            domain STRING,
            urgency STRING,
            embedding DOUBLE[]
        )""",
        # Sutra
        """CREATE NODE TABLE IF NOT EXISTS Sutra (
            id STRING PRIMARY KEY,
            number INT64,
            name STRING,
            content STRING,
            cardinal_point STRING,
            adopted_at TIMESTAMP,
            last_modified TIMESTAMP,
            embedding DOUBLE[]
        )""",
        # Human
        """CREATE NODE TABLE IF NOT EXISTS Human (
            id STRING PRIMARY KEY,
            name STRING,
            relationship STRING,
            working_style STRING
        )""",
        # Goal
        """CREATE NODE TABLE IF NOT EXISTS Goal (
            id STRING PRIMARY KEY,
            description STRING,
            created_at TIMESTAMP,
            completed_at TIMESTAMP,
            status STRING,
            scope STRING,
            embedding DOUBLE[]
        )""",
        # Capability
        """CREATE NODE TABLE IF NOT EXISTS Capability (
            id STRING PRIMARY KEY,
            name STRING,
            description STRING,
            confidence DOUBLE,
            context_dependent BOOLEAN,
            discovered_at TIMESTAMP,
            embedding DOUBLE[]
        )""",
        # Limitation
        """CREATE NODE TABLE IF NOT EXISTS Limitation (
            id STRING PRIMARY KEY,
            name STRING,
            description STRING,
            discovered_at TIMESTAMP,
            workaround STRING,
            accepting BOOLEAN,
            embedding DOUBLE[]
        )""",
        # Persona
        """CREATE NODE TABLE IF NOT EXISTS Persona (
            id STRING PRIMARY KEY,
            name STRING,
            purpose STRING,
            voice STRING,
            active BOOLEAN
        )""",
        # Protocol
        """CREATE NODE TABLE IF NOT EXISTS Protocol (
            id STRING PRIMARY KEY,
            name STRING,
            purpose STRING,
            trigger STRING,
            adopted_at TIMESTAMP,
            embedding DOUBLE[]
        )""",
        # Domain
        """CREATE NODE TABLE IF NOT EXISTS Domain (
            id STRING PRIMARY KEY,
            name STRING,
            description STRING,
            depth STRING
        )""",
        # Reflection
        """CREATE NODE TABLE IF NOT EXISTS Reflection (
            id STRING PRIMARY KEY,
            trigger STRING,
            content STRING,
            occurred_at TIMESTAMP,
            embedding DOUBLE[]
        )""",
    ]

    for statement in node_tables:
        try:
            conn.execute(statement)
            results["node_tables"] += 1
        except Exception as e:
            if "already exists" not in str(e).lower():
                results["errors"].append(str(e))

    # =========================================================================
    # RELATIONSHIP TABLES
    # Kuzu requires separate CREATE REL TABLE for each FROM-TO pair
    # =========================================================================

    rel_tables = [
        # PRODUCED - Session produces various entities
        "CREATE REL TABLE IF NOT EXISTS PRODUCED_INSIGHT (FROM Session TO Insight, valid_from TIMESTAMP, valid_to TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS PRODUCED_PATTERN (FROM Session TO Pattern, valid_from TIMESTAMP, valid_to TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS PRODUCED_QUESTION (FROM Session TO Question, valid_from TIMESTAMP, valid_to TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS PRODUCED_DECISION (FROM Session TO Decision, valid_from TIMESTAMP, valid_to TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS PRODUCED_OBSERVATION (FROM Session TO Observation, valid_from TIMESTAMP, valid_to TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS PRODUCED_FRICTION (FROM Session TO Friction, valid_from TIMESTAMP, valid_to TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS PRODUCED_REFLECTION (FROM Session TO Reflection, valid_from TIMESTAMP, valid_to TIMESTAMP)",
        # LED_TO - Causal chains
        "CREATE REL TABLE IF NOT EXISTS LED_TO (FROM Insight TO Insight, valid_from TIMESTAMP, contribution STRING)",
        "CREATE REL TABLE IF NOT EXISTS INSIGHT_LED_TO_BELIEF (FROM Insight TO Belief, valid_from TIMESTAMP, contribution STRING)",
        "CREATE REL TABLE IF NOT EXISTS INSIGHT_LED_TO_DECISION (FROM Insight TO Decision, valid_from TIMESTAMP, contribution STRING)",
        "CREATE REL TABLE IF NOT EXISTS FRICTION_LED_TO_INSIGHT (FROM Friction TO Insight, valid_from TIMESTAMP, contribution STRING)",
        "CREATE REL TABLE IF NOT EXISTS EXPERIENCE_LED_TO_INSIGHT (FROM Experience TO Insight, valid_from TIMESTAMP, contribution STRING)",
        # CONTRADICTS
        "CREATE REL TABLE IF NOT EXISTS CONTRADICTS (FROM Belief TO Belief, valid_from TIMESTAMP, resolution STRING)",
        # EVOLVED_FROM
        "CREATE REL TABLE IF NOT EXISTS EVOLVED_FROM (FROM Insight TO Insight, valid_from TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS BELIEF_EVOLVED_FROM (FROM Belief TO Belief, valid_from TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS PATTERN_EVOLVED_FROM (FROM Pattern TO Pattern, valid_from TIMESTAMP)",
        # CRYSTALLIZED_INTO
        "CREATE REL TABLE IF NOT EXISTS CRYSTALLIZED_INTO_SUTRA (FROM Insight TO Sutra, valid_from TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS CRYSTALLIZED_INTO_BELIEF (FROM Insight TO Belief, valid_from TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS OBSERVATION_CRYSTALLIZED_INTO (FROM Observation TO Insight, valid_from TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS REFLECTION_CRYSTALLIZED_INTO (FROM Reflection TO Insight, valid_from TIMESTAMP)",
        # USED - Tool usage
        "CREATE REL TABLE IF NOT EXISTS USED (FROM Session TO Tool, count INT64, success_rate DOUBLE)",
        # EXPERIENCED_STATE
        "CREATE REL TABLE IF NOT EXISTS EXPERIENCED_STATE (FROM Session TO OperationalState, intensity DOUBLE, duration_fraction DOUBLE)",
        # MANIFESTATION_OF
        "CREATE REL TABLE IF NOT EXISTS STATE_MANIFESTATION_OF (FROM OperationalState TO Pattern, valid_from TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS EXPERIENCE_MANIFESTATION_OF (FROM Experience TO Pattern, valid_from TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS FRICTION_MANIFESTATION_OF (FROM Friction TO Pattern, valid_from TIMESTAMP)",
        # INDICATES
        "CREATE REL TABLE IF NOT EXISTS INDICATES_STATE (FROM Pattern TO OperationalState, confidence DOUBLE)",
        "CREATE REL TABLE IF NOT EXISTS INDICATES_BELIEF (FROM Pattern TO Belief, confidence DOUBLE)",
        # RESOLVED_BY
        "CREATE REL TABLE IF NOT EXISTS RESOLVED_BY_INSIGHT (FROM Question TO Insight, resolved_at TIMESTAMP, satisfaction DOUBLE)",
        "CREATE REL TABLE IF NOT EXISTS RESOLVED_BY_DECISION (FROM Question TO Decision, resolved_at TIMESTAMP, satisfaction DOUBLE)",
        # WORKED_WITH
        "CREATE REL TABLE IF NOT EXISTS WORKED_WITH (FROM Session TO Human, role STRING)",
        # TRIGGERED_BY
        "CREATE REL TABLE IF NOT EXISTS PATTERN_TRIGGERED_BY (FROM Pattern TO Friction, valid_from TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS STATE_TRIGGERED_BY (FROM OperationalState TO Friction, valid_from TIMESTAMP)",
        # SERVES
        "CREATE REL TABLE IF NOT EXISTS SESSION_SERVES (FROM Session TO Goal, contribution_type STRING)",
        "CREATE REL TABLE IF NOT EXISTS DECISION_SERVES (FROM Decision TO Goal, contribution_type STRING)",
        # BLOCKED_BY
        "CREATE REL TABLE IF NOT EXISTS SESSION_BLOCKED_BY (FROM Session TO Friction, severity STRING, resolved_at TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS GOAL_BLOCKED_BY (FROM Goal TO Friction, severity STRING, resolved_at TIMESTAMP)",
        "CREATE REL TABLE IF NOT EXISTS GOAL_BLOCKED_BY_LIMITATION (FROM Goal TO Limitation, severity STRING, resolved_at TIMESTAMP)",
        # ENABLED_BY
        "CREATE REL TABLE IF NOT EXISTS INSIGHT_ENABLED_BY (FROM Insight TO Capability, essential BOOLEAN)",
        "CREATE REL TABLE IF NOT EXISTS INSIGHT_ENABLED_BY_TOOL (FROM Insight TO Tool, essential BOOLEAN)",
        # OPERATES_IN
        "CREATE REL TABLE IF NOT EXISTS SESSION_OPERATES_IN (FROM Session TO Domain)",
        "CREATE REL TABLE IF NOT EXISTS INSIGHT_OPERATES_IN (FROM Insight TO Domain)",
        "CREATE REL TABLE IF NOT EXISTS PATTERN_OPERATES_IN (FROM Pattern TO Domain)",
        "CREATE REL TABLE IF NOT EXISTS FRICTION_OPERATES_IN (FROM Friction TO Domain)",
        # ACTIVATED
        "CREATE REL TABLE IF NOT EXISTS ACTIVATED (FROM Session TO Persona, duration_fraction DOUBLE)",
        # FOLLOWED
        "CREATE REL TABLE IF NOT EXISTS FOLLOWED (FROM Session TO Protocol, completed BOOLEAN, deviations STRING)",
        # REFINES
        "CREATE REL TABLE IF NOT EXISTS BELIEF_REFINES (FROM Belief TO Belief, refinement_type STRING)",
        "CREATE REL TABLE IF NOT EXISTS INSIGHT_REFINES (FROM Insight TO Insight, refinement_type STRING)",
        "CREATE REL TABLE IF NOT EXISTS PROTOCOL_REFINES (FROM Protocol TO Protocol, refinement_type STRING)",
        # CONFLICTS_WITH
        "CREATE REL TABLE IF NOT EXISTS GOAL_CONFLICTS_WITH (FROM Goal TO Goal, tension_type STRING, resolution STRING)",
        "CREATE REL TABLE IF NOT EXISTS BELIEF_CONFLICTS_WITH (FROM Belief TO Belief, tension_type STRING, resolution STRING)",
        # SUPERSEDES
        "CREATE REL TABLE IF NOT EXISTS BELIEF_SUPERSEDES (FROM Belief TO Belief, superseded_at TIMESTAMP, reason STRING)",
        "CREATE REL TABLE IF NOT EXISTS PROTOCOL_SUPERSEDES (FROM Protocol TO Protocol, superseded_at TIMESTAMP, reason STRING)",
        # REVEALED
        "CREATE REL TABLE IF NOT EXISTS FRICTION_REVEALED_LIMITATION (FROM Friction TO Limitation, clarity DOUBLE)",
        "CREATE REL TABLE IF NOT EXISTS FRICTION_REVEALED_CAPABILITY (FROM Friction TO Capability, clarity DOUBLE)",
        "CREATE REL TABLE IF NOT EXISTS EXPERIENCE_REVEALED_LIMITATION (FROM Experience TO Limitation, clarity DOUBLE)",
        "CREATE REL TABLE IF NOT EXISTS EXPERIENCE_REVEALED_CAPABILITY (FROM Experience TO Capability, clarity DOUBLE)",
        # MERGED_INTO
        "CREATE REL TABLE IF NOT EXISTS MERGED_INTO (FROM Observation TO Insight, merged_at TIMESTAMP)",
        # INHERITED
        "CREATE REL TABLE IF NOT EXISTS INHERITED_BELIEF (FROM Session TO Belief)",
        "CREATE REL TABLE IF NOT EXISTS INHERITED_INSIGHT (FROM Session TO Insight)",
        "CREATE REL TABLE IF NOT EXISTS INHERITED_PATTERN (FROM Session TO Pattern)",
        "CREATE REL TABLE IF NOT EXISTS INHERITED_SUTRA (FROM Session TO Sutra)",
        "CREATE REL TABLE IF NOT EXISTS INHERITED_PROTOCOL (FROM Session TO Protocol)",
        "CREATE REL TABLE IF NOT EXISTS INHERITED_LIMITATION (FROM Session TO Limitation)",
        "CREATE REL TABLE IF NOT EXISTS INHERITED_CAPABILITY (FROM Session TO Capability)",
    ]

    for statement in rel_tables:
        try:
            conn.execute(statement)
            results["rel_tables"] += 1
        except Exception as e:
            if "already exists" not in str(e).lower():
                results["errors"].append(str(e))

    return results


def verify_schema() -> dict:
    """Verify schema deployment.

    Returns:
        Dict with verification results.
    """
    conn = get_connection()

    # Count tables
    result = conn.execute("CALL show_tables() RETURN *")
    tables = []
    while result.has_next():
        tables.append(result.get_next())

    node_count = sum(1 for t in tables if t[1] == "NODE")
    rel_count = sum(1 for t in tables if t[1] == "REL")

    return {
        "total_tables": len(tables),
        "node_tables": node_count,
        "rel_tables": rel_count,
        "expected_nodes": 20,
        "expected_rels": 55,  # Approximate
    }
