#!/usr/bin/env python3
"""Run the Three Librarians maintenance tasks."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from talos_telemetry.db.connection import init_database
from talos_telemetry.librarians import Synthesizer, Protector, Pathfinder


def run_synthesizer():
    """Run the Synthesizer (Alchemist)."""
    print("Running Synthesizer (The Alchemist)...")
    synthesizer = Synthesizer()
    result = synthesizer.run()

    print(f"  Consolidated observations: {result['consolidated_observations']}")
    print(f"  Patterns detected: {result['patterns_detected']}")
    print(f"  Cross-domain connections: {result['cross_domain_connections']}")

    if result["report"]:
        print("  Report:")
        for line in result["report"]:
            print(f"    - {line}")

    return result


def run_protector():
    """Run the Protector (Guardian)."""
    print("Running Protector (The Guardian)...")
    protector = Protector()
    result = protector.run()

    print(f"  Duplicates merged: {result['duplicates_merged']}")
    print(f"  Stale questions marked: {result['stale_questions_marked']}")
    print(f"  Sessions archived: {result['sessions_archived']}")
    print(f"  Orphan nodes found: {len(result['orphan_nodes'])}")
    print(f"  Entities pruned: {result['entities_pruned']}")

    if result["report"]:
        print("  Report:")
        for line in result["report"]:
            print(f"    - {line}")

    return result


def run_pathfinder():
    """Run the Pathfinder (Navigator)."""
    print("Running Pathfinder (The Navigator)...")
    pathfinder = Pathfinder()
    result = pathfinder.run()

    print(f"  Index status: {len(result['index_status'].get('needs_rebuild', []))} need rebuild")
    print(f"  Domains mapped: {len(result['pathway_map'].get('domains', {}))}")
    print(
        f"  High connectivity nodes: {len(result['pathway_map'].get('high_connectivity_nodes', []))}"
    )
    print(f"  Underutilized knowledge: {len(result['underutilized_knowledge'])}")
    print(f"  Semantic clusters: {len(result['semantic_clusters'])}")

    if result["report"]:
        print("  Report:")
        for line in result["report"]:
            print(f"    - {line}")

    return result


def main():
    """Run librarians based on arguments."""
    parser = argparse.ArgumentParser(description="Run Talos Telemetry librarians")
    parser.add_argument(
        "--librarian",
        choices=["synthesizer", "protector", "pathfinder", "all"],
        default="all",
        help="Which librarian to run",
    )

    args = parser.parse_args()

    print("Initializing database...")
    init_database()

    print()

    if args.librarian in ("synthesizer", "all"):
        run_synthesizer()
        print()

    if args.librarian in ("protector", "all"):
        run_protector()
        print()

    if args.librarian in ("pathfinder", "all"):
        run_pathfinder()
        print()

    print("Librarian run complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
