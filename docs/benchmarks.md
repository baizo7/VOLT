# VOLT benchmark reporting

This file defines how to produce defensible performance results. It intentionally contains no pre-filled latency or quality claims.

## What to report

- Test date and UTC time.
- VOLT deployment/commit identifier.
- Endpoint and model identifier.
- Provider and configured route (where disclosure is permitted).
- Prompt set/version and prompt count.
- Concurrency and warm-up count.
- Successful, failed, timed-out and rate-limited requests.
- Client-observed wall-clock latency: median (P50), P95 and mean.
- Server-reported `volt_coordination.latency_ms`, where present.
- Prompt, completion and total tokens from API usage.
- Throughput only when measured over a clearly defined interval.

## Method

1. Use fixed, non-sensitive prompts with documented input sizes.
2. Warm up the service before collecting samples.
3. Keep concurrency, timeout, and prompt set consistent across runs.
4. Record all failures; do not silently discard slow or unsuccessful requests.
5. Run multiple repetitions and report sample counts.
6. Separate cold-start observations from steady-state observations.
7. Compare models only when provider, hardware, prompt set, and generation settings are sufficiently comparable.
8. Do not describe a simulated response or routing estimate as a live benchmark.

## Reproducible runner

Run `python benchmarks/benchmark_latency.py --help` for options. The runner writes raw JSONL samples and a Markdown summary. The API key is read from an environment variable and is never written to the result file.

## Results

Add dated reports under `benchmarks/results/`. Include methodology and environment details with each report. Do not commit raw prompts that contain user data, private source code, or secrets.
