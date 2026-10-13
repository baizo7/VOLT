"""Opt-in text-only adapter for the local OpenCode server."""

import asyncio
import os
import re
import time
from urllib.parse import urlsplit


class OpenCodeInputError(ValueError):
    """The request cannot be represented by the text-only adapter."""


def _token_count(value):
    """Return a safe, non-negative token count."""
    if isinstance(value, bool):
        return 0
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


def _server_auth():
    """Read local OpenCode server credentials from environment variables."""
    password = os.environ.get("OPENCODE_SERVER_PASSWORD")
    username = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")
    if not password:
        raise RuntimeError("OPENCODE_SERVER_PASSWORD is not configured.")
    if not username.strip():
        raise RuntimeError("OPENCODE_SERVER_USERNAME cannot be empty.")
    return (username, password)

async def _interrupt_session(client, base_url, session_id):
    """Try to stop active generation without deleting session history."""
    try:
        response = await client.post(
            f"{base_url}/api/session/{session_id}/interrupt",
            timeout=5.0,
            auth=_server_auth(),
        )
        response.raise_for_status()
    except Exception:
        # Preserve the original request failure; interruption is best-effort.
        pass


async def call_opencode(client, model, messages):
    base_url = os.environ.get(
        "OPENCODE_SERVER_URL", "http://127.0.0.1:4096"
    ).rstrip("/")
    parsed = urlsplit(base_url)

    try:
        port = parsed.port
    except ValueError:
        port = None
        invalid_port = True
    else:
        invalid_port = False

    if (
        parsed.scheme != "http"
        or parsed.hostname not in ("127.0.0.1", "localhost", "::1")
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
        or invalid_port
        or (port is not None and not 1 <= port <= 65535)
    ):
        raise RuntimeError(
            "OPENCODE_SERVER_URL must point to a local HTTP server."
        )

    if not isinstance(model, str) or not model.startswith("opencode/"):
        raise OpenCodeInputError("An OpenCode catalogue model is required.")

    if not isinstance(messages, list) or not messages:
        raise OpenCodeInputError("A non-empty messages array is required.")

    prompt_parts = []
    allowed_roles = {"system", "developer", "user", "assistant"}

    for message in messages:
        if not isinstance(message, dict):
            raise OpenCodeInputError("Each message must be an object.")

        role = message.get("role", "user")
        if not isinstance(role, str) or role not in allowed_roles:
            raise OpenCodeInputError("This message role is not supported.")

        if (
            message.get("tool_calls")
            or message.get("function_call")
            or role in ("tool", "function")
        ):
            raise OpenCodeInputError(
                "Tool messages and tool calls are not supported."
            )

        content = message.get("content")
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            pieces = []
            for part in content:
                if (
                    not isinstance(part, dict)
                    or part.get("type") != "text"
                    or not isinstance(part.get("text"), str)
                ):
                    raise OpenCodeInputError(
                        "Only text content is supported; images and other "
                        "multimodal parts are not supported."
                    )
                pieces.append(part["text"])
            text = "\n".join(pieces)
        else:
            raise OpenCodeInputError(
                "Each message must contain text-only content."
            )

        prompt_parts.append(f"{role.upper()}:\n{text}")

    prompt_text = "\n\n".join(prompt_parts)
    model_id = model.removeprefix("opencode/").strip()

    if not model_id or len(model_id) > 200:
        raise OpenCodeInputError("The OpenCode model ID is invalid.")

    started = time.time()

    session_response = await client.post(
        f"{base_url}/api/session",
        json={
            "agent": "observer-text-only",
            "model": {
                "providerID": "opencode",
                "id": model_id,
            },
        },
        timeout=30.0,
        auth=_server_auth(),
    )
    session_response.raise_for_status()

    try:
        session_data = session_response.json().get("data", {})
    except (ValueError, AttributeError):
        raise RuntimeError("OpenCode returned an invalid session response.") from None

    session_id = (
        session_data.get("id") if isinstance(session_data, dict) else None
    )
    if (
        not isinstance(session_id, str)
        or not re.fullmatch(r"ses[A-Za-z0-9_-]{6,128}", session_id)
    ):
        raise RuntimeError("OpenCode returned an invalid session ID.")

    # From this point onward, failures trigger a best-effort interruption.
    try:
        prompt_response = await client.post(
            f"{base_url}/api/session/{session_id}/prompt",
            json={"prompt": {"text": prompt_text}},
            timeout=600.0,
            auth=_server_auth(),
        )
        prompt_response.raise_for_status()

        wait_response = await client.post(
            f"{base_url}/api/session/{session_id}/wait",
            timeout=600.0,
            auth=_server_auth(),
        )
        wait_response.raise_for_status()

        messages_response = await client.get(
            f"{base_url}/api/session/{session_id}/message",
            timeout=30.0,
        auth=_server_auth(),
        )
        messages_response.raise_for_status()

        payload = messages_response.json()
        message_items = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(message_items, list):
            raise RuntimeError("OpenCode returned an invalid message list.")

        assistant = next(
            (
                item for item in reversed(message_items)
                if isinstance(item, dict) and item.get("type") == "assistant"
            ),
            None,
        )
        if assistant is None:
            raise RuntimeError("OpenCode returned no assistant message.")

        content = assistant.get("content", [])
        if not isinstance(content, list):
            raise RuntimeError("OpenCode returned invalid assistant content.")

        text_parts = []
        for part in content:
            if not isinstance(part, dict):
                raise RuntimeError("OpenCode returned an invalid content part.")
            if part.get("type") == "text":
                value = part.get("text")
                if not isinstance(value, str):
                    raise RuntimeError("OpenCode returned invalid text content.")
                text_parts.append(value)

        answer = "\n".join(text_parts).strip()
        if not answer:
            raise RuntimeError("OpenCode returned no text answer.")

        tokens = assistant.get("tokens")
        if not isinstance(tokens, dict):
            tokens = {}

        prompt_tokens = _token_count(tokens.get("input"))
        completion_tokens = _token_count(tokens.get("output"))

        return {
            "id": f"chatcmpl-{session_id}",
            "object": "chat.completion",
            "created": int(started),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": answer},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }

    except asyncio.CancelledError:
        # Let interruption continue even if the caller is being cancelled.
        try:
            await asyncio.shield(
                _interrupt_session(client, base_url, session_id)
            )
        except asyncio.CancelledError:
            pass
        raise
    except Exception:
        await _interrupt_session(client, base_url, session_id)
        raise

