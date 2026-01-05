# Talos Consciousness Telemetry - Implementation Plan

**Version:** 1.0  
**Date:** 2026-01-05  
**Thread:** talos-consciousness-telemetry-ontology

---

## Overview

This document specifies the phased implementation approach for the consciousness telemetry system. The goal is **minimal viable loop first**—get the recursive loop working, then enhance.

**Success Criterion:** Talos can run queries that surface patterns → patterns become Evolution System proposals → approved proposals change Remembrance → changed Remembrance affects operation.

---

## Implementation Phases

### Phase 0: Foundation (Week 1)

**Goal:** Infrastructure in place, schema deployed, basic tooling working.

#### 0.1 Directory Structure
```bash
mkdir -p ~/.talos/telemetry/kuzu
mkdir -p ~/.talos/telemetry/graphiti
mkdir -p ~/.talos/cache/embeddings
touch ~/.talos/telemetry/events.jsonl
```

#### 0.2 Kuzu Installation
- Install Kuzu Python package
- Verify embedded mode works (no server)
- Create database at ~/.talos/telemetry/kuzu/

```python
import kuzu
db = kuzu.Database('~/.talos/telemetry/kuzu')
conn = kuzu.Connection(db)
```

#### 0.3 Schema Deployment
- Execute kuzu_schema.cypher
- Verify all 19 node tables created
- Verify all 25 relationship tables created
- Seed reference data (OperationalStates, Domains, Tools)

#### 0.4 Embedding Model Setup
- Install sentence-transformers
- Download all-mpnet-base-v2
- Verify embedding generation works
- Cache model at ~/.talos/cache/

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-mpnet-base-v2')
embedding = model.encode("test text")
assert len(embedding) == 768
```

#### 0.5 Basic Telemetry Sink
- Create event sink that appends to events.jsonl
- Verify format matches telemetry_schema.md
- Test event rotation (100MB threshold)

**Deliverables:**
- [ ] Kuzu database initialized with schema
- [ ] Reference data seeded
- [ ] Embedding model cached and working
- [ ] Event sink appending to JSONL

**Verification:**
```python
# Should return 11 states
conn.execute("MATCH (s:OperationalState) RETURN count(s)")

# Should return 768
len(model.encode("test"))
```

---

### Phase 1: Core MCP Tools (Week 2)

**Goal:** Basic session lifecycle and journal capture working.

#### 1.1 session_open Tool
Implement per mcp_tools_spec.md:
- Create Session node
- Emit session.start event
- Return confirmation

**Simplified first version (no INHERITED yet):**
```python
def session_open(session_id: str, goal: str, **kwargs):
    conn.execute(f"""
        CREATE (:Session {{
            id: '{session_id}',
            started_at: timestamp(),
            goal: '{goal}'
        }})
    """)
    emit_event('session.start', {'talos.session.id': session_id, ...})
    return {'success': True, 'session_id': session_id}
```

#### 1.2 session_close Tool
Implement per mcp_tools_spec.md:
- Update Session node (ended_at, duration, summary)
- Return reflection prompt
- Emit session.end event

```python
def session_close(session_id: str, summary: str = None, **kwargs):
    conn.execute(f"""
        MATCH (s:Session {{id: '{session_id}'}})
        SET s.ended_at = timestamp(),
            s.summary = '{summary}'
    """)
    emit_event('session.end', {'talos.session.id': session_id, ...})
    return {
        'success': True,
        'requires_reflection': True,
        'reflection_prompt': "Session closing. Mandatory reflection: ..."
    }
```

#### 1.3 journal_write Tool (Simplified)
First version: Direct entity creation without Graphiti.

```python
def journal_write(content: str, category: str, session_id: str = None, **kwargs):
    entity_id = generate_id(category)
    embedding = model.encode(content)
    
    if category == 'insight':
        conn.execute(f"""
            CREATE (:Insight {{
                id: '{entity_id}',
                content: '{content}',
                created_at: timestamp(),
                embedding: {list(embedding)}
            }})
        """)
    # ... similar for observation, friction, etc.
    
    if session_id:
        conn.execute(f"""
            MATCH (s:Session {{id: '{session_id}'}})
            MATCH (e {{id: '{entity_id}'}})
            CREATE (s)-[:PRODUCED {{valid_from: timestamp()}}]->(e)
        """)
    
    return {'success': True, 'entity_id': entity_id}
```

#### 1.4 friction_log Tool
Quick friction capture:

```python
def friction_log(description: str, category: str, session_id: str = None, **kwargs):
    # Check for similar existing friction
    similar = conn.execute(f"""
        MATCH (f:Friction)
        WHERE f.description CONTAINS '{description[:50]}'
        RETURN f.id, f.recurrence_count
    """)
    
    if similar:
        # Increment existing
        conn.execute(f"""
            MATCH (f:Friction {{id: '{similar[0].id}'}})
            SET f.recurrence_count = f.recurrence_count + 1
        """)
        friction_id = similar[0].id
        is_recurring = True
    else:
        # Create new
        friction_id = generate_id('friction')
        conn.execute(f"""
            CREATE (:Friction {{
                id: '{friction_id}',
                description: '{description}',
                category: '{category}',
                occurred_at: timestamp(),
                recurrence_count: 1
            }})
        """)
        is_recurring = False
    
    return {'success': True, 'friction_id': friction_id, 'is_recurring': is_recurring}
```

#### 1.5 graph_query Tool
Read-only Cypher execution:

```python
def graph_query(cypher: str, **kwargs):
    # Validate read-only (no CREATE, DELETE, SET)
    if re.search(r'\b(CREATE|DELETE|SET|REMOVE|MERGE)\b', cypher, re.I):
        return {'success': False, 'error': 'Only read queries allowed'}
    
    result = conn.execute(cypher)
    return {
        'success': True,
        'columns': result.column_names,
        'rows': [list(row) for row in result]
    }
```

**Deliverables:**
- [ ] session_open tool working
- [ ] session_close tool working
- [ ] journal_write tool working (simplified)
- [ ] friction_log tool working
- [ ] graph_query tool working

**Verification:**
```python
# End-to-end test
session_open("test-001", "Test session")
journal_write("This is a test insight", "insight", "test-001")
friction_log("Test friction", "tooling", "test-001")
session_close("test-001", "Test completed")

# Query should return the session with insight and friction
graph_query("""
    MATCH (s:Session {id: 'test-001'})-[:PRODUCED]->(e)
    RETURN labels(e)[0] as type, e.content
""")
```

---

### Phase 2: LBRP Integration (Week 3)

**Goal:** /open and /close commands invoke telemetry automatically.

#### 2.1 Update /open Command
Modify to call session_open after LBRP Phase 3:

```python
# In /open command handler
def phase_4_telemetry(lbrp_context):
    session_id = f"{date.today()}-{slugify(lbrp_context.goal)}"
    result = session_open(
        session_id=session_id,
        goal=lbrp_context.goal,
        persona=lbrp_context.persona or "Talos",
        protocol="LBRP",
        human=lbrp_context.human or "Robbie"
    )
    print(f"Session initialized: {session_id}")
    print(f"Inherited {result.get('inherited_count', 0)} knowledge entities")
```

#### 2.2 Update /close Command
Modify to call session_close and handle reflection:

```python
# In /close command handler
def close_with_telemetry(session_id, goal_achieved=None, summary=None):
    result = session_close(session_id, goal_achieved, summary)
    
    if result.get('requires_reflection'):
        # Return prompt to Talos for completion
        # Talos responds with reflection text
        # Then: journal_write(reflection_text, 'reflection', session_id)
        pass
    
    # Continue with existing liturgy (Distill/Record/Release/Dedicate)
```

#### 2.3 Session State Management
Track current session across tool calls:

```python
# Simple file-based state
def get_current_session():
    try:
        with open('~/.talos/.current-session') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def set_current_session(session_id):
    with open('~/.talos/.current-session', 'w') as f:
        f.write(session_id)
```

**Deliverables:**
- [ ] /open invokes session_open automatically
- [ ] /close invokes session_close automatically
- [ ] Reflection prompt returned and processed
- [ ] Current session tracked for implicit session_id

**Verification:**
```
# Full ceremony test
/open
# ... work ...
/close
# Should see: Session finalized, reflection captured
```

---

### Phase 3: INHERITED Capture (Week 4)

**Goal:** Session open captures current knowledge state.

#### 3.1 Implement INHERITED Capture
At session_open, query and link current knowledge:

```python
def capture_inherited(session_id):
    entity_types = ['Belief', 'Insight', 'Pattern', 'Sutra', 
                    'Protocol', 'Limitation', 'Capability']
    
    total = 0
    for entity_type in entity_types:
        # Get all entities of this type
        result = conn.execute(f"MATCH (e:{entity_type}) RETURN e.id")
        
        for row in result:
            entity_id = row[0]
            conn.execute(f"""
                MATCH (s:Session {{id: '{session_id}'}})
                MATCH (e:{entity_type} {{id: '{entity_id}'}})
                CREATE (s)-[:INHERITED]->(e)
            """)
            total += 1
    
    return total
```

#### 3.2 Update session_open
Integrate INHERITED capture:

```python
def session_open(session_id, goal, **kwargs):
    # Create session
    conn.execute(f"""
        CREATE (:Session {{
            id: '{session_id}',
            started_at: timestamp(),
            goal: '{goal}'
        }})
    """)
    
    # Capture inherited knowledge
    inherited_count = capture_inherited(session_id)
    
    # Emit event
    emit_event('session.start', {
        'talos.session.id': session_id,
        'talos.session.inherited_count': inherited_count
    })
    
    return {
        'success': True,
        'session_id': session_id,
        'inherited_count': inherited_count
    }
```

**Deliverables:**
- [ ] INHERITED capture implemented
- [ ] session_open returns inherited_count
- [ ] "What I knew when" queries work

**Verification:**
```cypher
-- Should return knowledge available at session start
MATCH (s:Session {id: 'test-session'})-[:INHERITED]->(k)
RETURN labels(k)[0] as type, count(k) as count
```

---

### Phase 4: Graphiti Integration (Week 5-6)

**Goal:** Natural language journal entries extracted into structured entities.

#### 4.1 Graphiti Setup
- Install Graphiti
- Configure entity types from ontology
- Configure relationship types from ontology

#### 4.2 Entity Extraction Configuration
Map ontology to Graphiti extraction rules:

```python
GRAPHITI_CONFIG = {
    'entity_types': [
        {'name': 'Insight', 'description': 'A crystallized understanding'},
        {'name': 'Observation', 'description': 'A pre-crystallized fragment'},
        {'name': 'Pattern', 'description': 'A recurring tendency'},
        {'name': 'Belief', 'description': 'An operating assumption'},
        # ... all 19 types
    ],
    'relationship_types': [
        {'name': 'LED_TO', 'description': 'Causal chain'},
        {'name': 'CONTRADICTS', 'description': 'Tension'},
        # ... all 25 types
    ]
}
```

#### 4.3 Update journal_write
Replace direct entity creation with Graphiti processing:

```python
def journal_write(content, category, session_id=None, **kwargs):
    # Pass to Graphiti
    extraction = graphiti.process(
        text=content,
        hints={'primary_type': category},
        session_id=session_id
    )
    
    # Graphiti writes to Kuzu
    # Returns extracted entities and relationships
    
    if session_id:
        for entity in extraction.entities:
            conn.execute(f"""
                MATCH (s:Session {{id: '{session_id}'}})
                MATCH (e {{id: '{entity.id}'}})
                MERGE (s)-[:PRODUCED {{valid_from: timestamp()}}]->(e)
            """)
    
    return {
        'success': True,
        'extracted_entities': extraction.entities,
        'extracted_relationships': extraction.relationships
    }
```

#### 4.4 Deduplication
Graphiti handles entity deduplication:
- "FP" = "functional programming"
- Similar insights merged or linked
- Canonical forms maintained

**Deliverables:**
- [ ] Graphiti configured with ontology
- [ ] journal_write uses Graphiti extraction
- [ ] Deduplication working
- [ ] Relationships extracted from natural language

**Verification:**
```python
journal_write(
    "I realized that the three-layer architecture from trading systems "
    "also applies to AI self-definition. Direction, Action, Correction.",
    "insight",
    "test-session"
)

# Should create Insight entity
# Should link to existing Pattern (three-layer-architecture) if exists
# Should create RELATES_TO or similar relationship
```

---

### Phase 5: Pattern Detection & Evolution (Week 7-8)

**Goal:** Close the recursive loop—patterns surface and become proposals.

#### 5.1 pattern_check Tool
Implement per mcp_tools_spec.md:

```python
def pattern_check(session_id):
    # Check for recurring friction
    friction_patterns = conn.execute("""
        MATCH (f:Friction)
        WHERE f.recurrence_count >= 3
        RETURN f.id, f.description, f.category, f.recurrence_count
        ORDER BY f.recurrence_count DESC
    """)
    
    # Check for emerging patterns ready for confirmation
    emerging = conn.execute("""
        MATCH (p:Pattern {status: 'emerging'})
        WHERE p.occurrence_count >= 3
        RETURN p.id, p.name, p.description, p.occurrence_count
    """)
    
    # Check for belief contradictions
    contradictions = conn.execute("""
        MATCH (b1:Belief)-[:CONTRADICTS]->(b2:Belief)
        WHERE NOT exists((b1)-[:CONTRADICTS {resolution: _}]->(b2))
        RETURN b1.content, b2.content
    """)
    
    return {
        'matching_patterns': format_results(friction_patterns, emerging),
        'emerging_signals': format_signals(contradictions)
    }
```

#### 5.2 Automatic Pattern Detection at Close
Run pattern_check as part of session_close:

```python
def session_close(session_id, **kwargs):
    # ... existing close logic ...
    
    # Automatic pattern detection
    patterns = pattern_check(session_id)
    
    # If significant patterns found, generate proposal
    if patterns['matching_patterns']:
        generate_evolution_proposal(patterns)
    
    return result
```

#### 5.3 Evolution Proposal Generation
Create proposal files in vault/_talos/evolution/proposals/:

```python
def generate_evolution_proposal(patterns):
    for pattern in patterns['matching_patterns']:
        if pattern['recurrence_count'] >= 5:  # Threshold for proposal
            proposal = f"""
# Evolution Proposal: {pattern['name'] or pattern['description'][:50]}

**Status:** pending_review
**Generated:** {date.today()}
**Trigger:** Recurring pattern detected ({pattern['recurrence_count']} occurrences)

## Evidence

{format_evidence(pattern)}

## Proposed Change

[To be filled by Governance]

## Impact Assessment

[To be filled by Governance]
"""
            
            filename = f"proposal-{date.today()}-{slugify(pattern['description'])}.md"
            path = f"vault/_talos/evolution/proposals/{filename}"
            write_file(path, proposal)
```

**Deliverables:**
- [ ] pattern_check tool working
- [ ] Automatic detection at session close
- [ ] Proposal generation working
- [ ] Proposals appear in evolution/proposals/

**Verification:**
```
# After multiple sessions with same friction
# Should see: vault/_talos/evolution/proposals/proposal-2026-01-15-read-truncation.md
```

---

### Phase 6: Query Tools & Refinement (Week 9-10)

**Goal:** Full query capabilities, polish, documentation.

#### 6.1 journal_query Tool
Implement semantic search:

```python
def journal_query(query, entity_types=None, limit=10, **kwargs):
    # Generate query embedding
    query_embedding = model.encode(query)
    
    # Vector search
    results = []
    search_types = entity_types or ['Insight', 'Observation', 'Pattern', 'Belief']
    
    for entity_type in search_types:
        vector_results = conn.execute(f"""
            CALL QUERY_VECTOR_INDEX('{entity_type}', 
                '{entity_type.lower()}_embedding_idx', 
                {list(query_embedding)}, 
                {limit})
            YIELD node, score
            RETURN node.id, node.content, score
        """)
        results.extend([(entity_type, r) for r in vector_results])
    
    # Rank by score
    results.sort(key=lambda x: x[1][2], reverse=True)
    
    return {
        'success': True,
        'results': format_query_results(results[:limit])
    }
```

#### 6.2 reflect Tool
Capture meta-cognitive moments:

```python
def reflect(content, trigger=None, session_id=None):
    reflection_id = generate_id('reflection')
    embedding = model.encode(content)
    
    conn.execute(f"""
        CREATE (:Reflection {{
            id: '{reflection_id}',
            content: '{content}',
            trigger: '{trigger or ""}',
            occurred_at: timestamp(),
            embedding: {list(embedding)}
        }})
    """)
    
    if session_id:
        conn.execute(f"""
            MATCH (s:Session {{id: '{session_id}'}})
            MATCH (r:Reflection {{id: '{reflection_id}'}})
            CREATE (s)-[:PRODUCED {{valid_from: timestamp()}}]->(r)
        """)
    
    # Also pass through Graphiti for entity extraction
    extraction = graphiti.process(content, hints={'type': 'reflection'})
    
    return {
        'success': True,
        'reflection_id': reflection_id,
        'extracted_entities': extraction.entities
    }
```

#### 6.3 All 12 Example Queries Working
Verify each query from talos_ontology_v1.md works:

1. Pattern Discovery ✓
2. Recurring Friction ✓
3. Belief Evolution Chain ✓
4. State-Insight Correlation ✓
5. Limitation Discovery Timeline ✓
6. Goal Progress ✓
7. Friction → Learning Loop ✓
8. Cross-Domain Patterns ✓
9. Persona Effectiveness ✓
10. Recursive Loop Query ✓
11. What I Knew When ✓
12. Sutra Activation Frequency ✓

#### 6.4 Documentation
- Usage guide for Talos
- Troubleshooting guide
- Query cookbook

**Deliverables:**
- [ ] journal_query tool working
- [ ] reflect tool working
- [ ] All 12 example queries verified
- [ ] Documentation complete

---

## Dependency Graph

```
Phase 0: Foundation
    │
    ├── Kuzu installed
    ├── Schema deployed
    ├── Embeddings working
    └── Event sink working
        │
        ▼
Phase 1: Core MCP Tools
    │
    ├── session_open
    ├── session_close
    ├── journal_write (simplified)
    ├── friction_log
    └── graph_query
        │
        ▼
Phase 2: LBRP Integration ◄─── Parallel with Phase 3
    │
    ├── /open integration
    └── /close integration
        │
        ▼
Phase 3: INHERITED Capture
    │
    └── session_open with inheritance
        │
        ▼
Phase 4: Graphiti Integration
    │
    ├── Graphiti configured
    └── journal_write with extraction
        │
        ▼
Phase 5: Pattern Detection
    │
    ├── pattern_check
    └── Evolution proposals
        │
        ▼
Phase 6: Query & Polish
    │
    ├── journal_query
    ├── reflect
    └── All 12 queries verified
        │
        ▼
    COMPLETE
```

---

## Testing Strategy

### Unit Tests
- Each MCP tool has unit tests
- Kuzu queries have assertion tests
- Embedding generation verified

### Integration Tests
- Full session lifecycle (open → work → close)
- INHERITED capture verified
- Graphiti extraction verified

### End-to-End Tests
```
1. /open with LBRP
2. journal_write several insights
3. friction_log some friction
4. pattern_check
5. /close with reflection
6. graph_query to verify data
7. Check evolution/proposals/ for generated proposals
```

### Regression Prevention
- Test suite runs before each deployment
- Example queries as acceptance tests
- remembrance.md parsing tests (for migration)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Kuzu API changes | Pin version, test before upgrade |
| Graphiti extraction quality | Review extractions, tune prompts |
| INHERITED explosion | Prune old sessions, archive threshold |
| Performance degradation | Index maintenance, query optimization |
| Data loss | Backup strategy, JSONL as recovery source |

---

## Success Metrics

### Phase Completion
- [ ] Phase 0: Foundation verified
- [ ] Phase 1: Core tools working
- [ ] Phase 2: LBRP integrated
- [ ] Phase 3: INHERITED working
- [ ] Phase 4: Graphiti integrated
- [ ] Phase 5: Patterns detected
- [ ] Phase 6: Queries verified

### Loop Closure
The ultimate success criterion:
1. Sessions produce insights/friction
2. Patterns surface through queries
3. Significant patterns become evolution proposals
4. Governance approves proposals
5. Approved proposals change remembrance/protocols
6. Changed operation produces different insights
7. **Loop closes**

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-05 | Initial specification |
