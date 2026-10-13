"""
Route resolution module mapping model names to upstream provider endpoints.
"""
import json
import os
from typing import Dict, Any, Optional
from app.config import DEFAULT_BASE, ROUTES_FILE


def load_routes(file_path: Optional[str] = None) -> Dict[str, Any]:
    """Load route definitions from JSON configuration file."""
    path = file_path or ROUTES_FILE
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def resolve_route(model: str, style: str, routes_map: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Resolve upstream configuration for a given model prefix.
    Falls back to wildcard '*' rule or default base URL for the given style.
    """
    mapping = routes_map if routes_map is not None else {}
    fallback = None
    for prefix, cfg in mapping.items():
        if prefix == "*":
            fallback = cfg
        elif model.startswith(prefix):
            return cfg
    return fallback or {"base_url": DEFAULT_BASE[style], "api_key_env": None}
