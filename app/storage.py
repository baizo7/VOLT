"""
Database access and persistence layer for PostgreSQL.
"""
import json
import logging
from typing import Any, Dict, List, Optional
import asyncpg
from app.config import MAX_CHARS, logger
from app.security import scrub_record


async def save_llm_call(pool: Optional[asyncpg.Pool], rec: dict, max_chars: int = MAX_CHARS):
    """Persist an intercepted LLM call record with scrubbed fields to PostgreSQL."""
    try:
        rec = scrub_record(rec)
        if pool is None:
            return
        async with pool.acquire() as c:
            if rec.get("task_id"):
                await c.execute(
                    """INSERT INTO tasks (task_id, project, task_type) VALUES ($1,$2,$3)
                       ON CONFLICT (task_id) DO UPDATE SET
                           project = COALESCE(tasks.project, EXCLUDED.project),
                           task_type = COALESCE(tasks.task_type, EXCLUDED.task_type)""",
                    rec["task_id"], rec.get("project"), rec.get("task_type")
                )
            await c.execute(
                """INSERT INTO llm_calls (id, project, task_id, session_id, task_type, model, upstream,
                       api_style, streamed, request, response_text, tool_calls, status_code,
                       latency_ms, input_tokens, output_tokens, error)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11,$12::jsonb,$13,$14,$15,$16,$17)""",
                rec["id"], rec.get("project"), rec.get("task_id"), rec.get("session_id"), rec.get("task_type"),
                rec["model"], rec["upstream"], rec["style"], rec["streamed"],
                json.dumps(rec.get("request")),
                (rec["response_text"] or "")[:max_chars] if rec.get("response_text") else None,
                json.dumps(rec.get("tool_calls") or []), rec.get("status_code"), rec.get("latency_ms"),
                rec.get("in"), rec.get("out"), rec.get("error")
            )
    except Exception as e:
        logger.error(f"observer log error: {e}", exc_info=True)


async def record_outcome(pool: asyncpg.Pool, task_id: str, kind: str, status: str, details: Optional[dict] = None):
    """Insert task outcome signal into PostgreSQL."""
    async with pool.acquire() as c:
        await c.execute("INSERT INTO tasks (task_id) VALUES ($1) ON CONFLICT DO NOTHING", task_id)
        await c.execute(
            "INSERT INTO outcomes (task_id, kind, status, details) VALUES ($1,$2,$3,$4::jsonb)",
            task_id, kind, status, json.dumps(details or {})
        )


async def fetch_stats(pool: asyncpg.Pool) -> List[Dict[str, Any]]:
    """Query model performance statistics with last-touch attribution and task-level success counts."""
    async with pool.acquire() as c:
        rows = await c.fetch("""
            WITH task_primary_model AS (
                -- Attribute each task outcome to the most recent model used in that task
                SELECT DISTINCT ON (task_id) task_id, model
                FROM llm_calls
                WHERE task_id IS NOT NULL
                ORDER BY task_id, ts DESC
            ),
            task_outcome_summary AS (
                SELECT
                    task_id,
                    bool_or(status IN ('fail', 'rejected')) AS has_fail,
                    bool_or(status IN ('pass', 'accepted')) AS has_pass
                FROM outcomes
                GROUP BY task_id
            )
            SELECT m.model, m.calls, m.avg_latency_ms, m.input_tokens, m.output_tokens,
                   COALESCE(o.passes, 0) AS passes, COALESCE(o.fails, 0) AS fails
            FROM (
                SELECT model, count(*) calls, round(avg(latency_ms)) avg_latency_ms,
                       sum(input_tokens) input_tokens, sum(output_tokens) output_tokens
                FROM llm_calls
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
            ORDER BY m.calls DESC""")
    return [dict(r) for r in rows]


async def fetch_tasks(pool: asyncpg.Pool, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent tasks summary."""
    async with pool.acquire() as c:
        rows = await c.fetch("""
            SELECT 
                t.task_id,
                t.project,
                t.task_type,
                t.title,
                t.created_at,
                count(c.id) AS call_count,
                (SELECT model FROM llm_calls WHERE task_id = t.task_id ORDER BY ts DESC LIMIT 1) AS primary_model,
                (SELECT status FROM outcomes WHERE task_id = t.task_id ORDER BY created_at DESC LIMIT 1) AS latest_outcome,
                (SELECT kind FROM outcomes WHERE task_id = t.task_id ORDER BY created_at DESC LIMIT 1) AS outcome_kind
            FROM tasks t
            LEFT JOIN llm_calls c ON c.task_id = t.task_id
            GROUP BY t.task_id, t.project, t.task_type, t.title, t.created_at
            ORDER BY t.created_at DESC
            LIMIT $1
        """, limit)
    result = []
    for r in rows:
        d = dict(r)
        if d.get("created_at"):
            d["created_at"] = d["created_at"].isoformat()
        result.append(d)
    return result


async def fetch_task_details(pool: asyncpg.Pool, task_id: str) -> Optional[Dict[str, Any]]:
    """Fetch complete task record, calls, and reported outcomes."""
    async with pool.acquire() as c:
        task_row = await c.fetchrow("SELECT * FROM tasks WHERE task_id = $1", task_id)
        if not task_row:
            return None
        call_rows = await c.fetch("""
            SELECT id, ts, model, upstream, api_style, streamed, status_code, latency_ms, input_tokens, output_tokens, error
            FROM llm_calls WHERE task_id = $1 ORDER BY ts ASC
        """, task_id)
        outcome_rows = await c.fetch("""
            SELECT id, kind, status, details, created_at
            FROM outcomes WHERE task_id = $1 ORDER BY created_at ASC
        """, task_id)

    t_dict = dict(task_row)
    if t_dict.get("created_at"):
        t_dict["created_at"] = t_dict["created_at"].isoformat()

    calls = []
    for r in call_rows:
        cd = dict(r)
        if cd.get("id"):
            cd["id"] = str(cd["id"])
        if cd.get("ts"):
            cd["ts"] = cd["ts"].isoformat()
        calls.append(cd)

    outcomes = []
    for r in outcome_rows:
        od = dict(r)
        if od.get("created_at"):
            od["created_at"] = od["created_at"].isoformat()
        if isinstance(od.get("details"), str):
            try:
                od["details"] = json.loads(od["details"])
            except Exception:
                pass
        outcomes.append(od)

    return {"task": t_dict, "calls": calls, "outcomes": outcomes}


async def prune_records(pool: asyncpg.Pool, days: int) -> Dict[str, str]:
    """Execute retention policy deletion queries across all historical tables."""
    async with pool.acquire() as c:
        s_del = await c.execute(f"DELETE FROM solutions WHERE created_at < NOW() - INTERVAL '{days} days'")
        o_del = await c.execute(f"DELETE FROM outcomes WHERE created_at < NOW() - INTERVAL '{days} days'")
        l_del = await c.execute(f"DELETE FROM llm_calls WHERE ts < NOW() - INTERVAL '{days} days'")
        t_del = await c.execute(f"""
            DELETE FROM tasks
            WHERE created_at < NOW() - INTERVAL '{days} days'
              AND task_id NOT IN (SELECT DISTINCT task_id FROM llm_calls WHERE task_id IS NOT NULL)
        """)
    return {"solutions_pruned": s_del, "outcomes_pruned": o_del, "calls_pruned": l_del, "tasks_pruned": t_del}


async def check_health(pool: Optional[asyncpg.Pool]) -> bool:
    """Validate database connectivity."""
    if pool is None:
        return False
    try:
        async with pool.acquire() as c:
            await c.fetchval("SELECT 1")
        return True
    except Exception as e:
        logger.warning(f"Health check query error: {e}")
        return False
