"""
Embedding generation service for AI Model Observer.
Generates 1536-dimensional embeddings for pgvector storage and semantic search.
Uses OpenAI/OpenRouter embedding API when configured, with a deterministic offline
fallback for local development and testing.
"""
import hashlib
import math
import os
from typing import List, Optional
import httpx
from app.config import logger

EMBEDDING_DIM = 1536
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_EMBEDDING_URL = "https://api.openai.com/v1/embeddings"
OPENROUTER_EMBEDDING_URL = "https://openrouter.ai/api/v1/embeddings"


def generate_deterministic_vector(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Generate a deterministic, unit-normalized float vector from text.
    Provides a zero-dependency fallback for local/test environments.
    """
    if not text:
        vec = [0.0] * dim
        vec[0] = 1.0
        return vec

    # Hash chunks of the text into pseudo-random numbers
    vec = []
    text_bytes = text.encode("utf-8")
    for i in range(dim):
        h = hashlib.sha256(text_bytes + i.to_bytes(4, byteorder="big")).digest()
        # Map 4 bytes to float between -1.0 and 1.0
        val = int.from_bytes(h[:4], byteorder="big", signed=True) / (2**31)
        vec.append(val)

    # Normalize to unit length (L2 norm)
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


async def get_embedding(
    text: str,
    client: Optional[httpx.AsyncClient] = None
) -> List[float]:
    """
    Get 1536-dim embedding vector for text.
    Uses OpenAI or OpenRouter if API keys are set, otherwise uses deterministic vector.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return generate_deterministic_vector("", EMBEDDING_DIM)

    openai_key = os.environ.get("OPENAI_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")

    if not openai_key and not openrouter_key:
        return generate_deterministic_vector(cleaned, EMBEDDING_DIM)

    url = OPENAI_EMBEDDING_URL if openai_key else OPENROUTER_EMBEDDING_URL
    api_key = openai_key or openrouter_key
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": cleaned[:8000],  # Bound input size
        "model": EMBEDDING_MODEL
    }

    should_close = False
    http_client = client
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=10.0)
        should_close = True

    try:
        resp = await http_client.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            embedding = data.get("data", [{}])[0].get("embedding")
            if embedding and len(embedding) == EMBEDDING_DIM:
                return embedding
        logger.warning(f"Embedding API returned status {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"Embedding request failed ({e}); falling back to deterministic vector.")
    finally:
        if should_close:
            await http_client.aclose()

    return generate_deterministic_vector(cleaned, EMBEDDING_DIM)
