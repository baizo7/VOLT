Create a detailed implementation plan based on the latest Architect assessment in .forge/runs/run-002/01_architect.md and the current project files.

Goal: harden and test Phase 1 of AI Model Observer before adding Phase 2 features.

Prioritize:
1. Security: scrub all persisted strings, protect endpoints with configurable authentication, secure PostgreSQL credentials, bind its port to localhost, and never log secrets.
2. Input validation: reject non-object proxy bodies with HTTP 400 and validate /outcomes with Pydantic.
3. Streaming: bound capture memory while forwarding the complete stream.
4. Health and observability: database readiness checks and structured logging.
5. Automated unit, API, streaming, and PostgreSQL integration tests.
6. Correct /stats attribution for tasks using multiple models.
7. Update README with setup, configuration, security, retention, and testing.

Constraints:
- Do not modify forge.yaml or Forge stage, adapter, or model configuration.
- Preserve endpoint paths, header names, and routes.json format.
- Logging failures must never break the coding tool's request.
- Keep changes minimal and compatible with Phase 1.
- Planning only: do not implement code.
- Break work into small tasks with dependencies, affected files, acceptance criteria, and verification commands.
- Mark security-critical tasks as blockers before capturing real prompts or source code.
- Never claim tests passed unless they were executed.

Return the implementation plan and recommend the first Developer task.
