"""Librarians module - automated graph maintenance agents.

The Three Librarians:
- Synthesizer (Alchemist): Consolidates and synthesizes understanding
- Protector (Guardian): Protects integrity and prunes entropy
- Pathfinder (Navigator): Maps pathways and optimizes retrieval
"""

from talos_telemetry.librarians.pathfinder import Pathfinder
from talos_telemetry.librarians.protector import Protector
from talos_telemetry.librarians.synthesizer import Synthesizer

__all__ = ["Synthesizer", "Protector", "Pathfinder"]
