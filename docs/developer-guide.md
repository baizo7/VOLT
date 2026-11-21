# VOLT-AI developer guide

## Requirements

- Python 3.9 or newer (see package metadata for the supported runtime).
- A VOLT API endpoint.
- A VOLT API credential or a personal provider key permitted by your deployment tier.

## Install the CLI

```bash
python -m pip install volt-ai
volt test
volt activate
```

The CLI stores local configuration under `~/.volt-ai/config.json`. Treat that file as sensitive because it can contain credentials.

## Quick API request

Set the server base URL and a key in your local shell. Never commit credentials.

### PowerShell

```powershell
$env:VOLT_BASE_URL = "https://volt-ai-lmgz.onrender.com"
$env:VOLT_API_KEY = "YOUR_VOLT_OR_PROVIDER_KEY"
```

### Bash

```bash
export VOLT_BASE_URL="https://volt-ai-lmgz.onrender.com"
export VOLT_API_KEY="YOUR_VOLT_OR_PROVIDER_KEY"
```

### Python

```python
import os
import httpx

base_url = os.environ["VOLT_BASE_URL"].rstrip("/")
api_key = os.environ["VOLT_API_KEY"]

response = httpx.post(
    f"{base_url}/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json={
        "model": "VOLT-AI",
        "messages": [
            {"role": "user", "content": "Explain binary search in Java."}
        ],
        "stream": False,
    },
    timeout=180.0,
)
response.raise_for_status()
payload = response.json()

print(payload["choices"][0]["message"]["content"])
print("Usage:", payload.get("usage", {}))
print("Coordination:", payload.get("volt_coordination", {}))
```

The response's `volt_coordination` metadata may include the selected track, specialist identifiers, routing reason, server-side latency, and whether a reasoning pass was used. Treat these values as operational metadata, not a guarantee of model quality.

## cURL

```bash
curl -X POST "$VOLT_BASE_URL/v1/chat/completions" \
  -H "Authorization: Bearer $VOLT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "VOLT-AI",
    "messages": [{"role": "user", "content": "Write quicksort in Python"}],
    "stream": false
  }'
```

## Compatible endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/chat/completions` | OpenAI-compatible chat completion |
| POST | `/v1/messages` | Anthropic Messages-compatible request |
| GET | `/v1/models` | Available model catalog |
| GET | `/health` | Readiness check |

Interactive API documentation is available at `/api/docs` if enabled by the deployed FastAPI configuration; the custom product documentation is at `/docs`.

## Performance fields

When returned by the API, `usage.prompt_tokens`, `usage.completion_tokens`, and `usage.total_tokens` are token counts. `volt_coordination.latency_ms` is server-reported coordination latency. Client-observed wall time also includes network and client overhead, so record both separately when benchmarking.

## Authentication and safe usage

- Use a dedicated API key for each application.
- Never send a provider key from a shared/public browser.
- Do not put credentials in source code, screenshots, issue reports, or command history.
- The statistics and trace endpoints are authenticated and session-scoped. Do not remove those checks to make a public dashboard.
- Follow the repository's `LICENSE` and attribution requirements.

## Local development

Clone the repository, create a virtual environment, install the repository's dependencies, configure environment variables based on `.env.example`, then start the FastAPI application using the command in the deployment configuration. Run tests with:

```bash
pytest -m "not integration"
```

Check the current `render.yaml`, `docker-compose.yml`, and `pyproject.toml` for the exact entrypoint and dependency configuration.
