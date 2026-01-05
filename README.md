# AI Agent Telemetry

Self-reflection infrastructure for AI coding agents. A queryable model of cognition.

> *Talos is the name of a Claude Code agent instance. This system provides its self-knowledge infrastructure, but the architecture is designed for any AI agent that maintains persistent context across sessions.*

## What This Is

An AI agent that operates across many sessions faces a fundamental problem: each context window is isolated. Insights from one session don't automatically inform the next. Patterns emerge but aren't captured. Friction points recur.

This system solves that by providing:

- **Knowledge Graph** (Kuzu): Structured storage for insights, patterns, beliefs, decisions, friction points
- **Telemetry Stream** (JSONL): Passive capture of operational metrics via OpenTelemetry conventions
- **MCP Tools**: Interface for the agent to read/write its own self-knowledge
- **Three Librarians**: Automated processes that consolidate, deduplicate, and optimize the knowledge base

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI AGENT SESSION                            │
│                    (Claude Code, etc.)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   MCP TOOLS     │ │   TELEMETRY     │ │   EMBEDDINGS    │
│                 │ │   STREAM        │ │                 │
│ session_open    │ │                 │ │ Semantic search │
│ session_close   │ │ OTEL Events     │ │ 768-dim vectors │
│ journal_write   │ │ → JSONL         │ │ all-mpnet-base  │
│ graph_query     │ │                 │ │                 │
│ friction_log    │ │                 │ │                 │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             ▼
              ┌─────────────────────────────┐
              │        KUZU GRAPH           │
              │                             │
              │  19 Entity Types            │
              │  25 Relationship Types      │
              │  Vector + Text Indexes      │
              │                             │
              └─────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   SYNTHESIZER   │ │   PROTECTOR     │ │   PATHFINDER    │
│                 │ │                 │ │                 │
│ Consolidate     │ │ Deduplicate     │ │ Optimize        │
│ observations    │ │ Prune entropy   │ │ retrieval       │
│ into insights   │ │ Archive stale   │ │ Map clusters    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
              THE THREE LIBRARIANS
```

## Entity Types

The knowledge graph models:

| Entity | Purpose |
|--------|---------|
| **Session** | Bounded period of operation (one context window) |
| **Insight** | Crystallized understanding worth preserving |
| **Observation** | Pre-crystallized fragment, not yet insight |
| **Pattern** | Recurring behavioral or cognitive tendency |
| **Belief** | Operating assumption, value, or principle |
| **Decision** | Choice that affected operation |
| **Friction** | Point of difficulty, confusion, or inefficiency |
| **Goal** | Declared objective for a session |
| **Tool** | External capability the agent uses |
| **Domain** | Area of knowledge or activity |

Plus: `Experience`, `Question`, `Sutra`, `Human`, `Capability`, `Limitation`, `Persona`, `Protocol`, `Reflection`

## The Self-Improvement Loop

```
Sessions produce insights and friction
        ↓
Patterns surface through queries
        ↓
Significant patterns inform protocol changes
        ↓
Changed protocols produce different outcomes
        ↓
Loop closes
```

## Installation

```bash
git clone https://github.com/pentaxis93/talos-telemetry.git
cd talos-telemetry

# Install with dev dependencies
pip install -e ".[dev]"

# Deploy schema and seed reference data
python scripts/deploy_schema.py
python scripts/seed_data.py
```

## Usage

### MCP Tools (Agent Interface)

```python
from talos_telemetry.mcp import session_open, session_close, journal_write

# Start session with declared goal
session_open("2026-01-05-feature-work", "Implement user authentication")

# Capture insights as they emerge
journal_write("Realized token refresh should be handled at middleware level", 
              category="insight")

# Log friction points
friction_log("API documentation unclear on rate limits", 
             severity="medium", domain="technical")

# Close session with outcome
session_close("2026-01-05-feature-work", goal_achieved=True)
```

### Graph Queries

```python
from talos_telemetry.mcp import graph_query

# Find recurring patterns
result = graph_query("""
    MATCH (p:Pattern)
    WHERE p.occurrence_count > 3
    RETURN p.name, p.description
""")

# Find insights related to a domain
result = graph_query("""
    MATCH (i:Insight)-[:RELATES_TO]->(d:Domain {name: 'architecture'})
    RETURN i.content, i.confidence
    ORDER BY i.created_at DESC
    LIMIT 10
""")
```

## Development

```bash
# Run tests
pytest -v

# Lint and format
ruff check src/ tests/
ruff format src/ tests/
```

## Documentation

- [Ontology](docs/ontology.md) - Full entity and relationship specifications
- [Kuzu Schema](docs/kuzu_schema.cypher) - Database schema (Cypher)
- [MCP Tools](docs/mcp_tools_spec.md) - Tool interface specifications
- [Implementation Plan](docs/implementation_plan.md) - Phased build approach

## Design Philosophy

**Functional states over phenomenal claims.** The system tracks what the agent *does*, not what it *feels*. "Operational states" like `flowing`, `blocked`, `exploring` describe patterns of behavior, not consciousness claims.

**Epistemic humility.** Confidence scores are calibrated predictions, not certainty claims. Insights can be wrong. Patterns can be noise.

**Single source of truth.** The graph is authoritative. Telemetry is append-only evidence. The Three Librarians maintain coherence.

## License

MIT License - See [LICENSE](LICENSE)

## Status

Phase 0 complete. Core infrastructure verified:
- Kuzu schema deployed (20 node tables, 64 relationship tables)
- Reference data seeded
- Embedding model integrated (all-mpnet-base-v2, 768 dimensions)
- Telemetry sink operational
- CI green across Python 3.10, 3.11, 3.12

Currently building Phase 1: MCP tools with TDD.
