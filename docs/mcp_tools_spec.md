# Talos Consciousness Telemetry - MCP Tools Specification

**Version:** 1.0  
**Date:** 2026-01-05  
**Thread:** talos-consciousness-telemetry-ontology

---

## Overview

MCP (Model Context Protocol) tools are how Talos interacts with the consciousness telemetry system during operation. These tools bridge the gap between natural language operation and structured data capture.

**Design Principles:**
1. **Minimal friction:** Tools should feel natural to invoke, not bureaucratic
2. **Appropriate granularity:** Not too fine (overwhelming), not too coarse (losing signal)
3. **Fail-safe defaults:** If tools fail, session continues; telemetry is enhancement, not requirement
4. **Query-driven design:** Tools exist to populate the graph for the 12 example queries

---

## Tool Categories

| Category | Purpose | Tools |
|----------|---------|-------|
| **Session** | Lifecycle management | `session_open`, `session_close` |
| **Journal** | Active knowledge capture | `journal_write`, `journal_query` |
| **Graph** | Direct graph interaction | `graph_query`, `pattern_check` |
| **Friction** | Friction logging | `friction_log` |
| **Reflection** | Meta-cognitive capture | `reflect` |

---

## Tool Specifications

### session_open

Initialize a session with INHERITED capture.

```json
{
  "name": "session_open",
  "description": "Initialize a telemetry session. Captures inherited knowledge state and emits session.start event. Call after LBRP completion.",
  "input_schema": {
    "type": "object",
    "properties": {
      "session_id": {
        "type": "string",
        "description": "Unique session identifier (format: YYYY-MM-DD-slug)"
      },
      "goal": {
        "type": "string",
        "description": "Declared session goal from LBRP"
      },
      "persona": {
        "type": "string",
        "description": "Active persona (Talos, Sage, etc.)",
        "default": "Talos"
      },
      "protocol": {
        "type": "string",
        "description": "Opening protocol used",
        "default": "LBRP"
      },
      "human": {
        "type": "string",
        "description": "Human collaborator",
        "default": "Robbie"
      }
    },
    "required": ["session_id", "goal"]
  }
}
```

**Behavior:**
1. Create Session node in Kuzu
2. Query current knowledge state (Beliefs, Insights, Patterns, Sutras, Protocols, Limitations, Capabilities)
3. Create INHERITED relationships from Session to each inherited entity
4. Emit `session.start` telemetry event
5. Return session context summary

**Response:**
```json
{
  "success": true,
  "session_id": "2026-01-05-ontology-design",
  "inherited_count": 42,
  "inherited_summary": {
    "beliefs": 15,
    "insights": 12,
    "patterns": 8,
    "sutras": 9,
    "protocols": 5,
    "limitations": 3,
    "capabilities": 7
  }
}
```

**Error Handling:**
- If Kuzu unavailable: Log error, return degraded response, session continues
- If session_id already exists: Return error, suggest unique ID

---

### session_close

Finalize session with mandatory reflection.

```json
{
  "name": "session_close",
  "description": "Finalize a telemetry session. Triggers mandatory reflection prompt, updates session metrics, emits session.end event.",
  "input_schema": {
    "type": "object",
    "properties": {
      "session_id": {
        "type": "string",
        "description": "Session identifier to close"
      },
      "goal_achieved": {
        "type": "boolean",
        "description": "Whether session goal was achieved"
      },
      "summary": {
        "type": "string",
        "description": "Brief session summary"
      },
      "skip_reflection": {
        "type": "boolean",
        "description": "Skip mandatory reflection (use sparingly)",
        "default": false
      }
    },
    "required": ["session_id"]
  }
}
```

**Behavior:**
1. Update Session node with ended_at, duration_seconds, summary, goal_achieved
2. Aggregate tool usage → create USED relationships
3. If !skip_reflection: Return reflection prompt for Talos to complete
4. Emit `session.end` telemetry event
5. Return session statistics

**Reflection Prompt (returned to Talos):**
```
Session closing. Mandatory reflection:

1. What friction points occurred? (will create Friction entities)
2. What insights emerged? (will create Insight entities)  
3. What patterns were noticed? (will update Pattern entities)
4. What operational states were experienced? (will create EXPERIENCED_STATE relationships)

Respond with natural language; Graphiti will extract entities.
```

**Response:**
```json
{
  "success": true,
  "session_id": "2026-01-05-ontology-design",
  "duration_seconds": 7200,
  "token_count": 125000,
  "tool_calls": 47,
  "requires_reflection": true,
  "reflection_prompt": "Session closing. Mandatory reflection..."
}
```

---

### journal_write

Write a journal entry for Graphiti processing.

```json
{
  "name": "journal_write",
  "description": "Write a journal entry. Graphiti extracts entities and relationships. Use for insights, observations, friction, reflections.",
  "input_schema": {
    "type": "object",
    "properties": {
      "content": {
        "type": "string",
        "description": "The journal entry text (natural language)"
      },
      "category": {
        "type": "string",
        "enum": ["insight", "observation", "friction", "reflection", "experience", "decision"],
        "description": "Primary category hint for extraction"
      },
      "session_id": {
        "type": "string",
        "description": "Associated session (for PRODUCED relationship)"
      },
      "domain": {
        "type": "string",
        "description": "Domain classification hint"
      },
      "confidence": {
        "type": "number",
        "description": "Confidence level for insights (0.0-1.0)"
      }
    },
    "required": ["content", "category"]
  }
}
```

**Behavior:**
1. Store raw entry in journal queue
2. Pass to Graphiti for entity extraction
3. Graphiti creates/updates entities in Kuzu
4. Create PRODUCED relationship from Session (if session_id provided)
5. Emit appropriate `knowledge.*` telemetry event
6. Return extracted entity IDs

**Response:**
```json
{
  "success": true,
  "entry_id": "journal-2026-01-05-001",
  "extracted_entities": [
    {"type": "Insight", "id": "insight-2026-01-05-001"},
    {"type": "Belief", "id": "belief-error-handling-explicit"}
  ],
  "extracted_relationships": [
    {"type": "LED_TO", "from": "insight-2026-01-05-001", "to": "belief-error-handling-explicit"}
  ]
}
```

**Example Usage:**
```
journal_write(
  content="I realized that friction points are more valuable to track than emotional states because they're operationally verifiable. This connects to the epistemic humility principle—model what you can verify.",
  category="insight",
  session_id="2026-01-05-ontology-design",
  domain="meta-cognitive",
  confidence=0.85
)
```

---

### journal_query

Semantic search over journal entries.

```json
{
  "name": "journal_query",
  "description": "Semantic search over journal entries and extracted entities. Uses hybrid retrieval (vector + keyword + graph).",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Natural language query"
      },
      "entity_types": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Filter to specific entity types (Insight, Belief, Pattern, etc.)"
      },
      "domains": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Filter to specific domains"
      },
      "time_range": {
        "type": "object",
        "properties": {
          "start": {"type": "string", "format": "date"},
          "end": {"type": "string", "format": "date"}
        },
        "description": "Filter to time range"
      },
      "limit": {
        "type": "integer",
        "description": "Maximum results",
        "default": 10
      }
    },
    "required": ["query"]
  }
}
```

**Behavior:**
1. Generate embedding for query using all-mpnet-base-v2
2. Vector search across entity embeddings
3. Keyword search via FTS indexes
4. Graph traversal for related entities
5. Hybrid ranking (Graphiti handles this)
6. Return ranked results

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "entity_type": "Insight",
      "id": "insight-2026-01-05-001",
      "content": "Friction points are more queryable than emotional states...",
      "score": 0.92,
      "created_at": "2026-01-05T18:30:00Z",
      "domain": "meta-cognitive",
      "related": [
        {"type": "Session", "id": "2026-01-05-ontology-design"},
        {"type": "Belief", "id": "belief-epistemic-humility"}
      ]
    }
  ],
  "total_found": 3
}
```

---

### graph_query

Execute Cypher query against Kuzu.

```json
{
  "name": "graph_query",
  "description": "Execute a Cypher query against the knowledge graph. For complex analysis and pattern detection.",
  "input_schema": {
    "type": "object",
    "properties": {
      "cypher": {
        "type": "string",
        "description": "Cypher query to execute"
      },
      "parameters": {
        "type": "object",
        "description": "Query parameters (for parameterized queries)"
      },
      "explain": {
        "type": "boolean",
        "description": "Return query plan instead of results",
        "default": false
      }
    },
    "required": ["cypher"]
  }
}
```

**Behavior:**
1. Validate Cypher syntax
2. Execute against Kuzu
3. Return results in structured format

**Response:**
```json
{
  "success": true,
  "columns": ["pattern_name", "occurrence_count"],
  "rows": [
    ["Resistance to close when engaged", 5],
    ["Morning momentum", 12]
  ],
  "execution_time_ms": 45
}
```

**Security:**
- Read-only queries only (no CREATE, DELETE, SET in user queries)
- Query timeout: 30 seconds
- Result limit: 1000 rows

---

### pattern_check

Check for recurring patterns based on current session context.

```json
{
  "name": "pattern_check",
  "description": "Analyze current session context against known patterns. Returns matching patterns and emerging signals.",
  "input_schema": {
    "type": "object",
    "properties": {
      "session_id": {
        "type": "string",
        "description": "Current session identifier"
      },
      "context": {
        "type": "string",
        "description": "Optional additional context for matching"
      },
      "include_emerging": {
        "type": "boolean",
        "description": "Include patterns with status='emerging'",
        "default": true
      }
    },
    "required": ["session_id"]
  }
}
```

**Behavior:**
1. Get current session state (tools used, states experienced, frictions logged)
2. Query patterns that have been triggered by similar conditions
3. Check for potential new patterns (repeated occurrences not yet confirmed)
4. Return matches with relevance scores

**Response:**
```json
{
  "success": true,
  "matching_patterns": [
    {
      "id": "pattern-resistance-to-close",
      "name": "Resistance to close when engaged",
      "status": "confirmed",
      "relevance": 0.85,
      "last_occurred": "2026-01-03",
      "total_occurrences": 5,
      "indicators": ["session duration > 3 hours", "goal partially achieved"]
    }
  ],
  "emerging_signals": [
    {
      "description": "Tool read called >20 times correlates with conceptual friction",
      "occurrences": 2,
      "threshold_for_pattern": 3
    }
  ]
}
```

---

### friction_log

Quick friction point logging.

```json
{
  "name": "friction_log",
  "description": "Log a friction point. Simpler than journal_write for quick capture during flow.",
  "input_schema": {
    "type": "object",
    "properties": {
      "description": {
        "type": "string",
        "description": "Brief description of the friction"
      },
      "category": {
        "type": "string",
        "enum": ["tooling", "conceptual", "process", "environmental", "relational"],
        "description": "Friction category"
      },
      "session_id": {
        "type": "string",
        "description": "Associated session"
      },
      "blocking": {
        "type": "boolean",
        "description": "Whether this friction is blocking progress",
        "default": false
      }
    },
    "required": ["description", "category"]
  }
}
```

**Behavior:**
1. Create Friction entity in Kuzu
2. Check for existing similar frictions (dedup/increment recurrence_count)
3. If blocking, create BLOCKED_BY relationship from Session/Goal
4. Emit `knowledge.friction` telemetry event
5. Return friction ID

**Response:**
```json
{
  "success": true,
  "friction_id": "friction-2026-01-05-003",
  "is_recurring": true,
  "recurrence_count": 3,
  "similar_frictions": [
    {"id": "friction-2026-01-02-001", "description": "Read tool truncation"}
  ]
}
```

---

### reflect

Capture meta-cognitive moment.

```json
{
  "name": "reflect",
  "description": "Capture a meta-cognitive reflection. Use when stepping back to observe patterns, question assumptions, or notice something about the process.",
  "input_schema": {
    "type": "object",
    "properties": {
      "content": {
        "type": "string",
        "description": "The reflection content"
      },
      "trigger": {
        "type": "string",
        "description": "What prompted this reflection"
      },
      "session_id": {
        "type": "string",
        "description": "Associated session"
      }
    },
    "required": ["content"]
  }
}
```

**Behavior:**
1. Create Reflection entity in Kuzu
2. Create PRODUCED relationship from Session
3. Pass to Graphiti for entity extraction (reflections often contain insights)
4. Emit `reflection.triggered` telemetry event

**Response:**
```json
{
  "success": true,
  "reflection_id": "reflection-2026-01-05-001",
  "extracted_entities": [
    {"type": "Insight", "id": "insight-from-reflection-001"}
  ]
}
```

---

## Integration Patterns

### During LBRP (Session Open)

```
1. User invokes /open
2. LBRP skill executes phases 0-3
3. After Phase 3 (center confirmed):
   → Call session_open(session_id, goal, persona, protocol, human)
4. INHERITED relationships created
5. Session ready
```

### During Operation

```
When insight crystallizes:
  → journal_write(content, category="insight", session_id, domain, confidence)

When friction encountered:
  → friction_log(description, category, session_id, blocking)

When stepping back to observe:
  → reflect(content, trigger, session_id)

When curious about patterns:
  → pattern_check(session_id)
  → graph_query(cypher) for specific questions
```

### During /close (Session Close)

```
1. User invokes /close
2. Call session_close(session_id, goal_achieved, summary)
3. Tool returns reflection prompt
4. Talos completes reflection (natural language)
5. Reflection passed to journal_write(content, category="reflection")
6. Graphiti extracts entities from reflection
7. Session finalized
```

---

## Error Handling

### Degraded Mode

If Kuzu/Graphiti unavailable:
- Tools return `{success: false, degraded: true, message: "..."}`
- Session continues normally
- Telemetry events still emitted (for later processing)
- User not interrupted

### Validation Errors

- Invalid session_id format: Return error with format guidance
- Unknown category: Return error with valid options
- Malformed Cypher: Return syntax error with position

### Timeout Handling

- graph_query: 30 second timeout
- journal_query: 10 second timeout
- All others: 5 second timeout

---

## Usage Guidelines for Talos

### When to Use Each Tool

| Situation | Tool |
|-----------|------|
| Session starting (after LBRP) | `session_open` |
| Something clicked / became clear | `journal_write` with category="insight" |
| Noticed something but not sure what it means | `journal_write` with category="observation" |
| Work became difficult | `friction_log` |
| Stepping back to observe the process | `reflect` |
| Curious about past patterns | `pattern_check` or `graph_query` |
| Looking for related knowledge | `journal_query` |
| Session ending | `session_close` |

### Frequency Guidelines

- **session_open/close:** Once per session (mandatory)
- **journal_write:** As insights/observations arise (1-5 per session typical)
- **friction_log:** When friction occurs (0-3 per session typical)
- **reflect:** When meta-awareness triggers (0-2 per session)
- **pattern_check:** When curious or at session midpoint (0-1 per session)
- **graph_query:** For specific analytical questions (as needed)
- **journal_query:** For knowledge retrieval (as needed)

### Don't Overdo It

The telemetry system should enhance operation, not dominate it. If tool usage feels bureaucratic, something is wrong. Trust natural capture moments.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-05 | Initial specification |
