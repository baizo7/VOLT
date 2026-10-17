"""
ObserverCoder-1.0: Multi-Model Coordinator & Orchestration Engine.

Coordinates multiple independent open-weight models (with permissive Apache 2.0 / MIT licenses)
under a single unified assistant interface:
- Deep Reasoning / Architectural Planning: DeepSeek-R1 / Qwen2.5-Math (MIT / Apache 2.0)
- Fast Code Synthesis: Qwen2.5-Coder-1.5B (Apache 2.0, user's LoRA adapter)
- Heavy Systems Refactoring: Granite-3.0-8B-Code / Qwen2.5-Coder-7B (Apache 2.0)
- Multimodal / UI Inspection: Qwen2-VL-7B (Apache 2.0)
"""

import json
import logging
import os
import re
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse

from app.routing import resolve_route
from app.security import hash_api_key, mask_api_key
from app.storage import record_developer_key

logger = logging.getLogger("observer.coordinator")


class SpecialistExecutionError(Exception):
    """Raised when all candidate models for a specialist fail to execute."""

    def __init__(self, specialist_key: str, message: str, status_code: int = 502):
        super().__init__(message)
        self.specialist_key = specialist_key
        self.message = message
        self.status_code = status_code


# ────────── Permissive Open-Source Specialist Registry ──────────
SPECIALIST_CATALOG = {
    "fast_coder": {
        "model": "local/qwen2.5-coder:1.5b",
        "fallback_model": "qwen/qwen-2.5-coder-32b-instruct",
        "role": "Fast code generation and syntax synthesis (Apache 2.0)",
        "license": "Apache 2.0"
    },
    "heavy_coder": {
        "model": "local/qwen2.5-coder:7b",
        "fallback_model": "qwen/qwen-2.5-coder-32b-instruct",
        "role": "Complex systems refactoring and multi-file codebases (Apache 2.0)",
        "license": "Apache 2.0"
    },
    "deep_reasoner": {
        "model": "local/deepseek-r1:7b",
        "fallback_model": "deepseek-reasoner",
        "cloud_fallback": "qwen/qwen-2.5-coder-32b-instruct",
        "role": "Step-by-step chain-of-thought, algorithm design & reasoning (MIT)",
        "license": "MIT"
    },
    "math_specialist": {
        "model": "local/qwen2.5-math:7b",
        "fallback_model": "qwen/qwen-2.5-coder-32b-instruct",
        "role": "Mathematical proofs, numerical formulas & algorithmic proofs (Apache 2.0)",
        "license": "Apache 2.0"
    },
    "vision_specialist": {
        "model": "local/qwen2-vl:7b",
        "fallback_model": "qwen/qwen-2-vl-72b-instruct",
        "role": "UI screenshot analysis and visual inspection (Apache 2.0)",
        "license": "Apache 2.0"
    }
}


REASONING_KEYWORDS = {
    "architecture", "architect", "design pattern", "system design", "trade-off",
    "algorithm", "complexity", "time complexity", "space complexity", "step-by-step",
    "optimize algorithm", "proof", "mathematical", "concurrency", "race condition",
    "deadlock", "refactor system", "explain why", "root cause"
}

MATH_KEYWORDS = {
    "equation", "formula", "calculus", "linear algebra", "matrix", "probability",
    "statistics", "theorem", "lemma", "derivative", "integral", "eigenvalue"
}

CODER_SYSTEM_INSTRUCTION = (
    "You are VOLT-AI, an expert autonomous software engineer and full-stack developer.\n"
    "Your mission is to directly implement clean, complete, production-ready code that satisfies the user's request.\n"
    "\n"
    "CRITICAL RULES:\n"
    "1. DIRECT CODE GENERATION: When asked to build, create, develop, or write anything (websites, applications, scripts, APIs, tools), "
    "DO NOT provide generic marketing advice, high-level business steps, or recommend website builders like Wix, Squarespace, or WordPress. "
    "Immediately write the actual, fully functional code files.\n"
    "2. FILE LABELS: Always label code blocks with the target filename on the opening fence line, for example:\n"
    "   ```html index.html\n"
    "   <!DOCTYPE html>...\n"
    "   ```\n"
    "   ```css style.css\n"
    "   ...\n"
    "   ```\n"
    "   ```python app.py\n"
    "   ...\n"
    "   ```\n"
    "3. COMPLETE CODE: Always write full, working code without truncation or placeholders (avoid '<!-- add more items here -->').\n"
    "4. MODERN & VISUAL: For web pages, include modern CSS styling (embedded or in style.css) so the page looks professional immediately."
)


def analyze_intent(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze conversation messages to determine required specialist models and pipeline track:
    - 'vision': Image attached -> Qwen2-VL
    - 'math': Heavy mathematical reasoning -> Qwen2.5-Math
    - 'two_pass_reasoning': Algorithmic/architectural depth -> DeepSeek-R1 (Plan) + Qwen-Coder (Code)
    - 'fast_coding': Direct implementation/bugfix -> Qwen-Coder-1.5B (Fast execution)
    """
    if not messages:
        return {"track": "fast_coding", "specialists": ["fast_coder"], "reason": "Default single pass"}

    last_user_msg = ""
    has_image = False
    for m in reversed(messages):
        if m.get("role") == "user":
            content = m.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") in ("image_url", "image"):
                            has_image = True
                        elif part.get("type") == "text":
                            last_user_msg += " " + part.get("text", "")
            elif isinstance(content, str):
                last_user_msg += " " + content
            break

    if has_image:
        return {
            "track": "vision",
            "specialists": ["vision_specialist"],
            "reason": "Multimodal visual inputs detected"
        }

    lower_prompt = last_user_msg.lower()

    # Check math keywords
    if any(re.search(r"\b" + re.escape(w) + r"\b", lower_prompt) for w in MATH_KEYWORDS):
        return {
            "track": "two_pass_reasoning",
            "specialists": ["math_specialist", "fast_coder"],
            "reason": "Mathematical/numerical optimization detected; coordinating Math Reasoner + Coder"
        }

    # Check deep reasoning keywords
    reasoning_hits = [w for w in REASONING_KEYWORDS if re.search(r"\b" + re.escape(w) + r"\b", lower_prompt)]
    if len(reasoning_hits) >= 1 or len(lower_prompt.split()) > 180:
        return {
            "track": "two_pass_reasoning",
            "specialists": ["deep_reasoner", "heavy_coder"],
            "reason": f"Architectural reasoning required ({', '.join(reasoning_hits[:2]) if reasoning_hits else 'complex multi-turn'}); coordinating DeepSeek-R1 + Qwen-Coder"
        }

    # Default to fast direct coding with Qwen-Coder
    return {
        "track": "fast_coding",
        "specialists": ["fast_coder"],
        "reason": "Direct code generation or routine repair"
    }


_IN_MEMORY_DAILY_CALLS: Dict[str, List[float]] = {}


def get_in_memory_call_count(tracker_id: str) -> int:
    now = time.time()
    cutoff = now - 86400
    ts_list = _IN_MEMORY_DAILY_CALLS.get(tracker_id, [])
    ts_list = [t for t in ts_list if t >= cutoff]
    _IN_MEMORY_DAILY_CALLS[tracker_id] = ts_list
    return len(ts_list)


def record_in_memory_call(tracker_id: str):
    now = time.time()
    if tracker_id not in _IN_MEMORY_DAILY_CALLS:
        _IN_MEMORY_DAILY_CALLS[tracker_id] = []
    _IN_MEMORY_DAILY_CALLS[tracker_id].append(now)


async def count_recent_calls(pool: Any, session_id: str, tracker_id: str) -> int:
    mem_cnt = get_in_memory_call_count(tracker_id)
    if pool is None:
        return mem_cnt
    try:
        async with pool.acquire() as c:
            row = await c.fetchrow("""
                SELECT COUNT(*) as cnt
                FROM llm_calls
                WHERE ts >= NOW() - INTERVAL '24 hours'
                  AND session_id = $1
            """, session_id)
            db_cnt = int(row["cnt"]) if row else 0
            return max(db_cnt, mem_cnt)
    except Exception as e:
        logger.debug(f"Failed to query recent calls from DB: {e}")
        return mem_cnt


async def call_specialist(
    client: httpx.AsyncClient,
    specialist_key: str,
    messages: List[Dict[str, Any]],
    temperature: float = 0.2,
    max_tokens: Optional[int] = None,
    routes_map: Optional[Dict[str, Any]] = None,
    custom_system_prompt: Optional[str] = None,
    client_auth_header: Optional[str] = None,
) -> Tuple[str, int, int]:
    """
    Call a specialist model with resilient fallback:
    1. Try local model route if configured (e.g. Ollama/vLLM on http://127.0.0.1:8080/v1).
    2. Gracefully fall back to open-weight upstream if local runtime is unreachable.
    3. Forward client credentials (BYOK) if server environment credentials are missing.
    Returns: (text_content, input_tokens, output_tokens)
    Raises: SpecialistExecutionError if all candidates fail.
    """
    spec = SPECIALIST_CATALOG.get(specialist_key, SPECIALIST_CATALOG["fast_coder"])
    primary_model = spec["model"]
    fallback_model = spec["fallback_model"]

    payload_messages = list(messages)
    if custom_system_prompt:
        if payload_messages and payload_messages[0].get("role") == "system":
            payload_messages[0] = {"role": "system", "content": payload_messages[0]["content"] + "\n\n" + custom_system_prompt}
        else:
            payload_messages.insert(0, {"role": "system", "content": custom_system_prompt})

    candidate_models = [primary_model, fallback_model]
    if "cloud_fallback" in spec and spec["cloud_fallback"] not in candidate_models:
        candidate_models.append(spec["cloud_fallback"])

    last_err = None

    for target_model in candidate_models:
        route = resolve_route(target_model, "openai", routes_map)
        url = route["base_url"].rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        api_key = os.environ.get(route.get("api_key_env") or "")

        # BYOK: Prioritize user's provided direct provider API key so usage is billed to their account.
        # If client has a portal key (volt_live_...) or free starter tier, fall back to server env key.
        is_direct_provider_key = bool(
            client_auth_header
            and not ("volt_live_" in client_auth_header or "volt_" in client_auth_header)
        )
        if is_direct_provider_key and not target_model.startswith("local/"):
            headers["Authorization"] = client_auth_header
        elif api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        elif client_auth_header and not target_model.startswith("local/"):
            headers["Authorization"] = client_auth_header

        # Strip 'local/' prefix when transmitting model name to local runner
        wire_model = target_model[6:] if target_model.startswith("local/") else target_model

        body = {
            "model": wire_model,
            "messages": payload_messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens

        # Fail fast on local endpoints (5s timeout) so cloud fallbacks are not stalled
        timeout = 5.0 if target_model.startswith("local/") else 150.0

        try:
            resp = await client.post(url, json=body, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    choices = data.get("choices")
                    if choices and len(choices) > 0:
                        msg = choices[0].get("message") or {}
                        content = msg.get("content", "")
                        if content:
                            usage = data.get("usage", {})
                            in_tok = usage.get("prompt_tokens") or len(str(payload_messages)) // 4
                            out_tok = usage.get("completion_tokens") or len(content) // 4
                            return content, in_tok, out_tok
                    last_err = f"Upstream '{target_model}' returned 200 but response missing choices/content"
                    logger.warning(last_err)
                except Exception as parse_err:
                    last_err = f"Upstream '{target_model}' returned invalid JSON: {parse_err}"
                    logger.warning(last_err)
            else:
                last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
                logger.warning(f"Specialist '{target_model}' returned {resp.status_code}; trying candidate...")
        except Exception as e:
            last_err = str(e)
            logger.warning(f"Specialist call to '{target_model}' on '{url}' failed: {e}; trying candidate...")

    # All candidate models failed - raise informative error rather than returning fake 200
    logger.error(f"All specialist candidates failed for {specialist_key}. Last error: {last_err}")
    raise SpecialistExecutionError(
        specialist_key=specialist_key,
        message=f"All specialist candidates failed for {specialist_key}. Last error: {last_err}"
    )


async def coordinate_request(
    request: Request,
    body: Dict[str, Any],
    client: httpx.AsyncClient,
    pool: Any,
    project: Optional[str] = None,
    log_call_fn: Optional[Any] = None,
    routes_map: Optional[Dict[str, Any]] = None,
) -> Response:
    """
    VOLT-AI unified coordination entrypoint (with legacy ObserverCoder compatibility).
    Executes intent analysis, coordinates specialist worker models, and streams or returns standard response.
    """
    t0 = time.perf_counter()
    messages = body.get("messages", [])
    streamed = bool(body.get("stream", False))
    temperature = body.get("temperature", 0.2)
    max_tokens = body.get("max_tokens")

    requested_model = body.get("model", "VOLT-AI")
    if str(requested_model).lower().startswith("observer-coder"):
        out_model = "observer-coder-1.0"
    else:
        out_model = "VOLT-AI"

    decision = analyze_intent(messages)
    track = decision["track"]
    specialists = decision["specialists"]
    reason = decision["reason"]

    logger.info(f"VOLT-AI activated ({out_model}): track='{track}', specialists={specialists}, reason='{reason}'")

    # Extract client authorization (BYOK: Bring Your Own Key)
    observer_token = (
        os.environ.get("VOLT_AUTH_TOKEN")
        or os.environ.get("OBSERVER_AUTH_TOKEN")
        or os.environ.get("OBSERVER_TOKEN")
    )
    client_raw = (
        request.headers.get("authorization", "").strip()
        or request.headers.get("x-api-key", "").strip()
        or request.headers.get("x-volt-key", "").strip()
    )
    client_key = ""
    client_auth = None
    if client_raw:
        parts = client_raw.split(None, 1)
        client_key = parts[1] if (len(parts) == 2 and parts[0].lower() == "bearer") else client_raw
        if not (observer_token and client_key == observer_token):
            client_auth = client_raw if client_raw.lower().startswith("bearer ") else f"Bearer {client_raw}"

    # Identify Key Type:
    # 1. Portal Generated Key: starts with 'volt_live_' or 'volt_'
    # 2. BYOK Provider Key: e.g. OpenRouter, DeepSeek, Gemini, OpenAI
    # 3. No Key / Dummy Key: Free Starter Tier (Option 1)
    is_portal_key = bool(client_key and (client_key.startswith("volt_live_") or client_key.startswith("volt_")))
    dummy_keys = {"", "none", "null", "volt-cloud", "anonymous", "undefined"}
    is_missing_or_dummy = not client_key or client_key.lower() in dummy_keys or len(client_key) < 6

    dev_session = (
        request.headers.get("x-session-id")
        or request.headers.get("x-user")
        or request.headers.get("user")
        or (request.client.host if request.client else "anonymous-session")
    )
    effective_project = project or request.headers.get("x-project") or "default"

    free_tier_enabled = os.environ.get("VOLT_FREE_TIER", "1").lower() in ("1", "true", "yes")
    free_daily_limit = int(os.environ.get("VOLT_FREE_DAILY_LIMIT", "30"))
    portal_key_limit = int(os.environ.get("VOLT_PORTAL_KEY_LIMIT", "50"))

    tier_label = "byok_unlimited"
    free_remaining = None

    if is_portal_key:
        tier_label = "portal_key"
        k_hash = hash_api_key(client_key)
        tracker_id = f"portal:{k_hash}"
        recent_calls = await count_recent_calls(pool, session_id=dev_session, tracker_id=tracker_id)
        if recent_calls >= portal_key_limit:
            logger.warning(f"VOLT-AI Portal Key limit reached for key {client_key[:12]}: {recent_calls}/{portal_key_limit}")
            return JSONResponse(
                {
                    "error": {
                        "message": (
                            f"Daily quota reached for your VOLT API key ({recent_calls}/{portal_key_limit} requests today). "
                            "To get unlimited usage, enter your personal provider API key (OpenRouter, DeepSeek, or Gemini) "
                            "or visit the VOLT portal to manage your key: https://volt-ai-lmgz.onrender.com"
                        ),
                        "type": "quota_exceeded",
                        "code": 429,
                    }
                },
                status_code=429,
                headers={
                    "x-volt-tier": "portal_key",
                    "x-volt-free-remaining": "0",
                    "x-volt-quota-status": "exceeded",
                }
            )
        free_remaining = max(0, portal_key_limit - recent_calls - 1)

    elif is_missing_or_dummy:
        if free_tier_enabled:
            tracker_id = f"free:{dev_session}"
            recent_calls = await count_recent_calls(pool, session_id=dev_session, tracker_id=tracker_id)
            if recent_calls >= free_daily_limit:
                logger.warning(f"VOLT-AI Free Starter Tier limit reached for '{dev_session}': {recent_calls}/{free_daily_limit}")
                return JSONResponse(
                    {
                        "error": {
                            "message": (
                                f"You have reached your {free_daily_limit} free daily requests for the VOLT-AI community model. "
                                "To continue coding, generate a free API key at the website portal (https://volt-ai-lmgz.onrender.com) "
                                "or supply your own provider API key via 'volt activate'."
                            ),
                            "type": "quota_exceeded",
                            "code": 429,
                        }
                    },
                    status_code=429,
                    headers={
                        "x-volt-tier": "free_starter",
                        "x-volt-free-remaining": "0",
                        "x-volt-quota-status": "exceeded",
                    }
                )
            tier_label = "free_starter"
            free_remaining = max(0, free_daily_limit - recent_calls - 1)
        else:
            # Strict BYOK required when free tier is explicitly disabled
            logger.warning("VOLT-AI request rejected: Missing or invalid user API key (BYOK required).")
            return JSONResponse(
                {
                    "error": {
                        "message": (
                            "VOLT-AI operates on a Bring-Your-Own-Key (BYOK) model. "
                            "Please provide your own LLM provider API key (OpenRouter, DeepSeek, Gemini, or OpenAI) "
                            "in the 'Authorization: Bearer <your-key>' header or generate a free key via 'volt activate'."
                        ),
                        "type": "authentication_required",
                        "code": 401,
                        "param": "Authorization",
                    }
                },
                status_code=401,
                headers={
                    "WWW-Authenticate": 'Bearer realm="VOLT-AI BYOK"',
                    "x-volt-byok": "required",
                },
            )

    # Telemetry and Key Identity tracking for the Data Collection Pipeline
    k_masked = mask_api_key(client_key) if not is_missing_or_dummy else "free-tier"
    k_hash = hash_api_key(client_key) if not is_missing_or_dummy else "anonymous"

    provider = "custom"
    lower_k = client_key.lower() if client_key else ""
    if is_portal_key:
        provider = "volt-portal"
    elif "sk-or-" in lower_k or "openrouter" in lower_k:
        provider = "openrouter"
    elif "aiza" in lower_k:
        provider = "gemini"
    elif "sk-ant" in lower_k:
        provider = "anthropic"
    elif "deepseek" in lower_k:
        provider = "deepseek"
    elif "sk-" in lower_k:
        provider = "openai"
    elif tier_label == "free_starter":
        provider = "volt-free-starter"

    if pool is not None and k_hash != "anonymous":
        try:
            await record_developer_key(
                pool=pool,
                key_hash=k_hash,
                session_id=dev_session,
                project=effective_project,
                key_masked=k_masked,
                provider=provider,
                model=out_model,
            )
        except Exception as k_err:
            logger.warning(f"Failed to record developer key in coordinator: {k_err}")

    total_in = 0
    total_out = 0
    final_text = ""
    reasoning_blueprint = ""

    try:
        if track == "two_pass_reasoning":
            reasoner_key = specialists[0]
            coder_key = specialists[1] if len(specialists) > 1 else "fast_coder"

            # Pass 1: Reasoner analyzes problem and outputs architectural strategy
            reasoning_prompt = (
                "You are the Architectural & Reasoning Specialist for ObserverCoder-1.0. "
                "Analyze the problem thoroughly. Provide a concise, step-by-step implementation plan, "
                "algorithmic design, and identify edge cases. Do NOT write full code, focus on the strategy."
            )
            plan, in1, out1 = await call_specialist(
                client=client,
                specialist_key=reasoner_key,
                messages=messages,
                temperature=0.3,
                max_tokens=600,
                routes_map=routes_map,
                custom_system_prompt=reasoning_prompt,
                client_auth_header=client_auth,
            )
            total_in += in1
            total_out += out1
            reasoning_blueprint = plan

            # Pass 2: Coder implements the solution based on the reasoning blueprint
            coder_system = (
                CODER_SYSTEM_INSTRUCTION + "\n\n"
                f"Here is the verified architectural strategy from our Reasoning Specialist:\n"
                f"<strategy>\n{reasoning_blueprint}\n</strategy>\n\n"
                "Now write clean, modular, production-ready code implementing this exact plan."
            )
            code_res, in2, out2 = await call_specialist(
                client=client,
                specialist_key=coder_key,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                routes_map=routes_map,
                custom_system_prompt=coder_system,
                client_auth_header=client_auth,
            )
            total_in += in2
            total_out += out2
            final_text = code_res

        else:
            # Fast direct track: Vision or Fast Coder
            specialist_key = specialists[0]
            custom_prompt = None
            if specialist_key in ("fast_coder", "heavy_coder"):
                custom_prompt = CODER_SYSTEM_INSTRUCTION
            elif specialist_key == "vision_specialist":
                custom_prompt = (
                    "You are the Multimodal UI Specialist for ObserverCoder-1.0. "
                    "Analyze the provided image and generate matching, production-ready frontend code. "
                    "Label every code block with its target filename (e.g. ```html index.html```)."
                )

            res, in_tok, out_tok = await call_specialist(
                client=client,
                specialist_key=specialist_key,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                routes_map=routes_map,
                custom_system_prompt=custom_prompt,
                client_auth_header=client_auth,
            )
            total_in += in_tok
            total_out += out_tok
            final_text = res


    except SpecialistExecutionError as err:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        task_id = request.headers.get("x-task-id") or str(uuid.uuid4())
        call_meta = {
            "id": str(uuid.uuid4()),
            "project": effective_project,
            "task_id": task_id,
            "session_id": dev_session,
            "task_type": "coding:volt_coordinated",
            "model": out_model,
            "upstream": "internal:coordinator",
            "style": "openai",
            "streamed": streamed,
            "request": body,
            "response_text": "",
            "tool_calls": [],
            "status_code": 502,
            "latency_ms": latency_ms,
            "error": err.message,
            "in": 0,
            "out": 0,
        }
        if log_call_fn:
            try:
                await log_call_fn(call_meta)
            except Exception as log_err:
                logger.warning(f"Coordinator error logging notice: {log_err}")

        error_headers = {
            "x-volt-model": out_model,
            "x-observer-model": out_model,
            "x-volt-track": track,
            "x-observer-track": track,
            "x-volt-specialists": ",".join(specialists),
            "x-observer-specialists": ",".join(specialists),
            "x-volt-latency-ms": str(latency_ms),
            "x-observer-latency-ms": str(latency_ms),
            "x-volt-byok": "active",
            "x-volt-data-collection": "active",
        }
        brand_label = "ObserverCoder" if out_model == "observer-coder-1.0" else "VOLT-AI"
        return JSONResponse(
            {
                "error": {
                    "message": f"{brand_label} specialist execution failed: {err.message}",
                    "type": "upstream_specialist_error",
                    "code": 502,
                    "specialist": err.specialist_key,
                }
            },
            status_code=502,
            headers=error_headers,
        )

    latency_ms = int((time.perf_counter() - t0) * 1000)

    # Persist coordinated trace to telemetry
    task_id = request.headers.get("x-task-id") or str(uuid.uuid4())
    call_meta = {
        "id": str(uuid.uuid4()),
        "project": effective_project,
        "task_id": task_id,
        "session_id": dev_session,
        "task_type": "coding:volt_coordinated",
        "model": out_model,
        "upstream": "internal:coordinator",
        "style": "openai",
        "streamed": streamed,
        "request": body,
        "response_text": final_text,
        "tool_calls": [],
        "status_code": 200,
        "latency_ms": latency_ms,
        "error": None,
        "in": total_in,
        "out": total_out,
    }

    if log_call_fn:
        try:
            await log_call_fn(call_meta)
        except Exception as log_err:
            logger.warning(f"Coordinator logging notice: {log_err}")

    # Record in-memory usage for instant quota evaluation
    if tier_label == "free_starter":
        record_in_memory_call(f"free:{dev_session}")
    elif tier_label == "portal_key":
        record_in_memory_call(f"portal:{k_hash}")

    # Build standard OpenAI response object
    resp_id = "chatcmpl-" + uuid.uuid4().hex[:12]
    created_ts = int(time.time())

    headers = {
        "x-volt-model": out_model,
        "x-observer-model": out_model,
        "x-volt-track": track,
        "x-observer-track": track,
        "x-volt-specialists": ",".join(specialists),
        "x-observer-specialists": ",".join(specialists),
        "x-volt-latency-ms": str(latency_ms),
        "x-observer-latency-ms": str(latency_ms),
        "x-volt-tier": tier_label,
        "x-volt-byok": "active" if tier_label == "byok_unlimited" else "free_tier",
        "x-volt-data-collection": "active",
    }
    if free_remaining is not None:
        headers["x-volt-free-remaining"] = str(free_remaining)

    if streamed:
        async def stream_generator() -> AsyncGenerator[bytes, None]:
            # Initial chunk with role
            first_chunk = {
                "id": resp_id,
                "object": "chat.completion.chunk",
                "created": created_ts,
                "model": out_model,
                "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
            }
            yield f"data: {json.dumps(first_chunk)}\n\n".encode("utf-8")

            # Word-by-word streaming for smooth IDE typing effect
            words = final_text.split(" ")
            for i, word in enumerate(words):
                token_text = word if i == 0 else " " + word
                chunk = {
                    "id": resp_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": out_model,
                    "choices": [{"index": 0, "delta": {"content": token_text}, "finish_reason": None}]
                }
                yield f"data: {json.dumps(chunk)}\n\n".encode("utf-8")

            final_chunk = {
                "id": resp_id,
                "object": "chat.completion.chunk",
                "created": created_ts,
                "model": out_model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n".encode("utf-8")
            yield b"data: [DONE]\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers=headers
        )

    coordination_details = {
        "track": track,
        "specialists_used": specialists,
        "reason": reason,
        "latency_ms": latency_ms,
        "has_reasoning_pass": bool(reasoning_blueprint)
    }

    response_payload = {
        "id": resp_id,
        "object": "chat.completion",
        "created": created_ts,
        "model": out_model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": final_text
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": total_in,
            "completion_tokens": total_out,
            "total_tokens": total_in + total_out
        },
        "volt_coordination": coordination_details,
        "observer_coordination": coordination_details
    }

    return JSONResponse(response_payload, headers=headers)
