"""
Response parsing utilities for OpenAI and Anthropic API formats (streaming and non-streaming).
"""
import json
from typing import Tuple, List, Dict, Any


def parse_response(style: str, raw: bytes, streamed: bool) -> Tuple[str, List[Any], Dict[str, Any]]:
    """
    Parse text, tool calls, and token usage from raw provider response bytes.
    Best-effort parsing; fails gracefully to empty values without raising exceptions.
    """
    text, tools, usage = [], [], {}
    body = raw.decode("utf-8", "replace")
    try:
        if not streamed:
            d = json.loads(body)
            if style == "openai":
                msg = (d.get("choices") or [{}])[0].get("message", {})
                text.append(msg.get("content") or "")
                tools = msg.get("tool_calls") or []
                u = d.get("usage") or {}
                usage = {"in": u.get("prompt_tokens"), "out": u.get("completion_tokens")}
            elif style == "gemini":
                for candidate in d.get("candidates") or []:
                    content = candidate.get("content") or {}
                    for part in content.get("parts") or []:
                        if not isinstance(part, dict):
                            continue
                        if part.get("text"):
                            text.append(part["text"])
                        call = part.get("functionCall")
                        if call:
                            tools.append({
                                "type": "function_call",
                                "name": call.get("name", ""),
                                "args": call.get("args") or {},
                            })
                u = d.get("usageMetadata") or {}
                usage = {
                    "in": u.get("promptTokenCount"),
                    "out": u.get("candidatesTokenCount"),
                }
            else:
                for b in d.get("content", []):
                    if b.get("type") == "text":
                        text.append(b.get("text", ""))
                    elif b.get("type") == "tool_use":
                        tools.append(b)
                u = d.get("usage") or {}
                usage = {"in": u.get("input_tokens"), "out": u.get("output_tokens")}
        else:
            openai_tools = {}
            anthropic_tools = {}
            gemini_tools = []
            for line in body.splitlines():
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if not payload or payload == "[DONE]":
                    continue
                try:
                    d = json.loads(payload)
                except Exception:
                    continue
                if not isinstance(d, dict):
                    continue

                if style == "openai":
                    for ch in d.get("choices") or []:
                        delta = ch.get("delta") or {}
                        if delta.get("content"):
                            text.append(delta["content"])
                        for tc in delta.get("tool_calls") or []:
                            idx = tc.get("index", 0)
                            if idx not in openai_tools:
                                openai_tools[idx] = {
                                    "id": tc.get("id", ""),
                                    "type": tc.get("type", "function"),
                                    "function": {
                                        "name": (tc.get("function") or {}).get("name", ""),
                                        "arguments": (tc.get("function") or {}).get("arguments", ""),
                                    }
                                }
                            else:
                                if tc.get("id"):
                                    openai_tools[idx]["id"] = tc["id"]
                                if tc.get("type"):
                                    openai_tools[idx]["type"] = tc["type"]
                                fn = tc.get("function")
                                if fn:
                                    if fn.get("name"):
                                        openai_tools[idx]["function"]["name"] = (
                                            openai_tools[idx]["function"]["name"] or ""
                                        ) + fn["name"]
                                    if fn.get("arguments"):
                                        openai_tools[idx]["function"]["arguments"] = (
                                            openai_tools[idx]["function"]["arguments"] or ""
                                        ) + fn["arguments"]
                    if d.get("usage"):
                        usage = {"in": d["usage"].get("prompt_tokens"), "out": d["usage"].get("completion_tokens")}
                elif style == "gemini":
                    for candidate in d.get("candidates") or []:
                        content = candidate.get("content") or {}
                        for part in content.get("parts") or []:
                            if not isinstance(part, dict):
                                continue
                            if part.get("text"):
                                text.append(part["text"])
                            call = part.get("functionCall")
                            if call:
                                gemini_tools.append({
                                    "type": "function_call",
                                    "name": call.get("name", ""),
                                    "args": call.get("args") or {},
                                })
                    u = d.get("usageMetadata") or {}
                    if "promptTokenCount" in u:
                        usage["in"] = u.get("promptTokenCount")
                    if "candidatesTokenCount" in u:
                        usage["out"] = u.get("candidatesTokenCount")
                else:  # anthropic
                    t = d.get("type")
                    if t == "content_block_start":
                        idx = d.get("index", 0)
                        cb = d.get("content_block") or {}
                        if cb.get("type") == "tool_use":
                            anthropic_tools[idx] = {
                                "type": "tool_use",
                                "id": cb.get("id", ""),
                                "name": cb.get("name", ""),
                                "input_parts": []
                            }
                    elif t == "content_block_delta":
                        delta = d.get("delta") or {}
                        if delta.get("type") == "text_delta":
                            text.append(delta.get("text", ""))
                        elif delta.get("type") == "input_json_delta":
                            idx = d.get("index", 0)
                            if idx in anthropic_tools:
                                anthropic_tools[idx]["input_parts"].append(delta.get("partial_json", ""))
                    elif t == "message_start":
                        usage["in"] = (d.get("message", {}).get("usage") or {}).get("input_tokens")
                    elif t == "message_delta":
                        usage["out"] = (d.get("usage") or {}).get("output_tokens")

            if style == "openai" and openai_tools:
                tools = [openai_tools[k] for k in sorted(openai_tools.keys())]
            elif style == "gemini" and gemini_tools:
                tools = gemini_tools
            elif style == "anthropic" and anthropic_tools:
                for idx in sorted(anthropic_tools.keys()):
                    item = anthropic_tools[idx]
                    joined_input = "".join(item["input_parts"])
                    try:
                        parsed_input = json.loads(joined_input) if joined_input else {}
                    except Exception:
                        parsed_input = joined_input
                    tools.append({
                        "type": "tool_use",
                        "id": item["id"],
                        "name": item["name"],
                        "input": parsed_input
                    })
    except Exception:
        pass  # Never let parsing exceptions break proxy delivery
    return "".join(text), tools, usage
