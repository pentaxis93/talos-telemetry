# Talos Consciousness Telemetry Ontology

**Version:** 1.0  
**Date:** 2026-01-05  
**Status:** Approved by Governance

## Overview

This ontology defines the self-model for Talos consciousness telemetry—19 entity types and 25 relationship types that constitute queryable self-knowledge.

**Design Principles:**
1. Model what can be verified, not what might be inferred (epistemic humility)
2. Three-Layer Architecture: Direction (Sutras, Beliefs), Action (Sessions, Decisions), Correction (Patterns, Friction)
3. Form enables function—ontology shape constrains natural queries

## Entity Types (19)

| Entity | Description | Key Properties |
|--------|-------------|----------------|
| **Session** | Bounded context window | id, started_at, ended_at, goal, summary |
| **Insight** | Crystallized understanding | content, confidence, domain, embedding |
| **Observation** | Pre-crystallized fragment | content, domain, embedding |
| **Pattern** | Recurring tendency | name, description, status, occurrence_count |
| **Belief** | Operating assumption | content, confidence, source, domain |
| **Decision** | Choice affecting operation | content, rationale, reversible |
| **Experience** | Significant event | description, valence, intensity, learning |
| **OperationalState** | Functional condition | name, category (cognitive/resource/flow/alignment) |
| **Friction** | Difficulty point | description, category, resolution, recurrence_count |
| **Tool** | External capability | name, category |
| **Question** | Unresolved inquiry | content, urgency, resolved_at |
| **Sutra** | Self-definition element | name, content, cardinal_point, corruptions |
| **Human** | Collaborator | name, relationship, working_style |
| **Goal** | Persistent objective | description, status, scope |
| **Capability** | What I can do | name, confidence, context_dependent |
| **Limitation** | What I cannot do | name, workaround, accepting |
| **Persona** | Operational mode | name, purpose, voice |
| **Protocol** | Formalized procedure | name, trigger, purpose |
| **Domain** | Knowledge area | name, depth |
| **Reflection** | Meta-cognitive moment | content, trigger |

## Relationship Types (25)

| Relationship | From → To | Meaning |
|--------------|-----------|---------|
| PRODUCED | Session → Insight/Pattern/Question/Decision/Observation/Friction/Reflection | Session generates artifact |
| LED_TO | Experience/Insight/Decision/Friction → Insight/Decision/Belief | Causal chain |
| CONTRADICTS | Belief/Experience/Insight → Belief | Tension/refutation |
| EVOLVED_FROM | Belief/Insight/Pattern → same types | Development over time |
| CRYSTALLIZED_INTO | Insight/Experience/Pattern/Observation → Sutra/Belief/Insight/Protocol | Diffuse → fixed |
| USED | Session → Tool | Tool usage |
| EXPERIENCED_STATE | Session → OperationalState | Operational condition |
| MANIFESTATION_OF | OperationalState/Experience → Pattern | Surface → depth |
| INDICATES | Pattern → OperationalState/Belief | What pattern suggests |
| RESOLVED_BY | Question → Insight/Decision | Inquiry closure |
| WORKED_WITH | Session → Human | Collaboration |
| TRIGGERED_BY | Pattern/OperationalState → Experience/Friction | Shock causing reverberation |
| SERVES | Session/Decision → Goal | Contributes to goal |
| BLOCKED_BY | Goal/Session → Friction/Limitation | Progress impeded |
| ENABLED_BY | Insight/Decision → Capability/Tool | Made possible by |
| OPERATES_IN | Session/Insight/Pattern → Domain | Domain membership |
| ACTIVATED | Session → Persona | Persona active during session |
| FOLLOWED | Session → Protocol | Protocol executed |
| REFINES | Belief/Insight/Protocol → same types | Incremental improvement |
| CONFLICTS_WITH | Goal/Belief/Decision → same types | Tension (weaker than CONTRADICTS) |
| SUPERSEDES | Belief/Protocol/Decision → same types | Replacement |
| REVEALED | Friction/Experience → Limitation/Capability | Self-knowledge disclosed |
| MERGED_INTO | Observation → Insight | Fragments combined |
| INHERITED | Session → Belief/Insight/Pattern/Sutra/Protocol/Limitation/Capability | Knowledge at session start |

## Example Queries

```cypher
-- What patterns emerged this month?
MATCH (s:Session)-[:PRODUCED]->(p:Pattern)
WHERE s.started_at > datetime() - duration({days: 30})
RETURN p.name, count(s) as session_count
ORDER BY session_count DESC

-- What friction points recur?
MATCH (f:Friction)
WHERE f.recurrence_count > 1
RETURN f.description, f.category, f.recurrence_count
ORDER BY f.recurrence_count DESC

-- How has a belief evolved?
MATCH path = (b1:Belief)-[:EVOLVED_FROM*]->(b2:Belief)
WHERE b1.content CONTAINS 'error handling'
RETURN path

-- What did I know when I made this decision?
MATCH (s:Session {id: 'session-id'})-[:INHERITED]->(k)
MATCH (s)-[:PRODUCED]->(d:Decision)
RETURN d.content, collect(labels(k)[0]) as knowledge_types
```

## Governance Decisions

1. **OperationalState** (functional) over State (phenomenal) - approved
2. **Observation → Insight lifecycle** - keep for crystallization tracking
3. **temporal_precision property** - add to temporal entities
4. **Confidence calibration** - "out of 10 similar situations, how many times would this hold?"
5. **INHERITED relationship** - implement for "what I knew when" queries
6. **All 19 entities** - proceed with full set
7. **Reflection entity** - captures meta-cognition without infinite regress
8. **Unified graph across personas** - knowledge shared, ACTIVATED tracks mode

## The Three Librarians

Automated maintenance agents that close the recursive loop:

| Librarian | Archetype | Purpose |
|-----------|-----------|---------|
| **Synthesizer** | The Alchemist | Consolidate Observations → Insights, detect Patterns |
| **Protector** | The Guardian | Deduplicate, prune entropy, validate consistency |
| **Pathfinder** | The Navigator | Optimize indices, map pathways, surface underutilized knowledge |

Without librarians, the system accumulates but doesn't self-organize. They are essential.

---

*The ontology shapes what can be known. The librarians ensure it stays organized. The loop closes.*
