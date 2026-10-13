import math
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.embeddings import generate_deterministic_vector, get_embedding, EMBEDDING_DIM


def test_deterministic_vector_properties():
    vec1 = generate_deterministic_vector("hello world")
    assert len(vec1) == EMBEDDING_DIM

    # Vector is normalized to unit length
    magnitude = math.sqrt(sum(x * x for x in vec1))
    assert math.isclose(magnitude, 1.0, rel_tol=1e-5)

    # Determinism: same input yields identical vector
    vec2 = generate_deterministic_vector("hello world")
    assert vec1 == vec2

    # Different inputs yield different vectors
    vec3 = generate_deterministic_vector("different text")
    assert vec1 != vec3


@pytest.mark.asyncio
async def test_get_embedding_offline_fallback(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    vec = await get_embedding("test prompt")
    assert len(vec) == EMBEDDING_DIM
    magnitude = math.sqrt(sum(x * x for x in vec))
    assert math.isclose(magnitude, 1.0, rel_tol=1e-5)


@pytest.mark.asyncio
async def test_get_embedding_with_api_mock(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-mock-key")

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"embedding": [0.5] * EMBEDDING_DIM}]
    }
    mock_client.post = AsyncMock(return_value=mock_resp)

    vec = await get_embedding("hello", client=mock_client)
    assert len(vec) == EMBEDDING_DIM
    assert vec[0] == 0.5
    assert mock_client.post.called
