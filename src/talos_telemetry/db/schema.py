"""Schema deployment for Kuzu database."""

from pathlib import Path

from talos_telemetry.db.connection import get_connection


def get_schema_path() -> Path:
    """Get path to schema file."""
    # Schema is in docs/ relative to package root
    package_root = Path(__file__).parent.parent.parent.parent
    return package_root / "docs" / "kuzu_schema.cypher"


def deploy_schema(schema_path: Path | None = None) -> dict:
    """Deploy schema to Kuzu database.

    Args:
        schema_path: Optional path to schema file.

    Returns:
        Dict with deployment results.
    """
    conn = get_connection()
    path = schema_path or get_schema_path()

    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    # Read schema file
    with open(path) as f:
        schema_content = f.read()

    # Split into individual statements
    # Skip comments and empty lines
    statements = []
    current_statement = []

    for line in schema_content.split("\n"):
        stripped = line.strip()

        # Skip comments and empty lines
        if stripped.startswith("--") or not stripped:
            continue

        current_statement.append(line)

        # Statement ends with semicolon
        if stripped.endswith(";"):
            statements.append("\n".join(current_statement))
            current_statement = []

    # Execute each statement
    results = {"node_tables": 0, "rel_tables": 0, "indexes": 0, "data": 0, "errors": []}

    for statement in statements:
        try:
            conn.execute(statement)

            # Track what was created
            upper_stmt = statement.upper()
            if "CREATE NODE TABLE" in upper_stmt:
                results["node_tables"] += 1
            elif "CREATE REL TABLE" in upper_stmt:
                results["rel_tables"] += 1
            elif "CREATE_VECTOR_INDEX" in upper_stmt or "CREATE_FTS_INDEX" in upper_stmt:
                results["indexes"] += 1
            elif "CREATE (" in upper_stmt:
                results["data"] += 1

        except Exception as e:
            error_msg = str(e)
            # Ignore "already exists" errors for idempotency
            if "already exists" not in error_msg.lower():
                results["errors"].append(
                    {
                        "statement": statement[:100] + "..." if len(statement) > 100 else statement,
                        "error": error_msg,
                    }
                )

    return results


def verify_schema() -> dict:
    """Verify schema deployment.

    Returns:
        Dict with verification results.
    """
    conn = get_connection()

    # Check node tables
    node_tables = conn.execute("CALL show_tables() RETURN *").get_as_df()

    expected_nodes = [
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
    ]

    found_nodes = set(node_tables["name"].tolist()) if not node_tables.empty else set()

    return {
        "expected_nodes": len(expected_nodes),
        "found_nodes": len(found_nodes & set(expected_nodes)),
        "missing_nodes": list(set(expected_nodes) - found_nodes),
        "tables": node_tables.to_dict("records") if not node_tables.empty else [],
    }
