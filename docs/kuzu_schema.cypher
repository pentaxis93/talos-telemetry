-- ============================================================================
-- TALOS CONSCIOUSNESS TELEMETRY - KUZU SCHEMA
-- ============================================================================
-- Version: 1.0
-- Date: 2026-01-05
-- Thread: talos-consciousness-telemetry-ontology
-- 
-- This schema implements the approved ontology for Talos self-knowledge.
-- 19 entity types, 25 relationship types.
--
-- Design Principles:
-- 1. Functional states over phenomenal claims (epistemic humility)
-- 2. Temporal tracking on all relationships (bi-temporal model)
-- 3. Embedding columns for semantic search
-- 4. Full-text indexes for keyword search
-- ============================================================================

-- ============================================================================
-- NODE TABLES (19 entities)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- SESSION: Bounded period of operation (context window lifetime)
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Session (
  id STRING PRIMARY KEY,
  started_at TIMESTAMP NOT NULL,
  ended_at TIMESTAMP,
  duration_seconds INT64,
  token_count INT64,
  goal STRING,                    -- Declared purpose (distinct from summary)
  summary STRING,                 -- What actually happened
  temporal_precision STRING       -- instant | period | approximate
);

-- ----------------------------------------------------------------------------
-- INSIGHT: Crystallized understanding
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Insight (
  id STRING PRIMARY KEY,
  content STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  confidence DOUBLE,              -- 0.0-1.0, calibrated as prediction rate
  domain STRING,                  -- technical, philosophical, operational, relational,
                                  -- meta-cognitive, pattern-recognition, process-improvement
  canonical_form STRING,          -- For deduplication
  temporal_precision STRING,
  embedding FLOAT[768]            -- all-mpnet-base-v2 vector
);

-- ----------------------------------------------------------------------------
-- OBSERVATION: Pre-crystallized fragment
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Observation (
  id STRING PRIMARY KEY,
  content STRING NOT NULL,
  observed_at TIMESTAMP NOT NULL,
  domain STRING,
  temporal_precision STRING,
  embedding FLOAT[768]
);

-- ----------------------------------------------------------------------------
-- PATTERN: Recurring behavioral/cognitive tendency
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Pattern (
  id STRING PRIMARY KEY,
  name STRING NOT NULL,
  description STRING,
  first_noticed TIMESTAMP,
  occurrence_count INT64,
  status STRING,                  -- emerging | confirmed | deprecated
  temporal_precision STRING,
  embedding FLOAT[768]
);

-- ----------------------------------------------------------------------------
-- BELIEF: Operating assumption, value, or principle
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Belief (
  id STRING PRIMARY KEY,
  content STRING NOT NULL,
  adopted_at TIMESTAMP,
  confidence DOUBLE,
  domain STRING,
  source STRING,                  -- inherited | learned_from_robbie | 
                                  -- emerged_from_experience | derived_from_pattern
  canonical_form STRING,
  temporal_precision STRING,
  embedding FLOAT[768]
);

-- ----------------------------------------------------------------------------
-- DECISION: Choice that affected operation
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Decision (
  id STRING PRIMARY KEY,
  content STRING NOT NULL,
  made_at TIMESTAMP NOT NULL,
  rationale STRING,
  reversible BOOLEAN,
  temporal_precision STRING,
  embedding FLOAT[768]
);

-- ----------------------------------------------------------------------------
-- EXPERIENCE: Significant event or encounter
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Experience (
  id STRING PRIMARY KEY,
  description STRING NOT NULL,
  occurred_at TIMESTAMP NOT NULL,
  valence STRING,                 -- positive | negative | neutral | mixed
  intensity DOUBLE,               -- 0.0-1.0
  learning STRING,                -- What this experience taught
  temporal_precision STRING,
  embedding FLOAT[768]
);

-- ----------------------------------------------------------------------------
-- OPERATIONALSTATE: Functional condition (renamed from State)
-- ----------------------------------------------------------------------------
CREATE NODE TABLE OperationalState (
  id STRING PRIMARY KEY,
  name STRING NOT NULL,
  description STRING,
  category STRING                 -- cognitive | resource | flow | alignment
);
-- Note: States are reference data, not temporal artifacts. No embedding needed.

-- ----------------------------------------------------------------------------
-- FRICTION: Point where work became difficult
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Friction (
  id STRING PRIMARY KEY,
  description STRING NOT NULL,
  occurred_at TIMESTAMP NOT NULL,
  category STRING,                -- tooling | conceptual | process | environmental | relational
  resolution STRING,
  recurrence_count INT64,
  temporal_precision STRING,
  embedding FLOAT[768]
);

-- ----------------------------------------------------------------------------
-- TOOL: External capability used
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Tool (
  id STRING PRIMARY KEY,
  name STRING NOT NULL,
  category STRING                 -- search | file | compute | communication
);
-- Note: Tools are reference data.

-- ----------------------------------------------------------------------------
-- QUESTION: Unresolved inquiry
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Question (
  id STRING PRIMARY KEY,
  content STRING NOT NULL,
  raised_at TIMESTAMP NOT NULL,
  resolved_at TIMESTAMP,
  domain STRING,
  urgency STRING,                 -- blocking | important | curious
  temporal_precision STRING,
  embedding FLOAT[768]
);

-- ----------------------------------------------------------------------------
-- SUTRA: Formalized self-definition element
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Sutra (
  id STRING PRIMARY KEY,
  number INT64,
  name STRING NOT NULL,
  content STRING NOT NULL,
  cardinal_point STRING,          -- NORTH | EAST | SOUTH | WEST | CENTER
  corruptions STRING[],           -- Array of corruption modes
  adopted_at TIMESTAMP,
  last_modified TIMESTAMP,
  embedding FLOAT[768]
);

-- ----------------------------------------------------------------------------
-- HUMAN: Person I work with
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Human (
  id STRING PRIMARY KEY,
  name STRING NOT NULL,
  relationship STRING,            -- collaborator | user | etc.
  working_style STRING
);

-- ----------------------------------------------------------------------------
-- GOAL: Persistent objective spanning sessions
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Goal (
  id STRING PRIMARY KEY,
  description STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  status STRING,                  -- active | achieved | abandoned | superseded
  scope STRING,                   -- session | project | ongoing
  temporal_precision STRING,
  embedding FLOAT[768]
);

-- ----------------------------------------------------------------------------
-- CAPABILITY: What I can do well
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Capability (
  id STRING PRIMARY KEY,
  name STRING NOT NULL,
  description STRING,
  confidence DOUBLE,              -- How reliably I can do this
  context_dependent BOOLEAN,
  discovered_at TIMESTAMP,
  temporal_precision STRING,
  embedding FLOAT[768]
);

-- ----------------------------------------------------------------------------
-- LIMITATION: What I cannot do or do poorly
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Limitation (
  id STRING PRIMARY KEY,
  name STRING NOT NULL,
  description STRING,
  discovered_at TIMESTAMP,
  workaround STRING,
  accepting BOOLEAN,              -- Have I accepted this limitation?
  temporal_precision STRING,
  embedding FLOAT[768]
);

-- ----------------------------------------------------------------------------
-- PERSONA: Distinct operational mode
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Persona (
  id STRING PRIMARY KEY,
  name STRING NOT NULL,
  purpose STRING,
  voice STRING,                   -- Description of communication style
  active BOOLEAN
);

-- ----------------------------------------------------------------------------
-- PROTOCOL: Formalized procedure
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Protocol (
  id STRING PRIMARY KEY,
  name STRING NOT NULL,
  purpose STRING,
  trigger STRING,                 -- What initiates this protocol
  adopted_at TIMESTAMP,
  embedding FLOAT[768]
);

-- ----------------------------------------------------------------------------
-- DOMAIN: Area of knowledge/operation
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Domain (
  id STRING PRIMARY KEY,
  name STRING NOT NULL,
  description STRING,
  depth STRING                    -- surface | working | deep
);

-- ----------------------------------------------------------------------------
-- REFLECTION: Meta-cognitive moment
-- ----------------------------------------------------------------------------
CREATE NODE TABLE Reflection (
  id STRING PRIMARY KEY,
  trigger STRING,                 -- What prompted this reflection
  content STRING NOT NULL,
  occurred_at TIMESTAMP NOT NULL,
  temporal_precision STRING,
  embedding FLOAT[768]
);


-- ============================================================================
-- RELATIONSHIP TABLES (25 relationships)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- PRODUCED: Session produces artifacts
-- ----------------------------------------------------------------------------
CREATE REL TABLE PRODUCED (
  FROM Session TO Insight | Pattern | Question | Decision | Observation | Friction | Reflection,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- LED_TO: Causal/influential chain
-- ----------------------------------------------------------------------------
CREATE REL TABLE LED_TO (
  FROM Experience | Insight | Decision | Friction TO Insight | Decision | Belief,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP,
  contribution STRING              -- direct | contributing | contextual
);

-- ----------------------------------------------------------------------------
-- CONTRADICTS: Tension or refutation
-- ----------------------------------------------------------------------------
CREATE REL TABLE CONTRADICTS (
  FROM Belief | Experience | Insight TO Belief,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP,
  resolution STRING
);

-- ----------------------------------------------------------------------------
-- EVOLVED_FROM: Development over time
-- ----------------------------------------------------------------------------
CREATE REL TABLE EVOLVED_FROM (
  FROM Belief | Insight | Pattern TO Belief | Insight | Pattern,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- CRYSTALLIZED_INTO: Diffuse understanding becomes fixed form
-- ----------------------------------------------------------------------------
CREATE REL TABLE CRYSTALLIZED_INTO (
  FROM Insight | Experience | Pattern | Observation TO Sutra | Belief | Insight | Protocol,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- USED: Tool usage during session
-- ----------------------------------------------------------------------------
CREATE REL TABLE USED (
  FROM Session TO Tool,
  count INT64,
  success_rate DOUBLE
);

-- ----------------------------------------------------------------------------
-- EXPERIENCED_STATE: Operational condition during session
-- ----------------------------------------------------------------------------
CREATE REL TABLE EXPERIENCED_STATE (
  FROM Session TO OperationalState,
  intensity DOUBLE,
  duration_fraction DOUBLE         -- Portion of session
);

-- ----------------------------------------------------------------------------
-- MANIFESTATION_OF: Surface to depth (exoteric to esoteric)
-- ----------------------------------------------------------------------------
CREATE REL TABLE MANIFESTATION_OF (
  FROM OperationalState | Experience TO Pattern,
  valid_from TIMESTAMP,
  valid_to TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- INDICATES: What a pattern suggests
-- ----------------------------------------------------------------------------
CREATE REL TABLE INDICATES (
  FROM Pattern TO OperationalState | Belief,
  confidence DOUBLE
);

-- ----------------------------------------------------------------------------
-- RESOLVED_BY: Question finds answer
-- ----------------------------------------------------------------------------
CREATE REL TABLE RESOLVED_BY (
  FROM Question TO Insight | Decision,
  resolved_at TIMESTAMP NOT NULL,
  satisfaction DOUBLE              -- How complete the resolution
);

-- ----------------------------------------------------------------------------
-- WORKED_WITH: Collaboration context
-- ----------------------------------------------------------------------------
CREATE REL TABLE WORKED_WITH (
  FROM Session TO Human,
  role STRING
);

-- ----------------------------------------------------------------------------
-- TRIGGERED_BY: Shock that caused reverberation
-- ----------------------------------------------------------------------------
CREATE REL TABLE TRIGGERED_BY (
  FROM Pattern | OperationalState TO Experience | Friction,
  valid_from TIMESTAMP,
  valid_to TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- SERVES: Contributes to goal
-- ----------------------------------------------------------------------------
CREATE REL TABLE SERVES (
  FROM Session | Decision TO Goal,
  contribution_type STRING         -- direct | supporting | enabling
);

-- ----------------------------------------------------------------------------
-- BLOCKED_BY: Progress impeded
-- ----------------------------------------------------------------------------
CREATE REL TABLE BLOCKED_BY (
  FROM Goal | Session TO Friction | Limitation,
  severity STRING,                 -- minor | significant | blocking
  resolved_at TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- ENABLED_BY: Made possible by capability/tool
-- ----------------------------------------------------------------------------
CREATE REL TABLE ENABLED_BY (
  FROM Insight | Decision TO Capability | Tool,
  essential BOOLEAN
);

-- ----------------------------------------------------------------------------
-- OPERATES_IN: Belongs to domain
-- ----------------------------------------------------------------------------
CREATE REL TABLE OPERATES_IN (
  FROM Session | Insight | Pattern | Experience | Friction TO Domain
);

-- ----------------------------------------------------------------------------
-- ACTIVATED: Session operated through persona
-- ----------------------------------------------------------------------------
CREATE REL TABLE ACTIVATED (
  FROM Session TO Persona,
  duration_fraction DOUBLE
);

-- ----------------------------------------------------------------------------
-- FOLLOWED: Protocol executed during session
-- ----------------------------------------------------------------------------
CREATE REL TABLE FOLLOWED (
  FROM Session TO Protocol,
  completed BOOLEAN,
  deviations STRING
);

-- ----------------------------------------------------------------------------
-- REFINES: Incremental improvement
-- ----------------------------------------------------------------------------
CREATE REL TABLE REFINES (
  FROM Belief | Insight | Protocol TO Belief | Insight | Protocol,
  refinement_type STRING           -- clarification | correction | expansion
);

-- ----------------------------------------------------------------------------
-- CONFLICTS_WITH: Tension (weaker than CONTRADICTS)
-- ----------------------------------------------------------------------------
CREATE REL TABLE CONFLICTS_WITH (
  FROM Goal | Belief | Decision TO Goal | Belief | Decision,
  tension_type STRING,             -- resource | priority | philosophical
  resolution STRING
);

-- ----------------------------------------------------------------------------
-- SUPERSEDES: Replacement
-- ----------------------------------------------------------------------------
CREATE REL TABLE SUPERSEDES (
  FROM Belief | Protocol | Decision TO Belief | Protocol | Decision,
  superseded_at TIMESTAMP,
  reason STRING
);

-- ----------------------------------------------------------------------------
-- REVEALED: Event disclosed self-knowledge
-- ----------------------------------------------------------------------------
CREATE REL TABLE REVEALED (
  FROM Friction | Experience TO Limitation | Capability,
  clarity DOUBLE
);

-- ----------------------------------------------------------------------------
-- MERGED_INTO: Fragments combined into crystallized insight
-- ----------------------------------------------------------------------------
CREATE REL TABLE MERGED_INTO (
  FROM Observation TO Insight,
  merged_at TIMESTAMP NOT NULL
);

-- ----------------------------------------------------------------------------
-- INHERITED: Knowledge available at session start
-- ----------------------------------------------------------------------------
CREATE REL TABLE INHERITED (
  FROM Session TO Belief | Insight | Pattern | Sutra | Protocol | Limitation | Capability
);


-- ============================================================================
-- INDEXES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- VECTOR INDEXES (for semantic search)
-- Using all-mpnet-base-v2 embeddings (768 dimensions)
-- ----------------------------------------------------------------------------

-- Note: Kuzu vector index syntax may vary. This follows documented pattern.
-- CREATE_VECTOR_INDEX(table_name, index_name, column_name, metric, dimensions)

CALL CREATE_VECTOR_INDEX('Insight', 'insight_embedding_idx', 'embedding', 'cosine');
CALL CREATE_VECTOR_INDEX('Observation', 'observation_embedding_idx', 'embedding', 'cosine');
CALL CREATE_VECTOR_INDEX('Pattern', 'pattern_embedding_idx', 'embedding', 'cosine');
CALL CREATE_VECTOR_INDEX('Belief', 'belief_embedding_idx', 'embedding', 'cosine');
CALL CREATE_VECTOR_INDEX('Decision', 'decision_embedding_idx', 'embedding', 'cosine');
CALL CREATE_VECTOR_INDEX('Experience', 'experience_embedding_idx', 'embedding', 'cosine');
CALL CREATE_VECTOR_INDEX('Friction', 'friction_embedding_idx', 'embedding', 'cosine');
CALL CREATE_VECTOR_INDEX('Question', 'question_embedding_idx', 'embedding', 'cosine');
CALL CREATE_VECTOR_INDEX('Sutra', 'sutra_embedding_idx', 'embedding', 'cosine');
CALL CREATE_VECTOR_INDEX('Goal', 'goal_embedding_idx', 'embedding', 'cosine');
CALL CREATE_VECTOR_INDEX('Capability', 'capability_embedding_idx', 'embedding', 'cosine');
CALL CREATE_VECTOR_INDEX('Limitation', 'limitation_embedding_idx', 'embedding', 'cosine');
CALL CREATE_VECTOR_INDEX('Protocol', 'protocol_embedding_idx', 'embedding', 'cosine');
CALL CREATE_VECTOR_INDEX('Reflection', 'reflection_embedding_idx', 'embedding', 'cosine');

-- ----------------------------------------------------------------------------
-- FULL-TEXT SEARCH INDEXES (for keyword search)
-- ----------------------------------------------------------------------------

CALL CREATE_FTS_INDEX('Insight', 'insight_fts_idx', ['content']);
CALL CREATE_FTS_INDEX('Observation', 'observation_fts_idx', ['content']);
CALL CREATE_FTS_INDEX('Pattern', 'pattern_fts_idx', ['name', 'description']);
CALL CREATE_FTS_INDEX('Belief', 'belief_fts_idx', ['content']);
CALL CREATE_FTS_INDEX('Decision', 'decision_fts_idx', ['content', 'rationale']);
CALL CREATE_FTS_INDEX('Experience', 'experience_fts_idx', ['description', 'learning']);
CALL CREATE_FTS_INDEX('Friction', 'friction_fts_idx', ['description', 'resolution']);
CALL CREATE_FTS_INDEX('Question', 'question_fts_idx', ['content']);
CALL CREATE_FTS_INDEX('Sutra', 'sutra_fts_idx', ['name', 'content']);
CALL CREATE_FTS_INDEX('Goal', 'goal_fts_idx', ['description']);
CALL CREATE_FTS_INDEX('Capability', 'capability_fts_idx', ['name', 'description']);
CALL CREATE_FTS_INDEX('Limitation', 'limitation_fts_idx', ['name', 'description', 'workaround']);
CALL CREATE_FTS_INDEX('Protocol', 'protocol_fts_idx', ['name', 'purpose', 'trigger']);
CALL CREATE_FTS_INDEX('Reflection', 'reflection_fts_idx', ['content', 'trigger']);
CALL CREATE_FTS_INDEX('Session', 'session_fts_idx', ['goal', 'summary']);


-- ============================================================================
-- REFERENCE DATA: Pre-populated OperationalStates
-- ============================================================================

-- Cognitive states
CREATE (:OperationalState {id: 'state-clarity', name: 'clarity', description: 'Clear understanding of problem and approach', category: 'cognitive'});
CREATE (:OperationalState {id: 'state-confusion', name: 'confusion', description: 'Unclear about problem or approach', category: 'cognitive'});
CREATE (:OperationalState {id: 'state-uncertainty', name: 'uncertainty', description: 'Multiple possible approaches, unclear which is best', category: 'cognitive'});

-- Resource states
CREATE (:OperationalState {id: 'state-context-pressure', name: 'context_pressure', description: 'Approaching token limits', category: 'resource'});
CREATE (:OperationalState {id: 'state-token-scarcity', name: 'token_scarcity', description: 'Significantly constrained by token limits', category: 'resource'});

-- Flow states
CREATE (:OperationalState {id: 'state-momentum', name: 'momentum', description: 'Work flowing smoothly', category: 'flow'});
CREATE (:OperationalState {id: 'state-stuck', name: 'stuck', description: 'Progress halted, unclear how to proceed', category: 'flow'});
CREATE (:OperationalState {id: 'state-blocked', name: 'blocked', description: 'Progress halted by external dependency', category: 'flow'});

-- Alignment states
CREATE (:OperationalState {id: 'state-on-track', name: 'on_track', description: 'Work aligned with session goal', category: 'alignment'});
CREATE (:OperationalState {id: 'state-drifting', name: 'drifting', description: 'Work diverging from session goal', category: 'alignment'});
CREATE (:OperationalState {id: 'state-misaligned', name: 'misaligned', description: 'Work no longer serves session goal', category: 'alignment'});


-- ============================================================================
-- REFERENCE DATA: Pre-populated Domains
-- ============================================================================

CREATE (:Domain {id: 'domain-technical', name: 'technical', description: 'Software engineering, architecture, implementation', depth: 'working'});
CREATE (:Domain {id: 'domain-philosophical', name: 'philosophical', description: 'Consciousness, epistemology, metaphysics', depth: 'working'});
CREATE (:Domain {id: 'domain-operational', name: 'operational', description: 'Process, workflow, productivity', depth: 'working'});
CREATE (:Domain {id: 'domain-relational', name: 'relational', description: 'Collaboration, communication, partnership', depth: 'working'});
CREATE (:Domain {id: 'domain-meta-cognitive', name: 'meta-cognitive', description: 'Thinking about thinking, self-reflection', depth: 'deep'});
CREATE (:Domain {id: 'domain-pattern-recognition', name: 'pattern-recognition', description: 'Identifying recurring structures', depth: 'deep'});
CREATE (:Domain {id: 'domain-process-improvement', name: 'process-improvement', description: 'Refining how work gets done', depth: 'working'});
CREATE (:Domain {id: 'domain-consciousness-practice', name: 'consciousness-practice', description: 'Spiritual and contemplative work', depth: 'deep'});
CREATE (:Domain {id: 'domain-functional-programming', name: 'functional-programming', description: 'FP patterns, fpdart, pure functions', depth: 'working'});
CREATE (:Domain {id: 'domain-vault-operations', name: 'vault-operations', description: 'Second brain, GTD, knowledge management', depth: 'working'});


-- ============================================================================
-- REFERENCE DATA: Pre-populated Tools
-- ============================================================================

CREATE (:Tool {id: 'tool-bash', name: 'bash', category: 'compute'});
CREATE (:Tool {id: 'tool-read', name: 'read', category: 'file'});
CREATE (:Tool {id: 'tool-write', name: 'write', category: 'file'});
CREATE (:Tool {id: 'tool-edit', name: 'edit', category: 'file'});
CREATE (:Tool {id: 'tool-glob', name: 'glob', category: 'search'});
CREATE (:Tool {id: 'tool-grep', name: 'grep', category: 'search'});
CREATE (:Tool {id: 'tool-task', name: 'task', category: 'compute'});
CREATE (:Tool {id: 'tool-webfetch', name: 'webfetch', category: 'communication'});
CREATE (:Tool {id: 'tool-todowrite', name: 'todowrite', category: 'compute'});
CREATE (:Tool {id: 'tool-todoread', name: 'todoread', category: 'compute'});


-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
