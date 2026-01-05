"""LLM-based entity extraction from free-form text.

Extracts structured entities (Insight, Pattern, Belief, etc.) from natural language
using OpenAI or Anthropic LLMs with structured output.
"""

import json
import os
from dataclasses import dataclass

# Lazy imports for LLM clients
_openai_client = None
_anthropic_client = None


@dataclass
class ExtractedEntity:
    """An entity extracted from text."""

    entity_type: str  # Insight, Observation, Pattern, Belief, Decision, Friction
    content: str  # The extracted content/description
    confidence: float  # 0.0-1.0 extraction confidence
    domain: str | None = None  # Optional domain classification
    metadata: dict | None = None  # Additional extracted properties


@dataclass
class ExtractionResult:
    """Result of entity extraction."""

    entities: list[ExtractedEntity]
    relationships: list[dict]  # Extracted relationships between entities
    raw_response: dict | None = None  # Raw LLM response for debugging


# JSON schema for structured output
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": [
                            "Insight",
                            "Observation",
                            "Pattern",
                            "Belief",
                            "Decision",
                            "Friction",
                            "Experience",
                            "Reflection",
                        ],
                        "description": "The type of entity being extracted",
                    },
                    "content": {
                        "type": "string",
                        "description": "The core content or description of this entity",
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Confidence in this extraction (0.0-1.0)",
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain this entity belongs to (optional)",
                    },
                },
                "required": ["entity_type", "content", "confidence"],
            },
        },
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "from_index": {
                        "type": "integer",
                        "description": "Index of source entity in entities array",
                    },
                    "to_index": {
                        "type": "integer",
                        "description": "Index of target entity in entities array",
                    },
                    "relationship_type": {
                        "type": "string",
                        "enum": ["LED_TO", "CONTRADICTS", "SUPPORTS", "REFINES", "REVEALED"],
                        "description": "Type of relationship",
                    },
                },
                "required": ["from_index", "to_index", "relationship_type"],
            },
        },
    },
    "required": ["entities", "relationships"],
}

EXTRACTION_PROMPT = """You are an entity extraction system for an AI agent's self-knowledge graph.
Analyze the following text and extract structured entities.

Entity types and their meanings:
- Insight: A crystallized understanding worth preserving (realization, learning, aha moment)
- Observation: A pre-crystallized fragment, not yet insight (raw data, noted fact)
- Pattern: A recurring behavioral or cognitive tendency (something that happens repeatedly)
- Belief: An operating assumption, value, or principle (something held to be true)
- Decision: A choice that affected operation (deliberate selection between options)
- Friction: A point of difficulty, confusion, or inefficiency (obstacle, problem)
- Experience: A notable event or situation encountered (something that happened)
- Reflection: A meta-cognitive consideration (thinking about thinking)

Guidelines:
- Extract only entities clearly present in the text
- Assign confidence based on how explicit the entity is (0.9+ for explicit, 0.6-0.8 for implicit)
- Identify relationships between extracted entities when present
- If the text is simple/single-purpose, extract just one entity
- Domain should reflect the subject area (e.g., "programming", "cognition", "process")

Text to analyze:
{text}

Extract entities and relationships as JSON."""


def _get_openai_client():
    """Get or create OpenAI client."""
    global _openai_client
    if _openai_client is None:
        try:
            from openai import OpenAI

            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            _openai_client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    return _openai_client


def _get_anthropic_client():
    """Get or create Anthropic client."""
    global _anthropic_client
    if _anthropic_client is None:
        try:
            import anthropic

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            _anthropic_client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    return _anthropic_client


def extract_entities(
    text: str,
    provider: str = "openai",
    model: str | None = None,
) -> ExtractionResult:
    """Extract entities from free-form text using LLM.

    Args:
        text: The text to extract entities from.
        provider: LLM provider ("openai" or "anthropic").
        model: Model to use. Defaults to gpt-4o-mini for OpenAI, claude-3-haiku for Anthropic.

    Returns:
        ExtractionResult with extracted entities and relationships.
    """
    if provider == "openai":
        return _extract_with_openai(text, model or "gpt-4o-mini")
    elif provider == "anthropic":
        return _extract_with_anthropic(text, model or "claude-3-haiku-20240307")
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'openai' or 'anthropic'.")


def _extract_with_openai(text: str, model: str) -> ExtractionResult:
    """Extract using OpenAI with structured output."""
    client = _get_openai_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You extract entities from text for a knowledge graph. Always respond with valid JSON.",
            },
            {"role": "user", "content": EXTRACTION_PROMPT.format(text=text)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "extraction", "schema": EXTRACTION_SCHEMA, "strict": True},
        },
        temperature=0.1,
    )

    content = response.choices[0].message.content
    if not content:
        return ExtractionResult(entities=[], relationships=[], raw_response=None)

    parsed = json.loads(content)
    return _parse_extraction_response(parsed)


def _extract_with_anthropic(text: str, model: str) -> ExtractionResult:
    """Extract using Anthropic."""
    client = _get_anthropic_client()

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"{EXTRACTION_PROMPT.format(text=text)}\n\nRespond only with valid JSON matching the schema.",
            }
        ],
        system="You extract entities from text for a knowledge graph. Always respond with valid JSON only, no explanations.",
    )

    content = response.content[0].text
    if not content:
        return ExtractionResult(entities=[], relationships=[], raw_response=None)

    # Parse JSON from response (may include ```json blocks)
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    parsed = json.loads(content)
    return _parse_extraction_response(parsed)


def _parse_extraction_response(data: dict) -> ExtractionResult:
    """Parse raw extraction response into structured result."""
    entities = []
    for e in data.get("entities", []):
        entities.append(
            ExtractedEntity(
                entity_type=e.get("entity_type", "Observation"),
                content=e.get("content", ""),
                confidence=e.get("confidence", 0.5),
                domain=e.get("domain"),
                metadata=e.get("metadata"),
            )
        )

    relationships = data.get("relationships", [])

    return ExtractionResult(entities=entities, relationships=relationships, raw_response=data)


def extract_single_entity(
    text: str,
    hint_type: str | None = None,
    provider: str = "openai",
    model: str | None = None,
) -> ExtractedEntity | None:
    """Extract a single primary entity from text.

    Useful when you expect the text to represent one concept.

    Args:
        text: The text to extract from.
        hint_type: Optional hint for expected entity type.
        provider: LLM provider.
        model: Model to use.

    Returns:
        The primary extracted entity, or None if extraction failed.
    """
    result = extract_entities(text, provider, model)
    if not result.entities:
        return None

    # If hint provided, prefer matching type
    if hint_type:
        for entity in result.entities:
            if entity.entity_type.lower() == hint_type.lower():
                return entity

    # Return highest confidence entity
    return max(result.entities, key=lambda e: e.confidence)
