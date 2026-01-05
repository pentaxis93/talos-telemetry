"""Tests for entity extraction module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from talos_telemetry.extraction.extractor import (
    _parse_extraction_response,
    extract_entities,
    extract_single_entity,
)


class TestParseExtractionResponse:
    """Tests for parsing LLM responses."""

    def test_parse_single_entity(self):
        """Parse a response with one entity."""
        data = {
            "entities": [
                {
                    "entity_type": "Insight",
                    "content": "Testing reveals assumptions",
                    "confidence": 0.9,
                    "domain": "programming",
                }
            ],
            "relationships": [],
        }

        result = _parse_extraction_response(data)

        assert len(result.entities) == 1
        assert result.entities[0].entity_type == "Insight"
        assert result.entities[0].content == "Testing reveals assumptions"
        assert result.entities[0].confidence == 0.9
        assert result.entities[0].domain == "programming"

    def test_parse_multiple_entities(self):
        """Parse a response with multiple entities."""
        data = {
            "entities": [
                {"entity_type": "Friction", "content": "API timeout issues", "confidence": 0.95},
                {
                    "entity_type": "Insight",
                    "content": "Need retry logic",
                    "confidence": 0.8,
                },
            ],
            "relationships": [
                {"from_index": 0, "to_index": 1, "relationship_type": "LED_TO"},
            ],
        }

        result = _parse_extraction_response(data)

        assert len(result.entities) == 2
        assert result.entities[0].entity_type == "Friction"
        assert result.entities[1].entity_type == "Insight"
        assert len(result.relationships) == 1
        assert result.relationships[0]["relationship_type"] == "LED_TO"

    def test_parse_empty_response(self):
        """Parse an empty response."""
        data = {"entities": [], "relationships": []}

        result = _parse_extraction_response(data)

        assert len(result.entities) == 0
        assert len(result.relationships) == 0

    def test_parse_missing_optional_fields(self):
        """Parse response with missing optional fields."""
        data = {
            "entities": [
                {"entity_type": "Observation", "content": "Something observed", "confidence": 0.7}
            ],
            "relationships": [],
        }

        result = _parse_extraction_response(data)

        assert result.entities[0].domain is None
        assert result.entities[0].metadata is None


class TestExtractEntitiesOpenAI:
    """Tests for OpenAI extraction (mocked)."""

    @patch("talos_telemetry.extraction.extractor._get_openai_client")
    def test_extract_insight(self, mock_get_client):
        """Extract an insight from text."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "entities": [
                                {
                                    "entity_type": "Insight",
                                    "content": "Context windows are the fundamental constraint",
                                    "confidence": 0.92,
                                    "domain": "AI",
                                }
                            ],
                            "relationships": [],
                        }
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = extract_entities(
            "I realized that context windows are the fundamental constraint for AI agents.",
            provider="openai",
        )

        assert result.entities[0].entity_type == "Insight"
        assert "context windows" in result.entities[0].content.lower()
        assert result.entities[0].confidence > 0.8

    @patch("talos_telemetry.extraction.extractor._get_openai_client")
    def test_extract_friction(self, mock_get_client):
        """Extract a friction from text."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "entities": [
                                {
                                    "entity_type": "Friction",
                                    "content": "Database connections not releasing properly",
                                    "confidence": 0.95,
                                    "domain": "programming",
                                }
                            ],
                            "relationships": [],
                        }
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = extract_entities(
            "Ran into issues where database connections weren't releasing properly.",
            provider="openai",
        )

        assert result.entities[0].entity_type == "Friction"
        assert "database" in result.entities[0].content.lower()

    @patch("talos_telemetry.extraction.extractor._get_openai_client")
    def test_extract_multiple_entities_with_relationship(self, mock_get_client):
        """Extract multiple entities with relationship."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "entities": [
                                {
                                    "entity_type": "Friction",
                                    "content": "Kuzu timestamp() failed",
                                    "confidence": 0.95,
                                },
                                {
                                    "entity_type": "Insight",
                                    "content": "Kuzu requires string argument for timestamp()",
                                    "confidence": 0.9,
                                },
                            ],
                            "relationships": [
                                {"from_index": 0, "to_index": 1, "relationship_type": "LED_TO"}
                            ],
                        }
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = extract_entities(
            "The Kuzu timestamp() function was failing. I discovered it requires a string argument.",
            provider="openai",
        )

        assert len(result.entities) == 2
        assert result.entities[0].entity_type == "Friction"
        assert result.entities[1].entity_type == "Insight"
        assert len(result.relationships) == 1
        assert result.relationships[0]["relationship_type"] == "LED_TO"


class TestExtractSingleEntity:
    """Tests for single entity extraction."""

    @patch("talos_telemetry.extraction.extractor._get_openai_client")
    def test_extract_single_returns_highest_confidence(self, mock_get_client):
        """Extract single entity returns highest confidence."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "entities": [
                                {
                                    "entity_type": "Observation",
                                    "content": "Low conf",
                                    "confidence": 0.5,
                                },
                                {
                                    "entity_type": "Insight",
                                    "content": "High conf",
                                    "confidence": 0.95,
                                },
                            ],
                            "relationships": [],
                        }
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = extract_single_entity("Some text", provider="openai")

        assert result is not None
        assert result.entity_type == "Insight"
        assert result.confidence == 0.95

    @patch("talos_telemetry.extraction.extractor._get_openai_client")
    def test_extract_single_with_hint_type(self, mock_get_client):
        """Extract single entity with hint prefers matching type."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "entities": [
                                {
                                    "entity_type": "Insight",
                                    "content": "High conf",
                                    "confidence": 0.95,
                                },
                                {
                                    "entity_type": "Friction",
                                    "content": "Lower conf friction",
                                    "confidence": 0.7,
                                },
                            ],
                            "relationships": [],
                        }
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = extract_single_entity("Some text", hint_type="friction", provider="openai")

        assert result is not None
        assert result.entity_type == "Friction"

    @patch("talos_telemetry.extraction.extractor._get_openai_client")
    def test_extract_single_empty_returns_none(self, mock_get_client):
        """Extract single entity returns None on empty response."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({"entities": [], "relationships": []})))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = extract_single_entity("Some text", provider="openai")

        assert result is None


class TestProviderSelection:
    """Tests for provider selection."""

    def test_unknown_provider_raises(self):
        """Unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            extract_entities("test", provider="unknown")
