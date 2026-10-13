from pathlib import Path
from datetime import datetime
import shutil
import sys

root = Path.cwd()
main_path = root / "main.py"
adapter_path = root / "app" / "opencode_adapter.py"

if not main_path.is_file() or not adapter_path.is_file():
    sys.exit("STOP: Expected project files were not found. No changes made.")

main = main_path.read_text(encoding="utf-8-sig")

old_routing = '''    requested_model = body.get("model", "unknown")
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
'''

new_routing = '''    requested_model = body.get("model", "unknown")
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
'''

old_rag = '    if inject_rag and pool is not None:'
new_rag = '''    if (
        inject_rag
        and not (isinstance(model, str) and model.startswith("opencode/"))
        and pool is not None
    ):'''

old_log = '            logger.warning(f"OpenCode adapter request failed: {exc}")'
new_log = '            logger.warning("OpenCode adapter request failed (%s)", type(exc).__name__)'

old_error = '                "error": str(exc)[:2000],'
new_error = '                "error": f"OpenCode adapter request failed ({type(exc).__name__})",'

old_response = '''                {"error": "OpenCode adapter request failed", "detail": str(exc)[:500]},
                status_code=502,
'''
new_response = '''                {"error": "OpenCode adapter request failed"},
                status_code=502,
'''

replacements = [
    (old_routing, new_routing, "routing"),
    (old_rag, new_rag, "RAG guard"),
    (old_log, new_log, "error log"),
    (old_error, new_error, "stored error"),
    (old_response, new_response, "error response"),
]

for old, new, label in replacements:
    count = main.count(old)
    if count != 1:
        sys.exit(f"STOP: Expected exactly one match for {label}, found {count}. No files changed.")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = root.parent / f"{root.name}-backup-opencode-{stamp}"
backup_dir.mkdir(parents=True)
shutil.copy2(main_path, backup_dir / "main.py")
shutil.copy2(adapter_path, backup_dir / "opencode_adapter.py")

for old, new, _ in replacements:
    main = main.replace(old, new, 1)

main_path.write_text(main, encoding="utf-8")
print("Patch applied to main.py.")
print(f"Backups saved in: {backup_dir}")
print("The adapter remains disabled; no model request was sent.")
