# Codebase Structure

**Analysis Date:** 2026-06-09

## Directory Layout

```
a2a-servers-dev/                        # Repo root — collection of A2A sample peer agents
├── helloworld/                         # Peer: static "Hello World" agent (port 10001 / 9999)
│   ├── __init__.py
│   ├── __main__.py                     # Entry point; AgentCard + uvicorn startup
│   ├── agent_executor.py               # HelloWorldAgent + HelloWorldAgentExecutor
│   ├── test_client.py                  # Manual smoke-test client
│   ├── pyproject.toml                  # Python project manifest (hatchling, a2a-sdk dep)
│   ├── uv.lock                         # Lockfile (uv)
│   ├── Dockerfile
│   ├── Containerfile
│   └── README.md
├── number_guessing_game/               # Peer: multi-agent toy game (Alice:10002, Carol:10004)
│   ├── agent_Alice.py                  # AgentExecutor + AgentCard for Alice (evaluator)
│   ├── agent_Bob.py                    # CLI guesser; not an HTTP server
│   ├── agent_Carol.py                  # Orchestrator agent
│   ├── config.py                       # Centralised port constants
│   ├── run_host_alice.py               # Host-run launcher for Alice (port 10002)
│   ├── run_host_carol.py               # Host-run launcher for Carol (port 10004)
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── Dockerfile
│   └── utils/
│       ├── __init__.py
│       ├── game_logic.py               # Secret-number state + process_guess()
│       ├── helpers.py                  # Misc helpers
│       ├── protocol_wrappers.py        # A2A message construction helpers
│       └── server.py                   # Shared build_starlette_app / run_agent_blocking
├── dice_agent_rest/                    # Peer: LLM-backed dice roller (port 10005, needs GOOGLE_API_KEY)
│   ├── __init__.py
│   ├── __main__.py                     # Entry point
│   ├── agent.py                        # DiceAgent wrapping google.adk LlmAgent
│   ├── agent_executor.py               # DiceAgentExecutor
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── Dockerfile
│   └── README.md
├── signing_and_verifying/              # Peer: signed AgentCard demo (port 10006)
│   ├── __init__.py
│   ├── __main__.py                     # Generates EC key pair, wires JWS signer, starts server
│   ├── agent_executor.py               # SignedAgentExecutor
│   ├── run_host.py                     # Host-run launcher
│   ├── test_client.py                  # Manual smoke-test client
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── Dockerfile
│   ├── Containerfile
│   └── README.md
├── adk_expense_reimbursement/          # Peer: LLM-backed expense flow (port 10007, needs GEMINI_API_KEY)
│   ├── __init__.py
│   ├── __main__.py
│   ├── agent.py                        # ReimbursementAgent wrapping google.adk LlmAgent
│   ├── agent_executor.py               # Executor bridging stream() to EventQueue
│   ├── pyproject.toml
│   └── Dockerfile
├── LICENSE                             # Apache-2.0
├── NOTICE                              # Attribution / provenance
├── README.md                           # Repo overview, port table, run instructions
└── .gitignore
```

## Directory Purposes

**`helloworld/`:**
- Purpose: Simplest reference peer; demonstrates streaming task events and public + extended AgentCard
- Contains: AgentExecutor with static response, dual AgentCard (public/extended), test client
- Key files: `helloworld/__main__.py`, `helloworld/agent_executor.py`

**`number_guessing_game/`:**
- Purpose: Multi-agent demo (Alice evaluator + Bob CLI guesser + Carol orchestrator); shows agent-to-agent A2A calls
- Contains: Three agent modules, shared utilities under `utils/`, centralised config, host launchers
- Key files: `number_guessing_game/agent_Alice.py`, `number_guessing_game/utils/server.py`, `number_guessing_game/config.py`

**`number_guessing_game/utils/`:**
- Purpose: Shared helpers reused across Alice, Bob, Carol
- Contains: `server.py` (ASGI factory), `game_logic.py` (secret number), `protocol_wrappers.py`, `helpers.py`

**`dice_agent_rest/`:**
- Purpose: LLM-backed peer showing Google ADK integration and tool-use (roll dice, check primes)
- Contains: `agent.py` (core ADK logic), `agent_executor.py` (A2A bridge)
- Key files: `dice_agent_rest/agent.py`, `dice_agent_rest/agent_executor.py`

**`signing_and_verifying/`:**
- Purpose: Demonstrates JWS-signed AgentCards (ES256) and public-key endpoint
- Contains: Key generation in `__main__.py`, static executor, `/public_keys.json` route
- Key files: `signing_and_verifying/__main__.py`, `signing_and_verifying/agent_executor.py`

**`adk_expense_reimbursement/`:**
- Purpose: LLM-backed peer demonstrating multi-turn form-based workflows via ADK
- Contains: `agent.py` (form creation, reimbursement tools), `agent_executor.py`
- Key files: `adk_expense_reimbursement/agent.py`

## Key File Locations

**Entry Points:**
- `helloworld/__main__.py`: Builds and runs helloworld peer
- `dice_agent_rest/__main__.py`: Builds and runs dice peer
- `signing_and_verifying/__main__.py`: Generates signing keys, builds and runs signing peer
- `adk_expense_reimbursement/__main__.py`: Builds and runs expense peer
- `number_guessing_game/agent_Alice.py` (`__main__` block): Runs Alice directly
- `number_guessing_game/run_host_alice.py`: Host-run Alice at port 10002
- `number_guessing_game/run_host_carol.py`: Host-run Carol at port 10004
- `signing_and_verifying/run_host.py`: Host-run signing peer

**Shared Server Factory:**
- `number_guessing_game/utils/server.py`: `build_starlette_app()` and `run_agent_blocking()` — used by all number_guessing_game agents

**Port Configuration:**
- `number_guessing_game/config.py`: `AGENT_ALICE_PORT`, `AGENT_BOB_PORT`, `AGENT_CAROL_PORT`

**Core Agent Logic:**
- `dice_agent_rest/agent.py`: `DiceAgent` class with `stream()` method
- `adk_expense_reimbursement/agent.py`: `ReimbursementAgent` class with `stream()` method
- `number_guessing_game/utils/game_logic.py`: Secret number state and guess evaluation

**AgentExecutors:**
- `helloworld/agent_executor.py`
- `dice_agent_rest/agent_executor.py`
- `signing_and_verifying/agent_executor.py`
- `adk_expense_reimbursement/agent_executor.py`
- `number_guessing_game/agent_Alice.py` (executor class inline)

**Testing:**
- `helloworld/test_client.py`: Manual smoke-test for helloworld peer
- `signing_and_verifying/test_client.py`: Manual smoke-test for signing peer

**Container definitions:**
- `<agent>/Dockerfile`: Docker build for each peer (used by docker-compose)
- `helloworld/Containerfile`, `signing_and_verifying/Containerfile`: OCI alternative for Podman

## Naming Conventions

**Files:**
- Agent entry points: `__main__.py` (standard Python package entry)
- Executor files: `agent_executor.py` (consistent across all peers)
- Agent core logic: `agent.py` (dice, adk_expense) or inline in `agent_<Name>.py` (number_guessing_game)
- Host-run launchers: `run_host.py` / `run_host_<role>.py`
- Test clients: `test_client.py`

**Directories:**
- One directory per peer, named in `snake_case` matching the agent's concept (e.g. `dice_agent_rest`, `signing_and_verifying`)

**Classes:**
- AgentExecutors: `<Role>AgentExecutor` or `<Name>Executor` (e.g. `HelloWorldAgentExecutor`, `NumberGuessExecutor`, `SignedAgentExecutor`)
- Agent cores: `<Concept>Agent` (e.g. `HelloWorldAgent`, `DiceAgent`, `ReimbursementAgent`)

**Constants:**
- `UPPER_SNAKE_CASE` (e.g. `AGENT_ALICE_PORT`, `HOST_PORT`, `SUPPORTED_CONTENT_TYPES`)

## Where to Add New Code

**New A2A peer agent:**
1. Create `<new_agent>/` directory at repo root
2. Add `<new_agent>/pyproject.toml` (follow `helloworld/pyproject.toml` as template)
3. Add `<new_agent>/agent_executor.py` — subclass `AgentExecutor` from `a2a.server.agent_execution`
4. Add `<new_agent>/__main__.py` — declare `AgentCard`, wire `DefaultRequestHandler`, call `uvicorn.run()`
5. Add `<new_agent>/Dockerfile`
6. Update `README.md` port table

**New business logic in an existing LLM peer:**
- Add tool functions to `<agent>/agent.py` and include them in the `LlmAgent(tools=[...])` list

**New skill on an existing peer:**
- Add `AgentSkill(...)` in `<agent>/__main__.py` and add it to the `AgentCard.skills` list

**New shared utility for number_guessing_game:**
- Add to `number_guessing_game/utils/` and export from `number_guessing_game/utils/__init__.py`

**Host-run launcher for a new peer (macOS SSE workaround):**
- Create `<agent>/run_host.py` following `signing_and_verifying/run_host.py` as a template; override port to the docker-compose host-mapped port

## Special Directories

**`.planning/codebase/`:**
- Purpose: GSD codebase analysis documents
- Generated: Yes (by GSD mapper agent)
- Committed: No (not in source history by default)

**`<agent>/.vscode/`:**
- Purpose: VS Code launch configurations for running/debugging peers locally
- Key files: `dice_agent_rest/.vscode/launch.json`, `helloworld/.vscode/launch.json`
- Committed: Yes

---

*Structure analysis: 2026-06-09*
