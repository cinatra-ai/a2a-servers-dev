<!-- refreshed: 2026-06-09 -->
# Architecture

**Analysis Date:** 2026-06-09

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                   Cinatra dev stack (docker-compose)                     │
│                   CINATRA_A2A_DEV_PEER_URLS auto-import                  │
└────────┬──────────┬──────────┬──────────┬──────────┬──────────┬─────────┘
         │          │          │          │          │          │
         ▼          ▼          ▼          ▼          ▼          ▼
  helloworld  number_guessing  dice_agent  signing_  adk_expense
  :10001      _game            _rest       and_      reimbursement
              Alice:10002      :10005      verifying :10007
              Carol:10004                 :10006
┌──────────────────────────────────────────────────────────────────────────┐
│             A2A SDK layer (a2a-sdk Python package)                        │
│  A2AStarletteApplication → DefaultRequestHandler → InMemoryTaskStore     │
└──────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  AgentExecutor implementations (per-agent business logic)                │
│  `helloworld/agent_executor.py`                                          │
│  `dice_agent_rest/agent_executor.py`                                     │
│  `signing_and_verifying/agent_executor.py`                               │
│  `adk_expense_reimbursement/agent_executor.py`                           │
│  `number_guessing_game/agent_Alice.py`                                   │
│  `number_guessing_game/agent_Carol.py`                                   │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Agent Core / LLM backends                                               │
│  Simple agents: pure Python logic                                        │
│  LLM-backed agents: google.adk Runner + LlmAgent + InMemory* services   │
│  `dice_agent_rest/agent.py`                                              │
│  `adk_expense_reimbursement/agent.py`                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `HelloWorldAgentExecutor` | Enqueues TaskStatus + TextArtifact events for a static reply | `helloworld/agent_executor.py` |
| `HelloWorldAgent` | Returns the string `'Hello, World!'` | `helloworld/agent_executor.py` |
| `helloworld/__main__.py` | Builds AgentCard (public + extended), constructs A2AStarletteApplication, runs uvicorn on port 9999 | `helloworld/__main__.py` |
| `NumberGuessExecutor` | Evaluates a numeric guess against a secret; replies higher/lower/correct | `number_guessing_game/agent_Alice.py` |
| `AgentBob` | CLI guesser; calls Alice over A2A HTTP, not an HTTP server itself | `number_guessing_game/agent_Bob.py` |
| `AgentCarol` | Orchestrator; sends guesses to Alice on behalf of Bob | `number_guessing_game/agent_Carol.py` |
| `utils.server.build_starlette_app` | Shared factory: wraps any executor in DefaultRequestHandler + InMemoryTaskStore + A2AStarletteApplication | `number_guessing_game/utils/server.py` |
| `utils.server.run_agent_blocking` | Calls `build_starlette_app` then starts uvicorn synchronously | `number_guessing_game/utils/server.py` |
| `DiceAgent` | Wraps a Google ADK `LlmAgent` (gemini-2.0-flash); exposes async `stream()` | `dice_agent_rest/agent.py` |
| `DiceAgentExecutor` | Bridges `DiceAgent.stream()` to A2A EventQueue | `dice_agent_rest/agent_executor.py` |
| `ReimbursementAgent` | Wraps a Google ADK `LlmAgent` (LiteLLM/Gemini); exposes async `stream()` | `adk_expense_reimbursement/agent.py` |
| `SignedAgentExecutor` | Echoes a static "Verify me!" message; demonstrates signed AgentCard flow | `signing_and_verifying/agent_executor.py` |
| `signing_and_verifying/__main__.py` | Generates EC key pair at startup, signs AgentCard via JWS, exposes `/public_keys.json` | `signing_and_verifying/__main__.py` |
| `config.py` | Centralised port constants for number_guessing_game agents | `number_guessing_game/config.py` |

## Pattern Overview

**Overall:** Collection of self-contained A2A peer servers, each following the same Agent Executor pattern from the `a2a-sdk` Python library.

**Key Characteristics:**
- Every active peer exposes an HTTP server via `uvicorn` + Starlette (ASGI).
- Protocol routing is handled entirely by `A2AStarletteApplication` from `a2a-sdk`; agents only implement `AgentExecutor.execute()` and optionally `cancel()`.
- Task state is held in-memory (`InMemoryTaskStore`); no persistence across restarts.
- LLM-backed peers (`dice_agent_rest`, `adk_expense_reimbursement`) use Google ADK `Runner` + `LlmAgent` with all-in-memory service backends.
- Non-LLM peers implement pure-Python logic directly inside `AgentExecutor.execute()`.
- Each peer is its own deployable unit with its own `pyproject.toml` and `Dockerfile`.

## Layers

**A2A SDK / Server layer:**
- Purpose: HTTP transport, JSON-RPC routing, task lifecycle management
- Location: third-party `a2a-sdk` package (imported as `a2a.*`)
- Contains: `A2AStarletteApplication`, `DefaultRequestHandler`, `InMemoryTaskStore`, `AgentExecutor` base class, `EventQueue`, `TaskUpdater`, A2A type definitions
- Depends on: Starlette, uvicorn, pydantic
- Used by: all agent `__main__.py` and `agent_executor.py` files

**AgentExecutor layer:**
- Purpose: Glue between the A2A SDK and each agent's business logic
- Location: `<agent>/agent_executor.py` (or inline in `agent_Alice.py`, `agent_Bob.py`, `agent_Carol.py`)
- Contains: `AgentExecutor` subclass with `execute()` and `cancel()` methods; event-queue manipulation
- Depends on: A2A SDK layer, Agent Core layer
- Used by: `DefaultRequestHandler` (via dependency injection in `__main__.py`)

**Agent Core layer:**
- Purpose: Business logic — pure Python for simple agents, LLM orchestration for complex ones
- Location: `<agent>/agent.py` (dice, adk_expense), inline in executor files (helloworld, signing, number_guessing_game)
- Contains: domain functions, LLM agent construction, streaming output
- Depends on: `google.adk`, `google.genai` (LLM peers only); pure stdlib for simple peers
- Used by: AgentExecutor layer

**Entry-point / server assembly layer:**
- Purpose: Wire together AgentCard metadata, executor, and server; start uvicorn
- Location: `<agent>/__main__.py` and `run_host_*.py` launchers
- Contains: AgentCard / AgentSkill declarations, app construction, uvicorn.run() call
- Depends on: all layers above
- Used by: Docker `CMD` or direct `uv run` invocations

## Data Flow

### Inbound A2A request (typical peer)

1. Uvicorn receives HTTP POST on `/` (or `/a2a/v1`) (`<agent>/__main__.py` → uvicorn.run)
2. `A2AStarletteApplication` routes it to `DefaultRequestHandler`
3. `DefaultRequestHandler` looks up or creates a task in `InMemoryTaskStore`, constructs `RequestContext`, and calls `AgentExecutor.execute(context, event_queue)`
4. Executor enqueues `TaskStatusUpdateEvent` (WORKING) → calls agent logic → enqueues `TaskArtifactUpdateEvent` → enqueues `TaskStatusUpdateEvent` (COMPLETED)
5. SDK streams or returns events to the caller

### LLM-backed streaming flow (dice_agent_rest, adk_expense_reimbursement)

1. Executor calls `agent.stream(query, session_id)` which yields `(is_final, text)` tuples
2. For each non-final yield, executor enqueues a WORKING status event
3. On final yield, executor enqueues text artifact + COMPLETED status event
4. Google ADK `Runner.run_async()` handles model calls, tool dispatch, and session management internally

### Signed AgentCard flow (signing_and_verifying)

1. At startup, EC key pair generated; public key written to `public_keys.json`
2. `create_agent_card_signer` wraps the private key into a `card_modifier` callable
3. `A2AStarletteApplication` invokes the modifier before serving `/.well-known/agent.json` and the extended card endpoint
4. Clients fetch `/public_keys.json` to verify the JWS signature on the card

**State Management:**
- All task state is ephemeral (`InMemoryTaskStore`). Restarting a peer clears all task history.
- LLM peers maintain per-session conversation history via `InMemorySessionService` inside the ADK `Runner`.

## Key Abstractions

**AgentExecutor:**
- Purpose: Single interface every peer must implement; decouples business logic from A2A transport
- Examples: `helloworld/agent_executor.py`, `dice_agent_rest/agent_executor.py`, `signing_and_verifying/agent_executor.py`, `adk_expense_reimbursement/agent_executor.py`, `number_guessing_game/agent_Alice.py`
- Pattern: Subclass `a2a.server.agent_execution.AgentExecutor`; implement `async execute(context, event_queue)` and `async cancel(context, event_queue)`

**AgentCard:**
- Purpose: Machine-readable metadata describing the peer (name, skills, interfaces, capabilities)
- Examples: declared inline in every `__main__.py`; also as raw `dict` validated with `AgentCard.model_validate()` in number_guessing_game agents
- Pattern: Pydantic model from `a2a.types`; may be public + extended variants (helloworld, signing_and_verifying)

**EventQueue:**
- Purpose: Ordered channel through which executors publish task lifecycle events to the SDK
- Pattern: Call `await event_queue.enqueue_event(...)` with `TaskStatusUpdateEvent` or `TaskArtifactUpdateEvent` instances

**TaskUpdater (convenience wrapper):**
- Purpose: Higher-level helper over EventQueue; used by number_guessing_game agents
- Examples: `number_guessing_game/agent_Alice.py` — `await updater.submit() / add_artifact() / complete()`

## Entry Points

**Docker / container:**
- Location: `<agent>/Dockerfile` (each peer), `<agent>/Containerfile` (helloworld, signing_and_verifying)
- Triggers: `docker compose --profile a2a-peers up -d --build`
- Responsibilities: Build image, run `python -m <agent>` or `uv run .`

**Direct host run (`__main__.py`):**
- Location: `helloworld/__main__.py`, `dice_agent_rest/__main__.py`, `signing_and_verifying/__main__.py`, `adk_expense_reimbursement/__main__.py`
- Triggers: `uv run .` inside the agent directory
- Responsibilities: Declare AgentCard, instantiate executor, start uvicorn

**Host-run launchers (macOS SSE workaround):**
- Location: `number_guessing_game/run_host_alice.py`, `number_guessing_game/run_host_carol.py`, `signing_and_verifying/run_host.py`
- Triggers: `uv run run_host_alice.py` etc.
- Responsibilities: Override port to host-mapped value (e.g. 10002 instead of 8001), start uvicorn on `127.0.0.1`

## Architectural Constraints

- **Threading:** Single-threaded async event loop via uvicorn/asyncio; all `AgentExecutor.execute()` methods are `async`.
- **Global state:** `number_guessing_game/utils/game_logic.py` holds the secret number as module-level state; restarting the process resets it. `adk_expense_reimbursement/agent.py` holds `request_ids` as a module-level `set`.
- **Circular imports:** None detected.
- **No shared runtime:** Each agent is a fully independent Python process with its own dependencies, lockfile, and network port.
- **In-memory only:** No database, no file persistence (except `signing_and_verifying` writing `public_keys.json` at startup for the JWK endpoint).

## Anti-Patterns

### Port constant mismatch

**What happens:** `number_guessing_game/config.py` defines `AGENT_ALICE_PORT = 8001` but `run_host_alice.py` overrides with `HOST_PORT = 10002` at the module level without importing from `config.py`.
**Why it's wrong:** The canonical port lives in two places; updating `config.py` does not update the host launcher.
**Do this instead:** Import `AGENT_ALICE_PORT` from `config.py` and define the host port offset relative to it, or add a dedicated `HOST_ALICE_PORT` constant to `config.py`.

### Inline `if __name__ == '__main__'` server code in agent files

**What happens:** `number_guessing_game/agent_Alice.py` contains the agent class, card declaration, and a `__main__` block all in one file.
**Why it's wrong:** Makes unit-testing the executor harder (importing the module triggers no side effects only if guarded, but the card dict is still evaluated at import time).
**Do this instead:** Follow the `helloworld` pattern — separate `agent.py` / `agent_executor.py` / `__main__.py`.

## Error Handling

**Strategy:** Minimal — agents raise exceptions or print to stdout; the A2A SDK surfaces unhandled errors as JSON-RPC error responses.

**Patterns:**
- `cancel()` raises `Exception('cancel not supported')` in helloworld and dice_agent_rest.
- `cancel()` calls `updater.reject()` in number_guessing_game (more correct A2A behaviour).
- LLM errors from google.adk propagate as unhandled exceptions out of `stream()`.

## Cross-Cutting Concerns

**Logging:** `print()` statements only; no structured logging library.
**Validation:** AgentCard metadata validated via `AgentCard.model_validate()` (pydantic); no input sanitisation on message text.
**Authentication:** `signing_and_verifying` demonstrates JWS-signed AgentCards (EC/ES256). All other peers serve unauthenticated cards. Extended agent cards (helloworld, signing_and_verifying) are gated by the A2A SDK's authentication middleware, but no custom auth is implemented in these sample peers.

---

*Architecture analysis: 2026-06-09*
