import json
import pytest
import httpx
import main


class MockAsyncStream(httpx.AsyncByteStream):
    def __init__(self, chunks):
        self.chunks = chunks

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk


@pytest.mark.asyncio
async def test_streaming_bound_capture(async_client, monkeypatch):
    # Set MAX_CHARS to a small value for testing
    cap = 1000
    monkeypatch.setattr(main, "MAX_CHARS", cap)

    # Generate 50 chunks of 100 bytes = 5000 bytes (greater than cap of 1000)
    chunk_piece = b"x" * 100
    num_chunks = 50
    total_bytes = 100 * num_chunks

    logged_record = {}

    async def mock_log_call(rec):
        logged_record.update(rec)

    monkeypatch.setattr(main, "log_call", mock_log_call)

    def mock_handler(request: httpx.Request):
        chunks = [chunk_piece for _ in range(num_chunks)]
        return httpx.Response(200, stream=MockAsyncStream(chunks))

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    monkeypatch.setattr(main, "client", mock_client)

    payload = {"model": "gpt-4", "stream": True, "messages": []}
    resp = await async_client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200

    # The client receives the entire stream unmodified
    client_body = resp.content
    assert len(client_body) == total_bytes

    # Stored response text is capped by MAX_STORED_CHARS
    stored_text = logged_record.get("response_text", "")
    assert len(stored_text) <= cap


@pytest.mark.asyncio
async def test_streaming_openai_tool_calls(async_client, monkeypatch):
    logged_record = {}

    async def mock_log_call(rec):
        logged_record.update(rec)

    monkeypatch.setattr(main, "log_call", mock_log_call)

    sse_chunks = [
        b'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_123","type":"function","function":{"name":"calc","arguments":"{\\"a\\":1"}}]}}]}\n\n',
        b'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":",\\"b\\":2}"}}]}}]}\n\n',
        b'data: [DONE]\n\n'
    ]

    def mock_handler(request: httpx.Request):
        return httpx.Response(
            200,
            stream=MockAsyncStream(sse_chunks),
            headers={"content-type": "text/event-stream"}
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    monkeypatch.setattr(main, "client", mock_client)

    payload = {"model": "gpt-4", "stream": True, "messages": []}
    resp = await async_client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200

    assert "tool_calls" in logged_record
    tools = logged_record["tool_calls"]
    assert len(tools) == 1
    assert tools[0]["id"] == "call_123"
    assert tools[0]["function"]["name"] == "calc"
    assert tools[0]["function"]["arguments"] == '{"a":1,"b":2}'


@pytest.mark.asyncio
async def test_streaming_anthropic_tool_calls(async_client, monkeypatch):
    logged_record = {}

    async def mock_log_call(rec):
        logged_record.update(rec)

    monkeypatch.setattr(main, "log_call", mock_log_call)

    sse_chunks = [
        b'data: {"type":"content_block_start","index":0,"content_block":{"type":"tool_use","id":"toolu_abc","name":"fetch","input":{}}}\n',
        b'data: {"type":"content_block_delta","index":0,"delta":{"type":"input_json_delta","partial_json":"{\\"id\\":42}"}}\n',
        b'data: {"type":"content_block_stop","index":0}\n'
    ]

    def mock_handler(request: httpx.Request):
        return httpx.Response(
            200,
            stream=MockAsyncStream(sse_chunks),
            headers={"content-type": "text/event-stream"}
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    monkeypatch.setattr(main, "client", mock_client)

    payload = {"model": "claude-3-5-sonnet", "stream": True, "messages": []}
    resp = await async_client.post("/v1/messages", json=payload)
    assert resp.status_code == 200

    assert "tool_calls" in logged_record
    tools = logged_record["tool_calls"]
    assert len(tools) == 1
    assert tools[0]["id"] == "toolu_abc"
    assert tools[0]["name"] == "fetch"
    assert tools[0]["input"] == {"id": 42}
