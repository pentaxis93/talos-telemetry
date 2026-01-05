"""Embedding model management."""

import os
from pathlib import Path
from typing import Optional, Union

import numpy as np

# Lazy import for sentence_transformers
_model = None

# Default model
DEFAULT_MODEL = "all-mpnet-base-v2"
EMBEDDING_DIM = 768

# Default cache path
DEFAULT_CACHE_PATH = Path.home() / ".talos" / "cache" / "embeddings"


def get_cache_path() -> Path:
    """Get embedding cache path."""
    env_path = os.environ.get("TALOS_EMBEDDING_CACHE")
    if env_path:
        return Path(env_path)
    return DEFAULT_CACHE_PATH


def get_model(model_name: Optional[str] = None):
    """Get or initialize the embedding model.

    Args:
        model_name: Model name. Uses default if not provided.

    Returns:
        SentenceTransformer model instance.
    """
    global _model

    if _model is not None:
        return _model

    from sentence_transformers import SentenceTransformer

    name = model_name or DEFAULT_MODEL
    cache_path = get_cache_path()
    cache_path.mkdir(parents=True, exist_ok=True)

    # Set cache directory
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(cache_path)

    _model = SentenceTransformer(name)
    return _model


def get_embedding(text: str, model_name: Optional[str] = None) -> list[float]:
    """Generate embedding for text.

    Args:
        text: Text to embed.
        model_name: Optional model name.

    Returns:
        List of floats (embedding vector).
    """
    model = get_model(model_name)
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def get_embeddings(texts: list[str], model_name: Optional[str] = None) -> list[list[float]]:
    """Generate embeddings for multiple texts.

    Args:
        texts: List of texts to embed.
        model_name: Optional model name.

    Returns:
        List of embedding vectors.
    """
    model = get_model(model_name)
    embeddings = model.encode(texts, convert_to_numpy=True)
    return [e.tolist() for e in embeddings]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Cosine similarity score.
    """
    a_np = np.array(a)
    b_np = np.array(b)
    return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))
