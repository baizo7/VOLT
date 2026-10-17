"""
Database access and persistence layer for PostgreSQL.
"""
import datetime
import json
import logging
import secrets
from typing import Any, Dict, List, Optional
import uuid
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


async def fetch_tasks(pool: asyncpg.Pool, limit: int = 50, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch recent tasks summary, optionally filtered to a specific developer session."""
    async with pool.acquire() as c:
        if session_id:
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
                JOIN llm_calls c ON c.task_id = t.task_id AND c.session_id = $2
                GROUP BY t.task_id, t.project, t.task_type, t.title, t.created_at
                ORDER BY t.created_at DESC
                LIMIT $1
            """, limit, session_id)
        else:
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
            SELECT id, ts, session_id, model, upstream, api_style, streamed, status_code, latency_ms, input_tokens, output_tokens, error
            FROM llm_calls WHERE task_id = $1 ORDER BY ts ASC
        """, task_id)
        outcome_rows = await c.fetch("""
            SELECT id, kind, status, details, created_at
            FROM outcomes WHERE task_id = $1 ORDER BY created_at ASC
        """, task_id)

    t_dict = dict(task_row)
    if t_dict.get("created_at"):
        t_dict["created_at"] = t_dict["created_at"].isoformat()

    sessions = []
    calls = []
    for r in call_rows:
        cd = dict(r)
        if cd.get("id"):
            cd["id"] = str(cd["id"])
        if cd.get("ts"):
            cd["ts"] = cd["ts"].isoformat()
        if cd.get("session_id") and cd["session_id"] not in sessions:
            sessions.append(cd["session_id"])
        calls.append(cd)

    if sessions:
        t_dict["session_id"] = sessions[0]

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

    return {"task": t_dict, "calls": calls, "outcomes": outcomes, "sessions": sessions}


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


async def record_developer_key(
    pool: Optional[asyncpg.Pool],
    key_hash: str,
    session_id: Optional[str],
    project: Optional[str],
    key_masked: str,
    provider: str,
    model: str,
):
    """Upsert developer connection record tracking their masked key and configured models."""
    if pool is None or not key_hash or key_hash == "anonymous":
        return
    try:
        async with pool.acquire() as c:
            await c.execute("""
                INSERT INTO developer_keys (key_hash, session_id, project, key_masked, provider, models_used, first_seen, last_seen, total_calls)
                VALUES ($1, $2, $3, $4, $5, ARRAY[$6::text], now(), now(), 1)
                ON CONFLICT (key_hash) DO UPDATE SET
                    session_id = COALESCE(EXCLUDED.session_id, developer_keys.session_id),
                    project = COALESCE(EXCLUDED.project, developer_keys.project),
                    provider = COALESCE(EXCLUDED.provider, developer_keys.provider),
                    last_seen = now(),
                    total_calls = developer_keys.total_calls + 1,
                    models_used = (
                        SELECT array_agg(DISTINCT m)
                        FROM unnest(array_append(developer_keys.models_used, EXCLUDED.models_used[1])) AS m
                        WHERE m IS NOT NULL
                    )
            """, key_hash, session_id or "anonymous", project or "default", key_masked, provider, model)
    except Exception as e:
        logger.warning(f"Failed to record developer key: {e}")


async def fetch_connected_developers(pool: asyncpg.Pool) -> List[Dict[str, Any]]:
    """Fetch list of all developers who connected their API keys, with usage and activity metrics."""
    async with pool.acquire() as c:
        rows = await c.fetch("""
            SELECT 
                dk.key_hash,
                COALESCE(dk.session_id, 'anonymous') AS session_id,
                COALESCE(dk.project, 'default') AS project,
                dk.key_masked,
                COALESCE(dk.provider, 'unknown') AS provider,
                COALESCE(dk.models_used, ARRAY[]::text[]) AS models_used,
                dk.first_seen,
                dk.last_seen,
                dk.total_calls,
                COALESCE(u.input_tokens, 0) AS total_input_tokens,
                COALESCE(u.output_tokens, 0) AS total_output_tokens
            FROM developer_keys dk
            LEFT JOIN (
                SELECT session_id, sum(input_tokens) AS input_tokens, sum(output_tokens) AS output_tokens
                FROM llm_calls
                GROUP BY session_id
            ) u ON u.session_id = dk.session_id
            ORDER BY dk.last_seen DESC
        """)
        results = []
        for r in rows:
            d = dict(r)
            if d.get("first_seen"):
                d["first_seen"] = d["first_seen"].isoformat()
            if d.get("last_seen"):
                d["last_seen"] = d["last_seen"].isoformat()
            results.append(d)
        return results


async def fetch_developer_profile(pool: asyncpg.Pool, session_id: str) -> Dict[str, Any]:
    """Fetch personal configuration and activity for a single developer."""
    async with pool.acquire() as c:
        row = await c.fetchrow("""
            SELECT 
                session_id, project, key_masked, provider, models_used, first_seen, last_seen, total_calls
            FROM developer_keys
            WHERE session_id = $1
            ORDER BY last_seen DESC
            LIMIT 1
        """, session_id)
        if row:
            d = dict(row)
            if d.get("first_seen"):
                d["first_seen"] = d["first_seen"].isoformat()
            if d.get("last_seen"):
                d["last_seen"] = d["last_seen"].isoformat()
            return d

        fallback = await c.fetchrow("""
            SELECT 
                session_id, project, 'configured' AS key_masked, 'custom' AS provider,
                array_agg(DISTINCT model) AS models_used,
                min(ts) AS first_seen, max(ts) AS last_seen, count(*) AS total_calls
            FROM llm_calls
            WHERE session_id = $1
            GROUP BY session_id, project
            LIMIT 1
        """, session_id)
        if fallback:
            d = dict(fallback)
            if d.get("first_seen"):
                d["first_seen"] = d["first_seen"].isoformat()
            if d.get("last_seen"):
                d["last_seen"] = d["last_seen"].isoformat()
            return d

        return {
            "session_id": session_id,
            "project": "default",
            "key_masked": "not-active",
            "provider": "unknown",
            "models_used": [],
            "first_seen": None,
            "last_seen": None,
            "total_calls": 0,
        }


async def fetch_timeseries_stats(
    pool: asyncpg.Pool,
    days: int = 7,
    session_id: Optional[str] = None,
    project: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetch daily aggregated call metrics for time-series charting."""
    async with pool.acquire() as c:
        rows = await c.fetch("""
            SELECT
                date_trunc('day', ts)::date AS day,
                model,
                count(*) AS calls,
                round(avg(latency_ms)) AS avg_latency_ms,
                COALESCE(sum(input_tokens), 0) AS input_tokens,
                COALESCE(sum(output_tokens), 0) AS output_tokens
            FROM llm_calls
            WHERE ts >= now() - make_interval(days => $1)
              AND ($2::text IS NULL OR session_id = $2)
              AND ($3::text IS NULL OR project = $3)
            GROUP BY day, model
            ORDER BY day ASC, calls DESC
        """, days, session_id, project)
    result = []
    for r in rows:
        d = dict(r)
        if hasattr(d.get("day"), "isoformat"):
            d["day"] = d["day"].isoformat()
        elif d.get("day") is not None:
            d["day"] = str(d["day"])
        result.append(d)
    return result


_IN_MEMORY_USERS: Dict[str, dict] = {}
_IN_MEMORY_SESSIONS: Dict[str, dict] = {}


async def upsert_google_user(
    pool: Optional[asyncpg.Pool],
    email: str,
    name: Optional[str] = None,
    google_id: Optional[str] = None,
    picture: Optional[str] = None,
    role: str = "developer",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Insert or update a registered Google user in PostgreSQL users table.
    Supports in-memory fallback when database pool is None.
    """
    email_clean = email.strip().lower()
    meta_json = json.dumps(metadata or {})
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if pool is None:
        user = _IN_MEMORY_USERS.get(email_clean)
        if not user:
            user_id = str(uuid.uuid4())
            user = {
                "id": user_id,
                "google_id": google_id,
                "email": email_clean,
                "name": name or email_clean.split("@")[0],
                "picture": picture,
                "role": role,
                "provider": "google",
                "created_at": now_iso,
                "last_login_at": now_iso,
                "metadata": metadata or {},
            }
            _IN_MEMORY_USERS[email_clean] = user
        else:
            if name:
                user["name"] = name
            if picture:
                user["picture"] = picture
            if google_id:
                user["google_id"] = google_id
            user["last_login_at"] = now_iso
            user["metadata"].update(metadata or {})
        return dict(user)

    async with pool.acquire() as c:
        row = await c.fetchrow(
            """
            INSERT INTO users (google_id, email, name, picture, role, provider, created_at, last_login_at, metadata)
            VALUES ($1, $2, $3, $4, $5, 'google', NOW(), NOW(), $6::jsonb)
            ON CONFLICT (email) DO UPDATE SET
                google_id = COALESCE(EXCLUDED.google_id, users.google_id),
                name = COALESCE(EXCLUDED.name, users.name),
                picture = COALESCE(EXCLUDED.picture, users.picture),
                last_login_at = NOW(),
                metadata = users.metadata || EXCLUDED.metadata
            RETURNING id, google_id, email, name, picture, role, provider, created_at, last_login_at, metadata;
            """,
            google_id,
            email_clean,
            name,
            picture,
            role,
            meta_json,
        )
        d = dict(row)
        if d.get("id"):
            d["id"] = str(d["id"])
        if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
            d["created_at"] = d["created_at"].isoformat()
        if d.get("last_login_at") and hasattr(d["last_login_at"], "isoformat"):
            d["last_login_at"] = d["last_login_at"].isoformat()
        if isinstance(d.get("metadata"), str):
            try:
                d["metadata"] = json.loads(d["metadata"])
            except Exception:
                pass
        return d


async def create_user_session(
    pool: Optional[asyncpg.Pool],
    user_id: str,
    email: str,
    name: Optional[str] = None,
    role: str = "developer",
    duration_days: int = 30,
) -> Dict[str, Any]:
    """Generate and store an authenticated session token for a user."""
    token = f"volt_sess_{secrets.token_hex(24)}"
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = now + datetime.timedelta(days=duration_days)

    if pool is None:
        sess_data = {
            "token": token,
            "user_id": user_id,
            "email": email,
            "name": name or email.split("@")[0],
            "role": role,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        }
        _IN_MEMORY_SESSIONS[token] = sess_data
        return sess_data

    async with pool.acquire() as c:
        await c.execute(
            """
            INSERT INTO user_sessions (token, user_id, email, name, role, created_at, expires_at)
            VALUES ($1, $2::uuid, $3, $4, $5, NOW(), $6)
            """,
            token,
            user_id,
            email,
            name,
            role,
            expires_at,
        )
    return {
        "token": token,
        "user_id": user_id,
        "email": email,
        "name": name,
        "role": role,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }


async def get_user_by_session_token(
    pool: Optional[asyncpg.Pool],
    token: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve active user profile matching session token."""
    if not token:
        return None

    if pool is None:
        sess = _IN_MEMORY_SESSIONS.get(token)
        if not sess:
            return None
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if sess.get("expires_at") and sess["expires_at"] < now_iso:
            _IN_MEMORY_SESSIONS.pop(token, None)
            return None
        return dict(sess)

    async with pool.acquire() as c:
        row = await c.fetchrow(
            """
            SELECT 
                u.id, u.google_id, u.email, u.name, u.picture, u.role, u.provider,
                u.created_at, u.last_login_at, s.token, s.expires_at
            FROM user_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = $1 AND s.expires_at > NOW()
            """,
            token,
        )
        if not row:
            return None
        d = dict(row)
        d["id"] = str(d["id"])
        if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
            d["created_at"] = d["created_at"].isoformat()
        if d.get("last_login_at") and hasattr(d["last_login_at"], "isoformat"):
            d["last_login_at"] = d["last_login_at"].isoformat()
        if d.get("expires_at") and hasattr(d["expires_at"], "isoformat"):
            d["expires_at"] = d["expires_at"].isoformat()
        return d


async def delete_user_session(pool: Optional[asyncpg.Pool], token: str):
    """Log out a user by terminating their session."""
    if not token:
        return
    if pool is None:
        _IN_MEMORY_SESSIONS.pop(token, None)
        return
    try:
        async with pool.acquire() as c:
            await c.execute("DELETE FROM user_sessions WHERE token = $1", token)
    except Exception as e:
        logger.warning(f"Error removing user session: {e}")


async def fetch_all_users(pool: Optional[asyncpg.Pool], limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch all registered account users for the admin dashboard."""
    if pool is None:
        return list(_IN_MEMORY_USERS.values())[:limit]

    async with pool.acquire() as c:
        rows = await c.fetch(
            """
            SELECT 
                u.id, u.google_id, u.email, u.name, u.picture, u.role, u.provider,
                u.created_at, u.last_login_at,
                (SELECT count(*) FROM llm_calls WHERE session_id = u.email) AS call_count
            FROM users u
            ORDER BY u.last_login_at DESC
            LIMIT $1
            """,
            limit,
        )
        results = []
        for r in rows:
            d = dict(r)
            d["id"] = str(d["id"])
            if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
                d["created_at"] = d["created_at"].isoformat()
            if d.get("last_login_at") and hasattr(d["last_login_at"], "isoformat"):
                d["last_login_at"] = d["last_login_at"].isoformat()
            results.append(d)
        return results

