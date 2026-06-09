# External Integrations

**Analysis Date:** 2026-06-09

## APIs & External Services

**Google AI / Gemini:**
- Google GenAI (Gemini models) — LLM backbone for `dice_agent_rest` and `adk_expense_reimbursement`
  - SDK/Client: `google-genai` >=1.9.0 / >=1.27.0 (imported as `from google.genai import types`)
  - Auth: `GOOGLE_API_KEY` env var (dice), `GEMINI_API_KEY` env var (adk); alternatively `GOOGLE_GENAI_USE_VERTEXAI=TRUE` for Vertex AI authentication
  - Files: `dice_agent_rest/agent.py`, `dice_agent_rest/__main__.py`, `adk_expense_reimbursement/agent.py`, `adk_expense_reimbursement/__main__.py`

**Google Agent Development Kit (ADK):**
- `google-adk` >=1.0.0 / >=1.8.0 — agent runner, LLM agent abstraction, session/memory/artifact services
  - Components used: `LlmAgent`, `LiteLlm`, `Runner`, `InMemorySessionService`, `InMemoryMemoryService`, `InMemoryArtifactService`, `ToolContext`
  - Files: `dice_agent_rest/agent.py`, `adk_expense_reimbursement/agent.py`

**LangChain / LangGraph:**
- LangGraph + LangChain Google GenAI — agent orchestration for `helloworld`
  - SDK/Client: `langchain-google-genai` >=2.1.4, `langgraph` >=0.4.1
  - Auth: same `GOOGLE_API_KEY` / Gemini credentials inferred (loaded via `dotenv`)
  - Files: `helloworld/agent_executor.py`, `helloworld/pyproject.toml`

**LiteLLM:**
- Model abstraction layer used inside `adk_expense_reimbursement` via Google ADK's `LiteLlm` wrapper
  - SDK/Client: `litellm` (unpinned)
  - Files: `adk_expense_reimbursement/agent.py`

**A2A Protocol (Agent-to-Agent):**
- `a2a-sdk` — implements the A2A open protocol for agent discovery, task send, and streaming
  - All agents expose an HTTP endpoint serving an `AgentCard` at `/.well-known/agent.json`
  - Transport: HTTP+JSON (`A2ARESTFastAPIApplication`) or JSONRPC (`A2AStarletteApplication`)
  - Streaming: SSE (Server-Sent Events) via `sse-starlette`
  - Files: every agent's `__main__.py` and `agent_executor.py`

**Google Vertex AI (optional):**
- Vertex AI can substitute the direct Gemini API for `dice_agent_rest` and `adk_expense_reimbursement`
  - Activated by setting `GOOGLE_GENAI_USE_VERTEXAI=TRUE`; requires appropriate GCP credentials in the environment
  - Auth: ADC (Application Default Credentials) when Vertex AI mode is active

## Data Storage

**Databases:**
- In-memory task store (`InMemoryTaskStore`) — all agents use this for A2A task state; no persistent DB in use at runtime
- `helloworld` has `a2a-sdk[mysql]` extra declared in `helloworld/pyproject.toml` (MySQL-capable task store available but not instantiated in current code)
- `signing_and_verifying` has `a2a-sdk[sqlite]` extra declared in `signing_and_verifying/pyproject.toml` (SQLite-capable task store available but not instantiated in current code)

**File Storage:**
- Local filesystem only — `signing_and_verifying` writes a `public_keys.json` file at startup containing the EC public key PEM; served via a static `FileResponse` route at `/public_keys.json`
  - File: `signing_and_verifying/__main__.py`

**Caching:**
- None (all state is ephemeral / in-process)

## Authentication & Identity

**Agent Card Signing (JWS/EC):**
- `signing_and_verifying` agent generates a fresh ECDSA P-256 (`SECP256R1`) key pair at startup, signs its `AgentCard` responses using the `a2a-sdk`'s `create_agent_card_signer` utility with `ES256` JWS, and exposes the public key at `/public_keys.json` for client-side verification
  - Packages: `cryptography` >=43.0.0, `PyJWT` >=2.0.0
  - Files: `signing_and_verifying/__main__.py`, `signing_and_verifying/agent_executor.py`

**Extended Agent Card (authenticated users):**
- `helloworld` and `signing_and_verifying` implement a two-tier agent card pattern: a public card with basic skills and an extended card with additional skills for authenticated callers, using the A2A SDK's `extended_agent_card` capability
  - Files: `helloworld/__main__.py`, `signing_and_verifying/__main__.py`

**Custom Auth:**
- Not implemented — no OAuth, API key validation, or session auth on the agent HTTP endpoints themselves (these are dev-only peers)

## Monitoring & Observability

**Error Tracking:**
- Not detected — no Sentry, Datadog, or similar

**Logs:**
- Standard Python `logging` module with `basicConfig()` — used by `dice_agent_rest/__main__.py` and `adk_expense_reimbursement/__main__.py`; other agents use print/default output

## CI/CD & Deployment

**Hosting:**
- Docker Compose — the canonical way to run all peers; `docker compose --profile a2a-peers up -d --build`
- Each agent has a `Dockerfile` using `python:3.11-slim` + `uv`
- Ports: `helloworld`:10001, `number_guessing_game` Alice:10002, Carol:10004, `dice_agent_rest`:10005, `signing_and_verifying`:10006, `adk_expense_reimbursement`:10007
- All containers expose port 9999 internally; host port mapping is defined in the parent Cinatra monorepo's `docker-compose.yml`

**Host Launchers (macOS SSE workaround):**
- `number_guessing_game/run_host_alice.py` — runs Alice on port 10002
- `number_guessing_game/run_host_carol.py` — runs Carol on port 10004
- `signing_and_verifying/run_host.py` — runs signing agent on port 10006
- `dice_agent_rest` and `adk_expense_reimbursement` launched with `uv run . --host 127.0.0.1 --port <N>`

**CI Pipeline:**
- Not detected — no GitHub Actions, CircleCI, or other CI config present in this repo

## Environment Configuration

**Required env vars:**
- `GOOGLE_API_KEY` — Gemini API key for `dice_agent_rest` (unless Vertex AI)
- `GEMINI_API_KEY` — Gemini API key for `adk_expense_reimbursement` (unless Vertex AI)
- `GOOGLE_GENAI_USE_VERTEXAI` — set to `TRUE` to use Vertex AI instead of direct API keys (both LLM-backed agents)

**Optional env vars:**
- `CINATRA_A2A_SERVERS_DEV_REPO_URL` — alternate clone URL used by parent Cinatra monorepo

**Secrets location:**
- `.env` files per agent directory (gitignored); in docker-compose, keys are forwarded from the parent Cinatra `.env` as `GEMINI_API_KEY` with `GOOGLE_API_KEY` as fallback

## Webhooks & Callbacks

**Incoming:**
- A2A task endpoints on each agent (task send, streaming, agent card fetch) — these are the peer HTTP endpoints consumed by the Cinatra A2A connector during local development

**Outgoing:**
- None — agents are purely server-side; they do not call back to Cinatra or any external webhook URL

---

*Integration audit: 2026-06-09*
