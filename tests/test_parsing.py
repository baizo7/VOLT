import json
import pytest
from main import parse_response


def test_parse_openai_non_streaming():
    data = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello, world!",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "get_time", "arguments": "{}"}
                        }
                    ]
                }
            }
        ],
        "usage": {"prompt_tokens": 12, "completion_tokens": 5}
    }
    raw = json.dumps(data).encode("utf-8")
    text, tools, usage = parse_response("openai", raw, streamed=False)
    assert text == "Hello, world!"
    assert len(tools) == 1
    assert tools[0]["function"]["name"] == "get_time"
    assert usage == {"in": 12, "out": 5}


def test_parse_anthropic_non_streaming():
    data = {
        "content": [
            {"type": "text", "text": "I can help with that."},
            {
                "type": "tool_use",
                "id": "toolu_123",
                "name": "lookup_user",
                "input": {"user_id": 42}
            }
        ],
        "usage": {"input_tokens": 20, "output_tokens": 15}
    }
    raw = json.dumps(data).encode("utf-8")
    text, tools, usage = parse_response("anthropic", raw, streamed=False)
    assert text == "I can help with that."
    assert len(tools) == 1
    assert tools[0]["id"] == "toolu_123"
    assert usage == {"in": 20, "out": 15}


def test_parse_openai_streaming_with_tool_calls():
    sse_lines = [
        'data: {"choices":[{"delta":{"role":"assistant","content":"Sure, "}}]}',
        'data: {"choices":[{"delta":{"content":"let me check."}}]}',
        'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_abc","type":"function","function":{"name":"fetch_weather","arguments":"{\\"ci"}}]}}]}',
        'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"ty\\": \\"Paris\\"}"}}]}}]}',
        'data: {"choices":[],"usage":{"prompt_tokens":10,"completion_tokens":8}}',
        'data: [DONE]'
    ]
    raw = "\n\n".join(sse_lines).encode("utf-8")
    text, tools, usage = parse_response("openai", raw, streamed=True)
    assert text == "Sure, let me check."
    assert len(tools) == 1
    assert tools[0]["id"] == "call_abc"
    assert tools[0]["function"]["name"] == "fetch_weather"
    assert tools[0]["function"]["arguments"] == '{"city": "Paris"}'
    assert usage == {"in": 10, "out": 8}


def test_parse_anthropic_streaming_with_tool_use():
    sse_lines = [
        'data: {"type":"message_start","message":{"usage":{"input_tokens":25}}}',
        'data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}',
        'data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Checking data..."}}',
        'data: {"type":"content_block_stop","index":0}',
        'data: {"type":"content_block_start","index":1,"content_block":{"type":"tool_use","id":"toolu_999","name":"query_db","input":{}}}',
        'data: {"type":"content_block_delta","index":1,"delta":{"type":"input_json_delta","partial_json":"{\\"query\\": "}}',
        'data: {"type":"content_block_delta","index":1,"delta":{"type":"input_json_delta","partial_json":"\\"SELECT 1\\"}"}}',
        'data: {"type":"content_block_stop","index":1}',
        'data: {"type":"message_delta","usage":{"output_tokens":14}}'
    ]
    raw = "\n".join(sse_lines).encode("utf-8")
    text, tools, usage = parse_response("anthropic", raw, streamed=True)
    assert text == "Checking data..."
    assert len(tools) == 1
    assert tools[0]["id"] == "toolu_999"
    assert tools[0]["name"] == "query_db"
    assert tools[0]["input"] == {"query": "SELECT 1"}
    assert usage == {"in": 25, "out": 14}


def test_parse_streaming_malformed_sse_and_missing_usage():
    sse_lines = [
        ': this is an sse comment',
        'data: {invalid json here!!}',
        'data: {"choices":[{"delta":{"content":"Resilient text"}}]}',
        'data: not json at all',
        'data: ',
        'random line without prefix'
    ]
    raw = "\n".join(sse_lines).encode("utf-8")
    text, tools, usage = parse_response("openai", raw, streamed=True)
    assert text == "Resilient text"
    assert tools == []
    assert usage == {}
