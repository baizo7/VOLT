import math
from typing import Any, Dict, List, Optional
import asyncpg
from app.config import logger
from app.security import scrub_text

EXPECTED_EMBEDDING_DIM = 1536


def validate_embedding_vector(vec: Optional[List[float]], expected_dim: Optional[int] = EXPECTED_EMBEDDING_DIM):
    """Ensure vector is valid float list with exact dimension if expected_dim is specified."""
    if vec is None:
        return
    if not isinstance(vec, list):
        raise ValueError("Embedding must be a list of floats.")
    if expected_dim is not None and len(vec) != expected_dim:
        raise ValueError(f"Embedding dimension {len(vec)} does not match expected dimension {expected_dim}.")
    for x in vec:
        if not isinstance(x, (int, float)) or math.isnan(x) or math.isinf(x):
            raise ValueError("Embedding contains non-finite or invalid float values.")


def vector_to_string(vec: List[float]) -> str:
    """Format float list into PostgreSQL vector literal '[v1, v2, ...]'."""
    validate_embedding_vector(vec, expected_dim=None)
    return "[" + ",".join(str(float(x)) for x in vec) + "]"


async def index_solution(
    pool: asyncpg.Pool,
    task_id: str,
    problem_summary: str,
    solution_code: str,
    outcome_status: str = "pass",
    task_type: Optional[str] = None,
    project: Optional[str] = None,
    embedding: Optional[List[float]] = None
) -> int:
    """Index a verified solution idempotently in PostgreSQL with scrubbing."""
    validate_embedding_vector(embedding)
    clean_problem = scrub_text(problem_summary)
    clean_code = scrub_text(solution_code)

    async with pool.acquire() as c:
        # Check if already indexed for this task
        existing_id = await c.fetchval("SELECT id FROM solutions WHERE task_id = $1 LIMIT 1", task_id)
        if existing_id:
            if embedding:
                emb_str = vector_to_string(embedding)
                await c.execute("""
                    UPDATE solutions
                    SET problem_summary = $1, solution_code = $2, outcome_status = $3,
                        task_type = $4, project = $5, embedding = $6::vector, created_at = now()
                    WHERE id = $7
                """, clean_problem, clean_code, outcome_status, task_type, project, emb_str, existing_id)
            else:
                await c.execute("""
                    UPDATE solutions
                    SET problem_summary = $1, solution_code = $2, outcome_status = $3,
                        task_type = $4, project = $5, created_at = now()
                    WHERE id = $6
                """, clean_problem, clean_code, outcome_status, task_type, project, existing_id)
            return existing_id

        if embedding:
            emb_str = vector_to_string(embedding)
            row = await c.fetchrow("""
                INSERT INTO solutions (task_id, task_type, project, problem_summary, solution_code, outcome_status, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7::vector)
                RETURNING id
            """, task_id, task_type, project, clean_problem, clean_code, outcome_status, emb_str)
        else:
            row = await c.fetchrow("""
                INSERT INTO solutions (task_id, task_type, project, problem_summary, solution_code, outcome_status)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, task_id, task_type, project, clean_problem, clean_code, outcome_status)
        return row["id"]


async def search_solutions_by_embedding(
    pool: asyncpg.Pool,
    query_vector: List[float],
    limit: int = 5,
    task_type: Optional[str] = None,
    project: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieve top-K most similar solutions using pgvector cosine distance (<=>) with optional project scoping."""
    validate_embedding_vector(query_vector)
    emb_str = vector_to_string(query_vector)
    async with pool.acquire() as c:
        query = """
            SELECT id, task_id, task_type, project, problem_summary, solution_code, outcome_status,
                   (1 - (embedding <=> $1::vector)) AS similarity
            FROM solutions
            WHERE embedding IS NOT NULL
        """
        params = [emb_str]
        idx = 2

        if project:
            query += f" AND (project = ${idx} OR project IS NULL)"
            params.append(project)
            idx += 1

        if task_type:
            query += f" AND task_type = ${idx}"
            params.append(task_type)
            idx += 1

        query += f" ORDER BY embedding <=> $1::vector ASC LIMIT ${idx}"
        params.append(limit)

        rows = await c.fetch(query, *params)
    return [dict(r) for r in rows]


async def search_solutions_by_text(
    pool: asyncpg.Pool,
    query_text: str,
    limit: int = 5,
    project: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Text-based keyword search fallback over past solutions with project scoping."""
    pattern = f"%{query_text.strip()}%"
    async with pool.acquire() as c:
        if project:
            rows = await c.fetch("""
                SELECT id, task_id, task_type, project, problem_summary, solution_code, outcome_status, 1.0 AS similarity
                FROM solutions
                WHERE (project = $1 OR project IS NULL)
                  AND (problem_summary ILIKE $2 OR solution_code ILIKE $2)
                ORDER BY created_at DESC
                LIMIT $3
            """, project, pattern, limit)
        else:
            rows = await c.fetch("""
                SELECT id, task_id, task_type, project, problem_summary, solution_code, outcome_status, 1.0 AS similarity
                FROM solutions
                WHERE problem_summary ILIKE $1 OR solution_code ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2
            """, pattern, limit)
    return [dict(r) for r in rows]
