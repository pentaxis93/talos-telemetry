#!/usr/bin/env python3
"""Seed reference data for Talos Telemetry."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from talos_telemetry.db.connection import init_database
from talos_telemetry.db.seed import seed_reference_data, verify_reference_data


def main():
    """Seed reference data and verify."""
    print("Initializing database...")
    init_database()

    print("Seeding reference data...")
    result = seed_reference_data()

    print(f"\nSeeding results:")
    print(f"  Operational states: {result['operational_states']}")
    print(f"  Domains: {result['domains']}")
    print(f"  Tools: {result['tools']}")

    print("\nVerifying reference data...")
    verify = verify_reference_data()

    print(f"\nVerification results:")
    for category, counts in verify.items():
        status = "OK" if counts["expected"] == counts["found"] else "MISSING"
        print(f"  {category}: {counts['found']}/{counts['expected']} [{status}]")

    # Check if all data is present
    all_ok = all(v["expected"] == v["found"] for v in verify.values())

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
