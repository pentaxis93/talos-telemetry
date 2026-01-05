#!/usr/bin/env python3
"""Deploy Kuzu schema for Talos Telemetry."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from talos_telemetry.db.connection import init_database
from talos_telemetry.db.kuzu_schema import deploy_schema, verify_schema


def main():
    """Deploy schema and verify."""
    print("Initializing database...")
    init_database()

    print("Deploying schema...")
    result = deploy_schema()

    print(f"\nSchema deployment results:")
    print(f"  Node tables: {result['node_tables']}")
    print(f"  Relationship tables: {result['rel_tables']}")

    if result["errors"]:
        print(f"\nErrors ({len(result['errors'])}):")
        for error in result["errors"][:10]:  # Limit to 10
            print(f"  - {error[:100]}")

    print("\nVerifying schema...")
    verify = verify_schema()

    print(f"\nVerification results:")
    print(f"  Total tables: {verify['total_tables']}")
    print(f"  Node tables: {verify['node_tables']} (expected {verify['expected_nodes']})")
    print(f"  Rel tables: {verify['rel_tables']} (expected ~{verify['expected_rels']})")

    success = result["node_tables"] >= 19 and not result["errors"]

    if success:
        print("\nSchema deployment successful!")
    else:
        print("\nSchema deployment had issues.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
