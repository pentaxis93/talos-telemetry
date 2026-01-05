#!/usr/bin/env python3
"""Deploy Kuzu schema for Talos Telemetry."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from talos_telemetry.db.connection import init_database, get_connection
from talos_telemetry.db.schema import deploy_schema, verify_schema


def main():
    """Deploy schema and verify."""
    print("Initializing database...")
    init_database()

    print("Deploying schema...")
    result = deploy_schema()

    print(f"\nSchema deployment results:")
    print(f"  Node tables: {result['node_tables']}")
    print(f"  Relationship tables: {result['rel_tables']}")
    print(f"  Indexes: {result['indexes']}")
    print(f"  Reference data: {result['data']}")

    if result["errors"]:
        print(f"\nErrors ({len(result['errors'])}):")
        for error in result["errors"]:
            print(f"  - {error['error'][:100]}")

    print("\nVerifying schema...")
    verify = verify_schema()

    print(f"\nVerification results:")
    print(f"  Expected nodes: {verify['expected_nodes']}")
    print(f"  Found nodes: {verify['found_nodes']}")

    if verify["missing_nodes"]:
        print(f"  Missing: {verify['missing_nodes']}")
    else:
        print("  All node tables present!")

    return 0 if not result["errors"] and not verify["missing_nodes"] else 1


if __name__ == "__main__":
    sys.exit(main())
