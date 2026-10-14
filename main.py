"""
AI Model Observer - Main application entrypoint and reverse proxy.

Sits between your coding tools and model providers, forwards requests unchanged,
and logs a scrubbed record of every call to PostgreSQL.

Endpoints:
  POST /v1/chat/completions       OpenAI-compatible (OpenCode, DeepSeek, OpenRouter...)
  POST /v1/messages               Anthropic Messages API (Claude CLI via ANTHROPIC_BASE_URL)
  POST /p/{project}/v1/...        Project-scoped proxy routes
  POST /outcomes                  Report build/test/feedback results for a task
  GET  /stats                     Per-model summary with last-touch outcome attribution
  GET  /health                    Health readiness check (database-aware)
  GET  /tasks                     Recent tasks list and status
  GET  /tasks/{task_id}           Full audit trace for a specific task
  GET  /dashboard, GET /          Interactive analytics dashboard
  POST /admin/prune               Retention policy cleanup
  POST /knowledge/solutions       Index verified solution (pgvector)
  POST /knowledge/search          Retrieve similar past solutions (semantic search)
"""
import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, List, Optional

import asyncpg
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

# Modular component imports
from app.config import (
    DATABASE_URL,
    DEFAULT_BASE,
    MAX_CHARS,
    MAX_REQUEST_BYTES,
    ROUTES_FILE,
    SKIP_REQ_HEADERS,
    SKIP_RESP_HEADERS,
    UPSTREAM_PATH,
    logger,
)
from app.dashboard import DASHBOARD_HTML
from app.dataset import (
    compute_dataset_summary,
    export_dpo_dataset,
    export_sft_dataset,
    split_dataset,
)
from app.embeddings import get_embedding
from app.knowledge import (
    index_solution,
    search_solutions_by_embedding,
    search_solutions_by_text,
    validate_embedding_vector,
)
from app.parsing import parse_response
from app.opencode_adapter import call_opencode, OpenCodeInputError
from app.rag import (
    augment_anthropic_request,
    augment_openai_request,
    extract_prompt_text,
)
from app.router import resolve_dynamic_route, select_optimal_model
from app.routing import load_routes
from app.routing import resolve_route as _resolve_route
from app.security import (
    SECRET_PATTERNS,
    check_auth,
    scrub_json,
    scrub_record,
    scrub_text,
)
from app.storage import (
    check_health,
    fetch_stats,
    fetch_task_details,
    fetch_tasks,
    prune_records,
    record_outcome,
    save_llm_call,
)

# ---------- Pydantic request models ----------
class OutcomeRequest(BaseModel):
    task_id: str
    kind: str
    status: str
    details: Optional[dict[str, Any]] = None
    idempotency_key: Optional[str] = None


class SolutionIndexRequest(BaseModel):
    task_id: str
    problem_summary: str
    solution_code: str
    task_type: Optional[str] = None
    project: Optional[str] = None
    outcome_status: str = "pass"
    embedding: Optional[List[float]] = None


class SolutionSearchRequest(BaseModel):
    query_text: Optional[str] = None
    query_embedding: Optional[List[float]] = None
    limit: int = 5
    task_type: Optional[str] = None
    project: Optional[str] = None


class DatasetExportRequest(BaseModel):
    dataset_type: str = "sft"  # "sft" or "dpo"
    project: Optional[str] = None
    task_type: Optional[str] = None
    val_split: float = 0.1
    limit: Optional[int] = 1000
    deduplicate: bool = True


# ---------- application state & lifespan ----------
routes = load_routes()
pool: Optional[asyncpg.Pool] = None
client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app):
    global pool, client, routes
    try:
        clean_db_url = DATABASE_URL
        ssl_ctx = None
        if "sslmode=" in clean_db_url:
            clean_db_url = clean_db_url.split("?sslmode=")[0].split("&sslmode=")[0]
            ssl_ctx = "require"
        elif clean_db_url and "localhost" not in clean_db_url and "127.0.0.1" not in clean_db_url:
            ssl_ctx = "require"

        pool = await asyncpg.create_pool(clean_db_url, min_size=1, max_size=10, ssl=ssl_ctx)

        # Idempotently apply schema.sql so cloud databases (Supabase/Neon) are initialized automatically
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema_content = f.read()
                async with pool.acquire() as conn:
                    await conn.execute(schema_content)
                logger.info("Database schema verified and applied.")
            except Exception as schema_err:
                logger.warning(f"Schema initialization notice: {schema_err}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        pool = None
    client = httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=15.0))
    routes = load_routes(ROUTES_FILE)
    yield
    if client:
        await client.aclose()
    if pool:
        await pool.close()


app = FastAPI(title="AI Model Observer", lifespan=lifespan)


def resolve_route(model: str, style: str):
    """Resolve route using the active routes dictionary."""
    return _resolve_route(model, style, routes)


async def log_call(rec: dict):
    """Persist scrubbed call record to database."""
    await save_llm_call(pool, rec, MAX_CHARS)


# ---------- proxy logic ----------
async def proxy(request: Request, style: str, project: str = None):
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    # Enforce request payload size limit before buffering into memory
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_BYTES:
                return JSONResponse({"error": "Payload Too Large: request exceeds size limit"}, status_code=413)
        except ValueError:
            pass

    raw = await request.body()
    if len(raw) > MAX_REQUEST_BYTES:
        return JSONResponse({"error": "Payload Too Large: request exceeds size limit"}, status_code=413)

    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)

    if not isinstance(body, dict):
        return JSONResponse({"error": "Request body must be a JSON object"}, status_code=400)

    requested_model = body.get("model", "unknown")
    if isinstance(requested_model, str) and requested_model.startswith("opencode/"):
        # Keep OpenCode catalogue models out of dynamic provider routing.
        model = requested_model
    else:
        route_decision = await resolve_dynamic_route(
            pool=pool,
            requested_model=requested_model,
            headers=request.headers,
        )
        model = route_decision.selected_model
        if model != requested_model:
            logger.info(f"Router resolved '{requested_model}' -> '{model}' ({route_decision.reason})")
            body["model"] = model
            raw = json.dumps(body).encode("utf-8")

    streamed = bool(body.get("stream"))
    route = resolve_route(model, style)
    url = route["base_url"].rstrip("/") + UPSTREAM_PATH[style]
    if style == "anthropic" and route["base_url"].rstrip("/").endswith("/v1"):
        url = route["base_url"].rstrip("/") + "/messages"

    # Optional RAG prompt augmentation with verified past solutions (scoped to project)
    effective_project = project or request.headers.get("x-project")
    inject_rag = (
        request.headers.get("x-inject-knowledge", "").lower() in ("true", "1")
        or os.environ.get("AUTO_INJECT_KNOWLEDGE", "").lower() in ("true", "1")
    )
    if (
        inject_rag
        and not (isinstance(model, str) and model.startswith("opencode/"))
        and pool is not None
    ):
        try:
            prompt_text = extract_prompt_text(body, style)
            if prompt_text:
                query_vec = await get_embedding(prompt_text, client=client)
                matched = await search_solutions_by_embedding(
                    pool, query_vec, limit=2,
                    task_type=request.headers.get("x-task-type"),
                    project=effective_project
                )
                if not matched:
                    matched = await search_solutions_by_text(
                        pool, prompt_text[:100], limit=2, project=effective_project
                    )
                if matched:
                    if style == "openai":
                        body = augment_openai_request(body, matched)
                    else:
                        body = augment_anthropic_request(body, matched)
                    raw = json.dumps(body).encode("utf-8")
        except Exception as e:
            logger.warning(f"RAG injection skipped: {e}")


    # OpenCode catalogue models use the local session API, never provider fallback.
    if model.startswith("opencode/"):
        if style != "openai":
            return JSONResponse(
                {"error": "OpenCode adapter supports only the OpenAI chat-completions endpoint."},
                status_code=400,
            )

        if os.environ.get("OBSERVER_OPENCODE_ENABLED", "").lower() not in ("1", "true", "yes"):
            return JSONResponse(
                {"error": "OpenCode adapter is disabled. Set OBSERVER_OPENCODE_ENABLED=1 to enable it."},
                status_code=503,
            )

        if body.get("stream"):
            return JSONResponse(
                {"error": "Streaming is not supported by the OpenCode adapter yet."},
                status_code=400,
            )

        if any(body.get(key) for key in (
            "tools", "functions", "tool_choice", "function_call"
        )):
            return JSONResponse(
                {"error": "Tool/function calling is not supported by the OpenCode adapter."},
                status_code=400,
            )

        started = time.perf_counter()
        opencode_url = os.environ.get(
            "OPENCODE_SERVER_URL", "http://127.0.0.1:4096"
        ).rstrip("/")
        try:
            result = await call_opencode(client, model, body.get("messages"))
            answer = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            meta = {
                "id": str(uuid.uuid4()),
                "project": effective_project,
                "task_id": request.headers.get("x-task-id"),
                "session_id": request.headers.get("x-session-id"),
                "task_type": request.headers.get("x-task-type"),
                "model": model,
                "upstream": opencode_url,
                "style": style,
                "streamed": False,
                "request": body,
                "response_text": answer,
                "tool_calls": [],
                "status_code": 200,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "error": None,
                "in": usage.get("prompt_tokens"),
                "out": usage.get("completion_tokens"),
            }
            try:
                await log_call(meta)
            except Exception as log_error:
                logger.warning(f"OpenCode call logging failed: {log_error}")
            return JSONResponse(result)

        except OpenCodeInputError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            logger.warning("OpenCode adapter request failed (%s)", type(exc).__name__)
            meta = {
                "id": str(uuid.uuid4()),
                "project": effective_project,
                "task_id": request.headers.get("x-task-id"),
                "session_id": request.headers.get("x-session-id"),
                "task_type": request.headers.get("x-task-type"),
                "model": model,
                "upstream": opencode_url,
                "style": style,
                "streamed": False,
                "request": body,
                "response_text": "",
                "tool_calls": [],
                "status_code": 502,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "error": f"OpenCode adapter request failed ({type(exc).__name__})",
                "in": None,
                "out": None,
            }
            try:
                await log_call(meta)
            except Exception as log_error:
                logger.warning(f"OpenCode error logging failed: {log_error}")
            return JSONResponse(
                {"error": "OpenCode adapter request failed"},
                status_code=502,
            )


    headers = {k: v for k, v in request.headers.items() if k.lower() not in SKIP_REQ_HEADERS}

    # Isolate observer credentials: never forward observer token to upstream providers
    observer_token = os.environ.get("OBSERVER_AUTH_TOKEN") or os.environ.get("OBSERVER_TOKEN")
    client_auth = request.headers.get("authorization", "").strip()
    if observer_token:
        parts = client_auth.split(None, 1)
        if (len(parts) == 2 and parts[0].lower() == "bearer" and parts[1] == observer_token) or client_auth == observer_token:
            headers.pop("authorization", None)
        if request.headers.get("x-api-key") == observer_token:
            headers.pop("x-api-key", None)

    key = os.environ.get(route.get("api_key_env") or "")
    if key:  # proxy-held key replaces the client's
        headers.pop("authorization", None)
        headers.pop("x-api-key", None)
        headers["x-api-key" if style == "anthropic" else "authorization"] = key if style == "anthropic" else f"Bearer {key}"

    meta = {
        "id": str(uuid.uuid4()),
        "project": effective_project,
        "task_id": request.headers.get("x-task-id"),
        "session_id": request.headers.get("x-session-id"),
        "task_type": request.headers.get("x-task-type"),
        "model": model,
        "upstream": route["base_url"],
        "style": style,
        "streamed": streamed,
        "request": body,
        "error": None,
    }
    t0 = time.perf_counter()

    r = None
    try:
        upstream_req = client.build_request("POST", url, content=raw, headers=headers)
        r = await client.send(upstream_req, stream=True)
    except httpx.HTTPError as e:
        # Resilient local adapter fallback: If local inference runtime is offline, failover to upstream route
        if model.startswith("local/"):
            logger.warning(f"Local inference endpoint '{url}' unreachable ({e}); falling back to upstream provider.")
            fallback_route = resolve_route("*", style)
            fallback_url = fallback_route["base_url"].rstrip("/") + UPSTREAM_PATH[style]
            fb_headers = dict(headers)
            fb_key = os.environ.get(fallback_route.get("api_key_env") or "")
            if fb_key:
                fb_headers["authorization"] = f"Bearer {fb_key}"
            try:
                fb_req = client.build_request("POST", fallback_url, content=raw, headers=fb_headers)
                r = await client.send(fb_req, stream=True)
                route_decision.strategy = "local_failover_to_upstream"
            except httpx.HTTPError as fb_err:
                meta.update(
                    response_text="",
                    tool_calls=[],
                    status_code=502,
                    latency_ms=int((time.perf_counter() - t0) * 1000),
                    error=f"Local unreachable ({e}); upstream fallback also failed ({fb_err})",
                    **{"in": None, "out": None}
                )
                await log_call(meta)
                return JSONResponse({"error": f"local and upstream error: {fb_err}"}, status_code=502)
        else:
            meta.update(
                response_text="",
                tool_calls=[],
                status_code=502,
                latency_ms=int((time.perf_counter() - t0) * 1000),
                error=str(e),
                **{"in": None, "out": None}
            )
            await log_call(meta)
            return JSONResponse({"error": f"upstream error: {e}"}, status_code=502)

    resp_headers = {k: v for k, v in r.headers.items() if k.lower() not in SKIP_RESP_HEADERS}
    if route_decision.strategy != "direct":
        resp_headers["x-observer-routed-model"] = model
        resp_headers["x-observer-route-strategy"] = route_decision.strategy

    async def finish(chunks):
        try:
            data = b"".join(chunks)
            text, tools, usage = parse_response(style, data, streamed)
            err = None if r.status_code < 400 else data.decode("utf-8", "replace")[:2000]
            meta.update(
                response_text=text,
                tool_calls=tools,
                status_code=r.status_code,
                latency_ms=int((time.perf_counter() - t0) * 1000),
                error=err,
                **{"in": usage.get("in"), "out": usage.get("out")}
            )
            await log_call(meta)
        except Exception as e:
            logger.error(f"Error in finish logging: {e}", exc_info=True)

    if streamed:
        async def gen():
            captured_chunks = []
            captured_size = 0
            try:
                async for chunk in r.aiter_raw():
                    if captured_size < MAX_CHARS:
                        take_size = min(len(chunk), MAX_CHARS - captured_size)
                        captured_chunks.append(chunk[:take_size])
                        captured_size += take_size
                    yield chunk
            finally:
                await r.aclose()
                await finish(captured_chunks)
        return StreamingResponse(gen(), status_code=r.status_code, headers=resp_headers)

    data = await r.aread()
    await r.aclose()
    await finish([data])
    return Response(content=data, status_code=r.status_code, headers=resp_headers)


# ---------- proxy endpoints ----------
@app.post("/v1/chat/completions")
async def openai_route(request: Request):
    return await proxy(request, "openai")


@app.post("/v1/messages")
async def anthropic_route(request: Request):
    return await proxy(request, "anthropic")


@app.post("/p/{project}/v1/chat/completions")
async def openai_project_route(project: str, request: Request):
    return await proxy(request, "openai", project)


@app.post("/p/{project}/v1/messages")
async def anthropic_project_route(project: str, request: Request):
    return await proxy(request, "anthropic", project)



# GEMINI_OBSERVER_ENDPOINTS
async def gemini_proxy(request: Request, operation: str, model: str = None, project: str = None):
    """Native Gemini REST adapter with Observer auth and call logging."""
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    api_key = os.environ.get("GEMINI_API_KEY") or request.headers.get("x-goog-api-key")
    if not api_key:
        return JSONResponse(
            {"error": "Gemini API key required. Set GEMINI_API_KEY or send x-goog-api-key."},
            status_code=401,
        )
    if client is None:
        return JSONResponse({"error": "upstream client not ready"}, status_code=503)

    is_generation = operation in ("generateContent", "streamGenerateContent")
    streamed = operation == "streamGenerateContent"
    body = {}

    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_REQUEST_BYTES:
                    return JSONResponse({"error": "Payload Too Large"}, status_code=413)
            except ValueError:
                pass
        raw = await request.body()
        if len(raw) > MAX_REQUEST_BYTES:
            return JSONResponse({"error": "Payload Too Large"}, status_code=413)
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            return JSONResponse({"error": "invalid JSON"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "Request body must be a JSON object"}, status_code=400)
    else:
        raw = b""

    if is_generation:
        model = model or body.get("model")
        if isinstance(model, str) and model.startswith("models/"):
            model = model[len("models/"):]
        if not isinstance(model, str) or not model or not all(
            ch.isalnum() or ch in "-._" for ch in model
        ):
            return JSONResponse({"error": "Invalid or missing Gemini model name"}, status_code=400)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:{operation}"
    elif operation == "listModels":
        url = "https://generativelanguage.googleapis.com/v1beta/models"
    elif operation == "getModel":
        if not model or not all(ch.isalnum() or ch in "-._" for ch in model):
            return JSONResponse({"error": "Invalid Gemini model name"}, status_code=400)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
    else:
        return JSONResponse({"error": "Unsupported Gemini operation"}, status_code=400)

    headers = {"x-goog-api-key": api_key}
    if is_generation:
        headers["content-type"] = "application/json"
    params = dict(request.query_params)
    if streamed:
        params["alt"] = "sse"

    # Model discovery is proxied but is not recorded as an inference call.
    if not is_generation:
        try:
            upstream_req = client.build_request(
                "GET", url, headers=headers, params=params
            )
            upstream_resp = await client.send(upstream_req)
            data = await upstream_resp.aread()
            response_headers = {
                k: v for k, v in upstream_resp.headers.items()
                if k.lower() not in SKIP_RESP_HEADERS
            }
            status = upstream_resp.status_code
            await upstream_resp.aclose()
            return Response(content=data, status_code=status, headers=response_headers)
        except httpx.HTTPError as exc:
            return JSONResponse({"error": f"Gemini upstream error: {exc}"}, status_code=502)

    effective_project = project or request.headers.get("x-project")
    meta = {
        "id": str(uuid.uuid4()),
        "project": effective_project,
        "task_id": request.headers.get("x-task-id"),
        "session_id": request.headers.get("x-session-id"),
        "task_type": request.headers.get("x-task-type"),
        "model": model,
        "upstream": "https://generativelanguage.googleapis.com/v1beta",
        "style": "gemini",
        "streamed": streamed,
        "request": body,
        "error": None,
    }
    started = time.perf_counter()

    try:
        upstream_req = client.build_request(
            "POST", url, content=raw, headers=headers, params=params
        )
        upstream_resp = await client.send(upstream_req, stream=True)
    except httpx.HTTPError as exc:
        meta.update(
            response_text="",
            tool_calls=[],
            status_code=502,
            latency_ms=int((time.perf_counter() - started) * 1000),
            error=str(exc),
            **{"in": None, "out": None},
        )
        await log_call(meta)
        return JSONResponse({"error": f"Gemini upstream error: {exc}"}, status_code=502)

    response_headers = {
        k: v for k, v in upstream_resp.headers.items()
        if k.lower() not in SKIP_RESP_HEADERS
    }

    async def finish(chunks):
        try:
            data = b"".join(chunks)
            text, tools, usage = parse_response("gemini", data, streamed)
            meta.update(
                response_text=text,
                tool_calls=tools,
                status_code=upstream_resp.status_code,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error=None if upstream_resp.status_code < 400 else data.decode("utf-8", "replace")[:2000],
                **{"in": usage.get("in"), "out": usage.get("out")},
            )
            await log_call(meta)
        except Exception as exc:
            logger.error(f"Gemini call logging failed: {exc}", exc_info=True)

    if streamed:
        async def stream_body():
            captured = []
            captured_size = 0
            try:
                async for chunk in upstream_resp.aiter_raw():
                    if captured_size < MAX_CHARS:
                        take = min(len(chunk), MAX_CHARS - captured_size)
                        captured.append(chunk[:take])
                        captured_size += take
                    yield chunk
            finally:
                await upstream_resp.aclose()
                await finish(captured)

        return StreamingResponse(
            stream_body(),
            status_code=upstream_resp.status_code,
            headers=response_headers,
        )

    data = await upstream_resp.aread()
    status = upstream_resp.status_code
    await upstream_resp.aclose()
    await finish([data])
    return Response(content=data, status_code=status, headers=response_headers)


@app.get("/v1beta/models")
async def gemini_models_route(request: Request):
    return await gemini_proxy(request, "listModels")


@app.get("/v1beta/models/{model}")
async def gemini_model_route(model: str, request: Request):
    return await gemini_proxy(request, "getModel", model=model)


@app.post("/v1beta/models/{model}:generateContent")
async def gemini_generate_route(model: str, request: Request):
    return await gemini_proxy(request, "generateContent", model=model)


@app.post("/v1beta/models/{model}:streamGenerateContent")
async def gemini_stream_route(model: str, request: Request):
    return await gemini_proxy(request, "streamGenerateContent", model=model)


@app.get("/p/{project}/v1beta/models")
async def gemini_project_models_route(project: str, request: Request):
    return await gemini_proxy(request, "listModels", project=project)


@app.get("/p/{project}/v1beta/models/{model}")
async def gemini_project_model_route(project: str, model: str, request: Request):
    return await gemini_proxy(request, "getModel", model=model, project=project)


@app.post("/p/{project}/v1beta/models/{model}:generateContent")
async def gemini_project_generate_route(project: str, model: str, request: Request):
    return await gemini_proxy(request, "generateContent", model=model, project=project)


@app.post("/p/{project}/v1beta/models/{model}:streamGenerateContent")
async def gemini_project_stream_route(project: str, model: str, request: Request):
    return await gemini_proxy(request, "streamGenerateContent", model=model, project=project)



async def auto_index_task_solution(pool: asyncpg.Pool, task_id: str, status: str):
    """If outcome is pass/accepted, extract task prompt & code and index as verified solution."""
    try:
        async with pool.acquire() as c:
            existing = await c.fetchval("SELECT id FROM solutions WHERE task_id = $1 LIMIT 1", task_id)
            if existing:
                return

            call = await c.fetchrow("""
                SELECT task_type, project, request, response_text
                FROM llm_calls
                WHERE task_id = $1 AND response_text IS NOT NULL AND (status_code IS NULL OR status_code < 400)
                ORDER BY ts DESC
                LIMIT 1
            """, task_id)

            if not call or not call["response_text"]:
                return

            req_body = call["request"] or {}
            prompt = extract_prompt_text(req_body, "openai") or f"Task {task_id}"
            solution_code = call["response_text"]

            embedding = await get_embedding(prompt, client=client)

            await index_solution(
                pool=pool,
                task_id=task_id,
                problem_summary=prompt[:500],
                solution_code=solution_code,
                outcome_status=status,
                task_type=call["task_type"],
                project=call["project"],
                embedding=embedding,
            )
            logger.info(f"Auto-indexed verified solution for task {task_id}")
    except Exception as e:
        logger.warning(f"Auto-index solution failed for {task_id}: {e}")


# ---------- telemetry & stats ----------
@app.post("/outcomes")
async def add_outcome(payload: OutcomeRequest, request: Request):
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if pool is None:
        return JSONResponse({"error": "database uninitialized"}, status_code=503)
    await record_outcome(pool, payload.task_id, payload.kind, payload.status, payload.details)

    if payload.status in ("pass", "accepted"):
        await auto_index_task_solution(pool, payload.task_id, payload.status)

    return {"ok": True}


@app.get("/stats")
async def stats(request: Request, session_id: Optional[str] = None, project: Optional[str] = None):
    """Per-model summary with last-touch attribution and task-level success metric."""
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if pool is None:
        return JSONResponse({"error": "database uninitialized"}, status_code=503)
    async with pool.acquire() as c:
        rows = await c.fetch("""
            WITH filtered_calls AS (
                SELECT * FROM llm_calls
                WHERE ($1::text IS NULL OR session_id = $1)
                  AND ($2::text IS NULL OR project = $2)
            ),
            task_primary_model AS (
                -- Attribute each task outcome to the most recent model used in that task
                SELECT DISTINCT ON (task_id) task_id, model
                FROM filtered_calls
                WHERE task_id IS NOT NULL
                ORDER BY task_id, ts DESC
            ),
            task_outcome_summary AS (
                SELECT
                    task_id,
                    bool_or(status IN ('fail', 'rejected')) AS has_fail,
                    bool_or(status IN ('pass', 'accepted')) AS has_pass
                FROM outcomes
                WHERE task_id IN (SELECT DISTINCT task_id FROM filtered_calls WHERE task_id IS NOT NULL)
                GROUP BY task_id
            )
            SELECT m.model, m.calls, m.avg_latency_ms, m.input_tokens, m.output_tokens,
                   COALESCE(o.passes, 0) AS passes, COALESCE(o.fails, 0) AS fails
            FROM (
                SELECT model, count(*) calls, round(avg(latency_ms)) avg_latency_ms,
                       sum(input_tokens) input_tokens, sum(output_tokens) output_tokens
                FROM filtered_calls
                GROUP BY model
            ) m
            LEFT JOIN (
                SELECT tpm.model,
                       count(DISTINCT tpm.task_id) FILTER (WHERE tos.has_pass AND NOT tos.has_fail) AS passes,
                       count(DISTINCT tpm.task_id) FILTER (WHERE tos.has_fail) AS fails
                FROM task_primary_model tpm
                JOIN task_outcome_summary tos ON tos.task_id = tpm.task_id
                GROUP BY tpm.model
            ) o ON o.model = m.model
            ORDER BY m.calls DESC""", session_id, project)
    return [dict(r) for r in rows]


@app.get("/health")
async def health_view():
    if not await check_health(pool):
        return JSONResponse({"ok": False, "status": "unready", "error": "database unreachable"}, status_code=503)
    return {"ok": True, "status": "ready"}


@app.get("/download/observer.whl")
async def download_cli_wheel():
    """Serve the compiled observer CLI package wheel for client installation."""
    whl_path = os.path.join(os.path.dirname(__file__), "dist", "ai_observer-1.0.0-py3-none-any.whl")
    if os.path.exists(whl_path):
        return FileResponse(whl_path, filename="ai_observer-1.0.0-py3-none-any.whl", media_type="application/zip")
    return JSONResponse({"error": "wheel package not found"}, status_code=404)


# ---------- models listing compatibility ----------
@app.get("/v1/models")
@app.get("/p/{project}/v1/models")
async def list_models(request: Request):
    """OpenAI-compatible models catalog endpoint."""
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    model_list = []
    for prefix, cfg in routes.items():
        if prefix == "*":
            continue
        clean_id = prefix.rstrip("/")
        model_list.append({
            "id": clean_id,
            "object": "model",
            "created": 1700000000,
            "owned_by": "ai-model-observer"
        })
    if not model_list:
        model_list.append({"id": "default", "object": "model", "owned_by": "ai-model-observer"})
    return {"object": "list", "data": model_list}


# ---------- intelligent routing recommendations ----------
@app.get("/router/recommendations")
async def router_recommendations_endpoint(request: Request):
    """Provide model selection recommendations based on historical performance telemetry."""
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if pool is None:
        return JSONResponse({"error": "database uninitialized"}, status_code=503)

    from app.storage import fetch_stats
    stats = await fetch_stats(pool)
    best_pass = select_optimal_model(stats, strategy="best_pass_rate")
    fastest = select_optimal_model(stats, strategy="lowest_latency")
    balanced = select_optimal_model(stats, strategy="balanced")

    return {
        "ok": True,
        "recommendations": {
            "best_pass_rate": {
                "model": best_pass.selected_model,
                "reason": best_pass.reason,
                "metrics": best_pass.metrics,
            },
            "lowest_latency": {
                "model": fastest.selected_model,
                "reason": fastest.reason,
                "metrics": fastest.metrics,
            },
            "balanced": {
                "model": balanced.selected_model,
                "reason": balanced.reason,
                "metrics": balanced.metrics,
            },
        },
        "telemetry_models_count": len(stats),
    }


# ---------- task audit endpoints ----------
@app.get("/tasks")
async def list_tasks(request: Request, limit: int = 50):
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if pool is None:
        return JSONResponse({"error": "database uninitialized"}, status_code=503)
    return await fetch_tasks(pool, limit)


@app.get("/tasks/{task_id}")
async def get_task_trace(task_id: str, request: Request):
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if pool is None:
        return JSONResponse({"error": "database uninitialized"}, status_code=503)
    data = await fetch_task_details(pool, task_id)
    if data is None:
        return JSONResponse({"error": "task not found"}, status_code=404)
    return data


# ---------- admin & retention ----------
@app.post("/admin/prune")
async def prune_endpoint(request: Request, days: int = 90):
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if pool is None:
        return JSONResponse({"error": "database uninitialized"}, status_code=503)
    if days < 1 or days > 3650:
        return JSONResponse({"error": "days parameter must be between 1 and 3650"}, status_code=400)
    res = await prune_records(pool, days)
    return {"ok": True, **res}


# ---------- Phase 5: Training Dataset Curation & Export ----------
@app.post("/admin/export-dataset")
async def export_dataset_endpoint(payload: DatasetExportRequest, request: Request):
    """Export curated SFT or DPO datasets from verified task telemetry."""
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if pool is None:
        return JSONResponse({"error": "database uninitialized"}, status_code=503)

    if payload.dataset_type.lower() == "dpo":
        records = await export_dpo_dataset(
            pool=pool,
            project=payload.project,
            task_type=payload.task_type,
            limit=payload.limit,
        )
    else:
        records = await export_sft_dataset(
            pool=pool,
            project=payload.project,
            task_type=payload.task_type,
            limit=payload.limit,
            deduplicate=payload.deduplicate,
        )

    splits = split_dataset(records, val_ratio=payload.val_split)
    summary = compute_dataset_summary(records, dataset_type=payload.dataset_type.lower())

    return {
        "ok": True,
        "dataset_type": payload.dataset_type.lower(),
        "summary": summary,
        "splits": {
            "train_count": len(splits["train"]),
            "validation_count": len(splits["validation"]),
        },
        "train": splits["train"],
        "validation": splits["validation"],
    }


@app.get("/admin/dataset/stats")
async def dataset_stats_endpoint(request: Request, project: Optional[str] = None):
    """Inspect dataset curation potential and verified sample counts."""
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if pool is None:
        return JSONResponse({"error": "database uninitialized"}, status_code=503)

    sft_records = await export_sft_dataset(pool=pool, project=project, limit=5000)
    dpo_records = await export_dpo_dataset(pool=pool, project=project, limit=5000)

    return {
        "ok": True,
        "sft": compute_dataset_summary(sft_records, dataset_type="sft"),
        "dpo": compute_dataset_summary(dpo_records, dataset_type="dpo"),
    }


# ---------- Phase 3: pgvector Knowledge Retrieval ----------
@app.post("/knowledge/solutions")
async def add_solution(payload: SolutionIndexRequest, request: Request):
    """Index a verified solution into pgvector knowledge base."""
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if pool is None:
        return JSONResponse({"error": "database uninitialized"}, status_code=503)
    try:
        if payload.embedding:
            validate_embedding_vector(payload.embedding)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    sol_id = await index_solution(
        pool=pool,
        task_id=payload.task_id,
        problem_summary=payload.problem_summary,
        solution_code=payload.solution_code,
        outcome_status=payload.outcome_status,
        task_type=payload.task_type,
        project=payload.project or request.headers.get("x-project"),
        embedding=payload.embedding,
    )
    return {"ok": True, "solution_id": sol_id}


@app.post("/knowledge/search")
async def search_knowledge(payload: SolutionSearchRequest, request: Request):
    """Query past solutions using vector similarity or keyword search with project scoping."""
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if pool is None:
        return JSONResponse({"error": "database uninitialized"}, status_code=503)

    target_project = payload.project or request.headers.get("x-project")

    try:
        if payload.query_embedding:
            validate_embedding_vector(payload.query_embedding)
            results = await search_solutions_by_embedding(
                pool=pool,
                query_vector=payload.query_embedding,
                limit=payload.limit,
                task_type=payload.task_type,
                project=target_project,
            )
        elif payload.query_text:
            results = await search_solutions_by_text(
                pool=pool,
                query_text=payload.query_text,
                limit=payload.limit,
                project=target_project,
            )
        else:
            return JSONResponse({"error": "Must provide query_text or query_embedding"}, status_code=400)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    return {"results": results}


# ---------- analytics dashboard view ----------
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/", response_class=HTMLResponse)
async def root_view(request: Request):
    if not check_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return HTMLResponse(content=DASHBOARD_HTML)
