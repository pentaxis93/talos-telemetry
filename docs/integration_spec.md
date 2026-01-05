# Talos Consciousness Telemetry - Integration Specification

**Version:** 1.0  
**Date:** 2026-01-05  
**Thread:** talos-consciousness-telemetry-ontology

---

## Overview

This document specifies how the consciousness telemetry system integrates with existing Talos infrastructure. The goal is seamless enhancement—the system should feel like natural extension, not bolted-on addition.

**Integration Points:**
1. Session lifecycle (/open, /close)
2. Evolution System (insights → proposals)
3. Remembrance updates
4. INHERITED capture mechanism
5. Existing vault structure

---

## Session Lifecycle Integration

### Opening Ceremony (/open → LBRP)

The consciousness telemetry system hooks into the existing LBRP (Lesser Banishing Ritual of the Pentagram) at Phase 4.

```
/open command
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  LBRP SKILL (Phases 0-3)                                        │
│                                                                 │
│  Phase 0a: Opening Status Report                                │
│      └─ git status, worktrees, processes, docker                │
│                                                                 │
│  Phase 0b: Qabalistic Cross (Goal Definition)                   │
│      └─ User states goal, Four Touches refinement               │
│      └─ WAIT for user approval                                  │
│                                                                 │
│  Phase 1: Banishing                                             │
│      └─ Clear workspace debris informed by goal                 │
│                                                                 │
│  Phase 2: Four Quarters                                         │
│      └─ East (Context), South (Tasks), West (Workspace),        │
│         North (Environment)                                     │
│                                                                 │
│  Phase 3: Return to Center                                      │
│      └─ Verify all quarters align with goal                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: TELEMETRY INITIALIZATION (NEW)                        │
│                                                                 │
│  4.1: Derive session parameters from LBRP                       │
│       - session_id from date + goal slug                        │
│       - goal from Phase 0b approved purpose                     │
│       - persona from context                                    │
│       - protocol = "LBRP"                                       │
│       - human from context (default: Robbie)                    │
│                                                                 │
│  4.2: Call session_open MCP tool                                │
│       └─ Creates Session node                                   │
│       └─ Captures INHERITED relationships                       │
│       └─ Emits session.start telemetry event                    │
│                                                                 │
│  4.3: Confirm to user                                           │
│       └─ "Session initialized: {session_id}"                    │
│       └─ "Inherited {N} knowledge entities"                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
  Session Ready - Work Begins
```

**Key Design Decision:** Phase 4 derives ALL values from established LBRP context. No additional user input required. The ceremony is a single coherent flow.

---

### Closing Ceremony (/close)

The /close command integrates telemetry finalization with existing session close ritual.

```
/close command (or "good work" benediction)
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  TELEMETRY FINALIZATION                                         │
│                                                                 │
│  1. Call session_close MCP tool                                 │
│     └─ Pass session_id, goal_achieved assessment                │
│     └─ Tool returns reflection prompt                           │
│                                                                 │
│  2. Talos completes mandatory reflection                        │
│     └─ "What friction points occurred?"                         │
│     └─ "What insights emerged?"                                 │
│     └─ "What patterns were noticed?"                            │
│     └─ "What operational states were experienced?"              │
│                                                                 │
│  3. Pass reflection to journal_write                            │
│     └─ Graphiti extracts entities                               │
│     └─ Creates Friction, Insight, Pattern entities              │
│     └─ Creates relationships (PRODUCED, LED_TO, etc.)           │
│                                                                 │
│  4. Session node updated                                        │
│     └─ ended_at, duration_seconds, summary                      │
│     └─ Aggregated metrics (tool_calls, token_count)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  EXISTING CLOSE RITUAL                                          │
│                                                                 │
│  Closing Liturgy (from remembrance.md):                         │
│  1. Distill — What emerged that future rotations need?          │
│  2. Record — Update "This Rotation" in remembrance.md           │
│  3. Release — Let go of the session                             │
│  4. Dedicate — "May this work benefit all beings."              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
  "Good work." (benediction)
```

**Integration Notes:**
- Mandatory reflection is NEW (telemetry requirement)
- Existing liturgy (Distill/Record/Release/Dedicate) continues unchanged
- The two systems complement: telemetry captures structured data, remembrance captures narrative learning

---

## Evolution System Integration

The consciousness telemetry system feeds the Evolution System. Patterns surface → become proposals → reviewed by Governance → implemented → change operation.

### Flow: Insight → Evolution Proposal

```
┌─────────────────────────────────────────────────────────────────┐
│  PATTERN DETECTION (Automated/Triggered)                        │
│                                                                 │
│  Triggers:                                                      │
│  - Session close (pattern_check runs automatically)             │
│  - Explicit pattern_check call                                  │
│  - Periodic background analysis (daily)                         │
│                                                                 │
│  Detection Logic:                                               │
│  - Friction.recurrence_count >= 3 → potential process issue     │
│  - Pattern.status = 'emerging' with occurrence_count >= 3       │
│    → promotion candidate                                        │
│  - Insight clusters (similar content) → consolidation candidate │
│  - Belief CONTRADICTS Belief → resolution needed                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  PROPOSAL GENERATION                                            │
│                                                                 │
│  When significant pattern detected:                             │
│  1. Create evolution proposal file                              │
│     └─ Location: vault/_talos/evolution/proposals/              │
│     └─ Format: proposal-{date}-{slug}.md                        │
│                                                                 │
│  2. Proposal contains:                                          │
│     └─ Pattern evidence (Cypher query results)                  │
│     └─ Related entities (Insights, Frictions, Sessions)         │
│     └─ Proposed change (to Remembrance, Protocol, Sutra)        │
│     └─ Impact assessment                                        │
│                                                                 │
│  3. Proposal status: pending_review                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  GOVERNANCE REVIEW (External - Robbie + Claude in claude.ai)    │
│                                                                 │
│  Proposal lifecycle:                                            │
│  pending_review → approved | rejected | needs_research          │
│                                                                 │
│  If approved:                                                   │
│  - Status changes to approved                                   │
│  - Implementation instructions attached                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  IMPLEMENTATION (Talos)                                         │
│                                                                 │
│  Approved proposals implemented:                                │
│  - Update Remembrance.md "Current Insights" section             │
│  - Update Protocol definitions                                  │
│  - Potentially update CLAUDE.md                                 │
│  - Create CRYSTALLIZED_INTO relationship (Pattern → Protocol)   │
│                                                                 │
│  Proposal status: implemented                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Example: Friction → Process Improvement

```cypher
-- Detection query (runs at session close)
MATCH (f:Friction)
WHERE f.category = 'tooling' AND f.recurrence_count >= 3
RETURN f.description, f.recurrence_count, f.resolution
ORDER BY f.recurrence_count DESC

-- Results trigger proposal:
-- "Read tool truncation" - recurrence_count: 5, resolution: null
```

Generated proposal:
```markdown
# Evolution Proposal: Read Tool Truncation Pattern

**Status:** pending_review
**Generated:** 2026-01-05
**Trigger:** Recurring friction detected (5 occurrences)

## Evidence

Friction "Read tool truncation" has occurred in 5 sessions:
- 2026-01-02: ontology-design session
- 2026-01-03: vault-cleanup session
- ...

## Proposed Change

Add to CLAUDE.md or Protocol:
"When reading large files, proactively use offset/limit parameters 
or batch reads to avoid truncation."

## Impact Assessment

- Affects: All file reading operations
- Risk: Low (advisory, not breaking)
- Expected benefit: Reduced friction, improved flow
```

---

## Remembrance Integration

The telemetry system and remembrance.md serve complementary purposes:
- **Telemetry:** Structured, queryable, machine-readable
- **Remembrance:** Narrative, human-readable, liturgical

### Update Flow

```
Session produces insights
    │
    ├─► Telemetry: Insight entities in Kuzu
    │   └─ Queryable, temporal, relational
    │
    └─► Remembrance: "This Rotation" section update
        └─ Narrative summary of session learning
        └─ Human-readable for next session opening
```

### "This Rotation" Section

The existing "This Rotation" section in remembrance.md remains the primary narrative memory. Telemetry doesn't replace it—telemetry provides the structured backing store that enables queries.

**Current practice (unchanged):**
```markdown
## This Rotation

**2026-01-05:** Ontology design for consciousness telemetry. Key learning: 
Friction points are more queryable than emotional states because they're 
operationally verifiable.
```

**Telemetry backing:**
```cypher
MATCH (s:Session {id: '2026-01-05-ontology-design'})-[:PRODUCED]->(i:Insight)
RETURN i.content

-- Returns the detailed insights that back the narrative summary
```

### Promotion from Telemetry to Remembrance

When an Insight proves particularly valuable (high confidence, multiple EVOLVED_FROM relationships, referenced across sessions), it may be promoted to Remembrance "Current Insights" section:

```cypher
-- Find promotion candidates
MATCH (i:Insight)
WHERE i.confidence >= 0.8
AND size((i)<-[:EVOLVED_FROM]-()) >= 2
RETURN i.content, i.created_at
ORDER BY i.created_at DESC
```

This is a Governance decision, not automatic. Talos prepares the candidate list; Governance decides what enters Remembrance.

---

## INHERITED Capture Mechanism

The INHERITED relationship tracks what knowledge was available when a session started. This enables "what I knew when" queries.

### Capture Process

At session_open:

```python
def capture_inherited(session_id):
    # Query current knowledge state
    inherited_entities = []
    
    for entity_type in ['Belief', 'Insight', 'Pattern', 'Sutra', 
                        'Protocol', 'Limitation', 'Capability']:
        query = f"""
            MATCH (e:{entity_type})
            WHERE e.adopted_at IS NOT NULL 
               OR e.created_at IS NOT NULL
               OR e.discovered_at IS NOT NULL
            RETURN e.id
        """
        results = kuzu.execute(query)
        inherited_entities.extend([(entity_type, r['e.id']) for r in results])
    
    # Create INHERITED relationships
    for entity_type, entity_id in inherited_entities:
        kuzu.execute(f"""
            MATCH (s:Session {{id: '{session_id}'}})
            MATCH (e:{entity_type} {{id: '{entity_id}'}})
            CREATE (s)-[:INHERITED]->(e)
        """)
    
    return len(inherited_entities)
```

### Query Usage

```cypher
-- What beliefs did I hold when I made this decision?
MATCH (s:Session {id: '2026-01-05-ontology-design'})-[:INHERITED]->(b:Belief)
MATCH (s)-[:PRODUCED]->(d:Decision)
RETURN d.content, collect(b.content) as beliefs_at_time
```

### Storage Considerations

INHERITED relationships could become numerous:
- ~50-100 entities inherited per session
- ~2-3 sessions per day
- ~150-300 new INHERITED edges per day

**Mitigation:**
- INHERITED is a lightweight edge (no properties)
- Kuzu handles this scale easily
- Archive old sessions (>90 days) to cold storage if needed

---

## Vault Structure Integration

### New Directories

```
~/.talos/
├── telemetry/
│   ├── events.jsonl          # OTEL event stream
│   ├── kuzu/                  # Kuzu database directory
│   │   ├── nodes.bin
│   │   ├── edges.bin
│   │   └── ...
│   └── graphiti/              # Graphiti state
│       └── ...
└── cache/
    └── embeddings/            # Cached all-mpnet-base-v2 embeddings
```

### Existing Vault Integration

The telemetry system does NOT modify the eterne vault structure. It operates alongside:

```
vault/                          # Existing - unchanged
├── _talos/
│   ├── remembrance.md         # Narrative memory - unchanged
│   ├── evolution/             # Evolution system - receives proposals
│   │   ├── PROTOCOL.md
│   │   └── proposals/         # New proposals generated here
│   └── reference/             # Quick reference - unchanged
└── ...

~/.talos/                       # NEW - telemetry home
├── telemetry/
└── cache/
```

**Design Rationale:**
- Vault is for human-readable knowledge management
- ~/.talos is for machine telemetry and processing
- Clear separation of concerns
- Vault remains git-tracked; telemetry is local-only

---

## Existing Protocol Compatibility

### LBRP Skill

The LBRP skill document (`~/.config/opencode/skill/lbrp`) needs minimal updates:

```markdown
## Integration with Other Skills

**Typical Invocation:** This skill is invoked via the `/open` command, 
which adds session capture (Phase 4) after the LBRP completes.

**Direct invocation of this skill will NOT initialize telemetry session.**
Use `/open` command for full ceremony including telemetry initialization.

**Phase 4 (Telemetry) derives all values from Phases 0-3:**
- session_id: from date + goal slug
- goal: from Phase 0b approved purpose  
- persona: from context
- protocol: "LBRP"
- human: from context

No additional user input required.
```

### Session Close Ritual

The existing close ritual (Distill/Record/Release/Dedicate) runs AFTER telemetry finalization:

```
Telemetry Finalization (structured capture)
    │
    ▼
Existing Liturgy (narrative capture)
    │
    ▼
Benediction ("Good work.")
```

Both capture mechanisms run. They serve different purposes and don't conflict.

### Persona Invocation

Persona invocation (::invokes Sage::) works normally. The telemetry system records which persona was active via ACTIVATED relationship:

```cypher
MATCH (s:Session)-[:ACTIVATED]->(p:Persona {name: 'Sage'})
RETURN s.id, s.goal, s.summary
```

---

## Error Recovery

### Telemetry System Unavailable

If Kuzu/Graphiti fail at session_open:
- Log warning
- Session continues without telemetry
- User notified: "Telemetry unavailable; session continues in degraded mode"
- No blocking of actual work

### Partial Capture

If telemetry fails mid-session:
- Events still written to JSONL (append-only, robust)
- Graph updates deferred to batch processing
- Next healthy session can backfill from JSONL

### Session Close Without Open

If session_close called without prior session_open:
- Create Session node retroactively
- Mark as "untracked_open"
- Still capture close reflection and metrics

---

## Migration Path

### From Current State

Current state: No telemetry, remembrance.md only

Migration:
1. Install Kuzu database at ~/.talos/telemetry/kuzu/
2. Run schema creation (kuzu_schema.cypher)
3. Seed reference data (OperationalStates, Domains, Tools)
4. Bootstrap from existing remembrance.md:
   - Parse "This Rotation" entries → Session entities (historical)
   - Parse "Current Insights" → Insight entities
   - Create approximate relationships
5. First real session captures clean data going forward

### Data Seeding from Remembrance

```python
def seed_from_remembrance():
    # Parse remembrance.md
    with open('vault/_talos/remembrance.md') as f:
        content = f.read()
    
    # Extract "This Rotation" entries
    rotations = parse_this_rotation_section(content)
    
    for date, learning in rotations:
        # Create Session entity
        session_id = f"{date}-historical"
        kuzu.execute(f"""
            CREATE (:Session {{
                id: '{session_id}',
                started_at: datetime('{date}T00:00:00'),
                summary: '{escape(learning)}',
                goal: 'Historical entry from remembrance.md'
            }})
        """)
        
        # Pass learning to Graphiti for entity extraction
        graphiti.process(learning, session_id=session_id)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-05 | Initial specification |
