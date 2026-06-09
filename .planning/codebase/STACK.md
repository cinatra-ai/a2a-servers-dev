# Technology Stack

**Analysis Date:** 2026-06-09

## Languages

**Primary:**
- Python 3.10–3.13 - All agent implementations (version varies per agent; `adk_expense_reimbursement` requires >=3.13, others >=3.10 or >=3.11)

**Secondary:**
- None detected

## Runtime

**Environment:**
- CPython (standard Python runtime), run via `uv run`

**Package Manager:**
- `uv` (Astral) — used for dependency sync and project execution in all agents
- Lockfiles: present in `helloworld/uv.lock`, `dice_agent_rest/uv.lock`, `signing_and_verifying/uv.lock`; absent in `adk_expense_reimbursement/` and `number_guessing_game/` (uses `requirements.txt` instead)

## Frameworks

**Core (ASGI/HTTP serving):**
- `uvicorn` >=0.34.2 / ==0.35.0 — ASGI server for all agents
- `starlette` >=0.46.2 — underlying web framework for most agents (via `A2AStarletteApplication`)
- `fastapi` >=0.115.0 — used by `signing_and_verifying` agent only
- `sse-starlette` >=2.3.5 — Server-Sent Events streaming support (`helloworld`, `signing_and_verifying`)

**Agent SDK:**
- `a2a-sdk` — the A2A (Agent-to-Agent) Python SDK; version varies:
  - `a2a-sdk[mysql]>=1.0.0a0` — `helloworld` (MySQL-backed task store extras)
  - `a2a-sdk[sqlite]>=1.0.0a0` — `signing_and_verifying` (SQLite-backed task store extras)
  - `a2a-sdk==0.3.0` — `number_guessing_game`
  - `a2a-sdk>=0.3.0` — `dice_agent_rest`, `adk_expense_reimbursement`

**LLM / AI:**
- `google-adk` >=1.0.0 / >=1.8.0 — Google Agent Development Kit; used by `dice_agent_rest` and `adk_expense_reimbursement`
- `google-genai` >=1.9.0 / >=1.27.0 — Google GenAI client; used by `dice_agent_rest` and `adk_expense_reimbursement`
- `langchain-google-genai` >=2.1.4 — LangChain Google GenAI integration; used by `helloworld`
- `langgraph` >=0.4.1 — LangGraph agent orchestration; used by `helloworld`
- `litellm` (unpinned) — LiteLLM for model abstraction; used by `adk_expense_reimbursement`

**CLI:**
- `click` >=8.1.8 — CLI option parsing for `dice_agent_rest` and `adk_expense_reimbursement`
- `asyncclick` >=8.1.8 — async variant of click; used by `dice_agent_rest`

**Cryptography / Auth:**
- `cryptography` >=43.0.0 — EC key generation and PEM serialization; used by `signing_and_verifying`
- `PyJWT` >=2.0.0 — JWT handling; used by `signing_and_verifying`

**HTTP Client:**
- `httpx` >=0.28.1 — async HTTP client; used by `helloworld`, `dice_agent_rest`, `signing_and_verifying`

**Data Validation:**
- `pydantic` >=2.11.4 — used by `helloworld`, `dice_agent_rest`, `signing_and_verifying`

**gRPC:**
- `grpcio` >=1.60, `grpcio-tools` >=1.60, `grpcio_reflection` >=1.7.0 — used by `dice_agent_rest` (likely for Google ADK internals)

## Key Dependencies

**Critical:**
- `a2a-sdk` — the entire A2A protocol implementation (AgentCard, AgentSkill, task store, request handlers, JSONRPC/HTTP server apps) lives here
- `google-adk` — LLM agent execution engine for the two AI-backed peers (`dice_agent_rest`, `adk_expense_reimbursement`)

**Infrastructure:**
- `uvicorn` — ASGI process runner in all containers
- `uv` — installed inside Docker images via `pip install uv`; used for dependency sync and `uv run` entrypoint

## Configuration

**Environment:**
- `.env` files loaded via `python-dotenv` (`load_dotenv()`) in all agents that need secrets
- `.env` and `.env.*` are gitignored (`.env.example` is allowed)
- `GOOGLE_API_KEY` — required by `dice_agent_rest` unless `GOOGLE_GENAI_USE_VERTEXAI=TRUE`
- `GEMINI_API_KEY` — required by `adk_expense_reimbursement` unless `GOOGLE_GENAI_USE_VERTEXAI=TRUE`
- `CINATRA_A2A_SERVERS_DEV_REPO_URL` — optional; overrides clone URL in the parent Cinatra monorepo
- `CINATRA_A2A_DEV_PEER_URLS` — set in parent `.env.local` to register peers with the dev server

**Build:**
- Each agent has its own `pyproject.toml` using `hatchling` as build backend
- Dockerfiles use `python:3.11-slim` base image for all agents
- `uv sync --frozen --no-dev` is the install command inside Docker

## Platform Requirements

**Development:**
- `uv` installed locally
- Python >=3.10 (3.13 for `adk_expense_reimbursement`)
- Docker / Docker Compose for containerized operation
- Google/Gemini API key for `dice_agent_rest` (port 10005) and `adk_expense_reimbursement` (port 10007)

**Production:**
- Not applicable — development-only fixtures, never deployed to production. Consumed exclusively by `cinatra setup {dev,branch,clone}` which clones this repo into `dev/a2a-peers/` of the Cinatra monorepo working tree.

---

*Stack analysis: 2026-06-09*
