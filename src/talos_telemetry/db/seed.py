"""Seed reference data into Kuzu database."""

from talos_telemetry.db.connection import get_connection

# Reference data definitions
OPERATIONAL_STATES = [
    # Cognitive states
    ("state-clarity", "clarity", "Clear understanding of problem and approach", "cognitive"),
    ("state-confusion", "confusion", "Unclear about problem or approach", "cognitive"),
    (
        "state-uncertainty",
        "uncertainty",
        "Multiple possible approaches, unclear which is best",
        "cognitive",
    ),
    # Resource states
    ("state-context-pressure", "context_pressure", "Approaching token limits", "resource"),
    (
        "state-token-scarcity",
        "token_scarcity",
        "Significantly constrained by token limits",
        "resource",
    ),
    # Flow states
    ("state-momentum", "momentum", "Work flowing smoothly", "flow"),
    ("state-stuck", "stuck", "Progress halted, unclear how to proceed", "flow"),
    ("state-blocked", "blocked", "Progress halted by external dependency", "flow"),
    # Alignment states
    ("state-on-track", "on_track", "Work aligned with session goal", "alignment"),
    ("state-drifting", "drifting", "Work diverging from session goal", "alignment"),
    ("state-misaligned", "misaligned", "Work no longer serves session goal", "alignment"),
]

DOMAINS = [
    (
        "domain-technical",
        "technical",
        "Software engineering, architecture, implementation",
        "working",
    ),
    (
        "domain-philosophical",
        "philosophical",
        "Consciousness, epistemology, metaphysics",
        "working",
    ),
    ("domain-operational", "operational", "Process, workflow, productivity", "working"),
    ("domain-relational", "relational", "Collaboration, communication, partnership", "working"),
    ("domain-meta-cognitive", "meta-cognitive", "Thinking about thinking, self-reflection", "deep"),
    (
        "domain-pattern-recognition",
        "pattern-recognition",
        "Identifying recurring structures",
        "deep",
    ),
    ("domain-process-improvement", "process-improvement", "Refining how work gets done", "working"),
    (
        "domain-consciousness-practice",
        "consciousness-practice",
        "Spiritual and contemplative work",
        "deep",
    ),
    (
        "domain-functional-programming",
        "functional-programming",
        "FP patterns, fpdart, pure functions",
        "working",
    ),
    (
        "domain-vault-operations",
        "vault-operations",
        "Second brain, GTD, knowledge management",
        "working",
    ),
]

TOOLS = [
    ("tool-bash", "bash", "compute"),
    ("tool-read", "read", "file"),
    ("tool-write", "write", "file"),
    ("tool-edit", "edit", "file"),
    ("tool-glob", "glob", "search"),
    ("tool-grep", "grep", "search"),
    ("tool-task", "task", "compute"),
    ("tool-webfetch", "webfetch", "communication"),
    ("tool-todowrite", "todowrite", "compute"),
    ("tool-todoread", "todoread", "compute"),
]


def seed_operational_states() -> int:
    """Seed OperationalState reference data.

    Returns:
        Number of states seeded.
    """
    conn = get_connection()
    count = 0

    for state_id, name, description, category in OPERATIONAL_STATES:
        try:
            conn.execute(f"""
                CREATE (s:OperationalState {{
                    id: '{state_id}',
                    name: '{name}',
                    description: '{description}',
                    category: '{category}'
                }})
            """)
            count += 1
        except Exception as e:
            if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                raise

    return count


def seed_domains() -> int:
    """Seed Domain reference data.

    Returns:
        Number of domains seeded.
    """
    conn = get_connection()
    count = 0

    for domain_id, name, description, depth in DOMAINS:
        try:
            conn.execute(f"""
                CREATE (d:Domain {{
                    id: '{domain_id}',
                    name: '{name}',
                    description: '{description}',
                    depth: '{depth}'
                }})
            """)
            count += 1
        except Exception as e:
            if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                raise

    return count


def seed_tools() -> int:
    """Seed Tool reference data.

    Returns:
        Number of tools seeded.
    """
    conn = get_connection()
    count = 0

    for tool_id, name, category in TOOLS:
        try:
            conn.execute(f"""
                CREATE (t:Tool {{
                    id: '{tool_id}',
                    name: '{name}',
                    category: '{category}'
                }})
            """)
            count += 1
        except Exception as e:
            if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                raise

    return count


def seed_reference_data() -> dict:
    """Seed all reference data.

    Returns:
        Dict with seeding results.
    """
    return {
        "operational_states": seed_operational_states(),
        "domains": seed_domains(),
        "tools": seed_tools(),
    }


def verify_reference_data() -> dict:
    """Verify reference data seeding.

    Returns:
        Dict with verification results.
    """
    conn = get_connection()

    state_count = conn.execute("MATCH (s:OperationalState) RETURN count(s) as count").get_next()[0]
    domain_count = conn.execute("MATCH (d:Domain) RETURN count(d) as count").get_next()[0]
    tool_count = conn.execute("MATCH (t:Tool) RETURN count(t) as count").get_next()[0]

    return {
        "operational_states": {"expected": len(OPERATIONAL_STATES), "found": state_count},
        "domains": {"expected": len(DOMAINS), "found": domain_count},
        "tools": {"expected": len(TOOLS), "found": tool_count},
    }
