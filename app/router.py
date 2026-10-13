"""
Intelligent Model Router for AI Model Observer.

Routes LLM requests dynamically to the highest-performing model based on
verified task outcomes, historical pass rates, and latency/cost constraints.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger("observer.router")

DEFAULT_FALLBACK_MODEL = "deepseek-chat"


@dataclass
class RouterDecision:
    selected_model: str
    strategy: str
    reason: str
    is_fallback: bool
    metrics: Dict[str, Any]


def calculate_pass_rate(passes: int, fails: int) -> float:
    """Calculate pass rate with Laplace smoothing for statistical confidence."""
    total = passes + fails
    if total == 0:
        return 0.0
    # Add-1 smoothing: (passes + 1) / (total + 2)
    return round((passes + 1) / (total + 2), 4)


def select_optimal_model(
    model_stats: List[Dict[str, Any]],
    strategy: str = "best_pass_rate",
    task_type: Optional[str] = None,
    candidate_models: Optional[List[str]] = None,
    max_latency_ms: Optional[int] = None,
    default_model: str = DEFAULT_FALLBACK_MODEL,
) -> RouterDecision:
    """
    Select optimal model given historical performance statistics and constraints.

    Strategies:
    - 'best_pass_rate': Select model with highest outcome pass rate.
    - 'lowest_latency': Select model with lowest average latency.
    - 'balanced': Select model balancing pass rate and latency.
    """
    if not model_stats:
        return RouterDecision(
            selected_model=default_model,
            strategy=strategy,
            reason="No historical telemetry available; using default fallback.",
            is_fallback=True,
            metrics={}
        )

    # Filter candidates if explicit candidate list provided
    candidates = []
    for stat in model_stats:
        m_name = stat.get("model", "")
        if candidate_models and m_name not in candidate_models:
            continue
        candidates.append(stat)

    if not candidates:
        return RouterDecision(
            selected_model=default_model,
            strategy=strategy,
            reason="No matching candidate models found in statistics; using default fallback.",
            is_fallback=True,
            metrics={}
        )

    # Filter out models exceeding latency constraint if specified
    if max_latency_ms is not None:
        eligible = [c for c in candidates if (c.get("avg_latency_ms") or 0) <= max_latency_ms]
        if eligible:
            candidates = eligible
        else:
            logger.warning(
                f"All candidates exceed max latency {max_latency_ms}ms; proceeding with lowest latency model."
            )

    # Score candidates
    scored = []
    for c in candidates:
        passes = c.get("passes") or 0
        fails = c.get("fails") or 0
        calls = c.get("calls") or 0
        avg_lat = c.get("avg_latency_ms") or 1000
        pass_rate = calculate_pass_rate(passes, fails)

        if strategy == "lowest_latency":
            # Lower latency is better (sort ascending)
            score = -float(avg_lat)
        elif strategy == "balanced":
            # Composite score: pass rate weighted against normalized latency
            lat_penalty = min(avg_lat / 5000.0, 1.0) * 0.3
            score = pass_rate - lat_penalty
        else:  # best_pass_rate
            score = pass_rate

        scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_stat = scored[0]
    best_model = best_stat.get("model") or default_model

    return RouterDecision(
        selected_model=best_model,
        strategy=strategy,
        reason=f"Selected '{best_model}' via '{strategy}' (score: {best_score:.4f}, passes: {best_stat.get('passes', 0)}, fails: {best_stat.get('fails', 0)})",
        is_fallback=False,
        metrics={
            "calls": best_stat.get("calls", 0),
            "passes": best_stat.get("passes", 0),
            "fails": best_stat.get("fails", 0),
            "avg_latency_ms": best_stat.get("avg_latency_ms", 0),
            "score": round(best_score, 4),
        }
    )


async def resolve_dynamic_route(
    pool: Optional[Any],
    requested_model: str,
    headers: Dict[str, str],
    default_model: str = DEFAULT_FALLBACK_MODEL
) -> RouterDecision:
    """
    Check if requested model or headers require intelligent routing.
    If requested_model starts with 'auto' or 'router:', selects optimal model from database stats.
    """
    is_auto = requested_model.lower().startswith("auto") or requested_model.lower().startswith("router:")
    strategy_header = headers.get("x-route-strategy")

    if not is_auto and not strategy_header:
        return RouterDecision(
            selected_model=requested_model,
            strategy="direct",
            reason="Direct model specified without auto-routing request.",
            is_fallback=False,
            metrics={}
        )

    # Determine strategy
    strategy = strategy_header or "best_pass_rate"
    if "latency" in requested_model.lower():
        strategy = "lowest_latency"
    elif "balanced" in requested_model.lower():
        strategy = "balanced"

    # Extract task_type if encoded like 'auto:backend' or header 'x-task-type'
    task_type = None
    if ":" in requested_model:
        parts = requested_model.split(":", 1)
        if parts[1].strip() and parts[1].strip() not in ("fastest", "best", "balanced"):
            task_type = parts[1].strip()
    if not task_type:
        task_type = headers.get("x-task-type")

    # Max latency constraint from header
    max_lat = None
    if headers.get("x-max-latency-ms"):
        try:
            max_lat = int(headers["x-max-latency-ms"])
        except ValueError:
            pass

    if pool is None:
        return RouterDecision(
            selected_model=default_model,
            strategy=strategy,
            reason="Database pool unavailable for routing; falling back to default.",
            is_fallback=True,
            metrics={}
        )

    try:
        from app.storage import fetch_stats
        stats = await fetch_stats(pool)
        return select_optimal_model(
            model_stats=stats,
            strategy=strategy,
            task_type=task_type,
            max_latency_ms=max_lat,
            default_model=default_model
        )
    except Exception as e:
        logger.error(f"Error querying model stats for intelligent routing: {e}")
        return RouterDecision(
            selected_model=default_model,
            strategy=strategy,
            reason=f"Routing query failed ({e}); falling back to default.",
            is_fallback=True,
            metrics={}
        )
