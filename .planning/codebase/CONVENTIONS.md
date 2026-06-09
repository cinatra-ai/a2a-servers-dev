# Coding Conventions

**Analysis Date:** 2026-06-09

## Naming Patterns

**Files:**
- `snake_case` for all Python source files: `agent_executor.py`, `game_logic.py`, `protocol_wrappers.py`
- `__main__.py` for runnable entry points in each sub-package
- `__init__.py` for package markers (often empty)
- Agent files named after their role: `agent_Alice.py`, `agent_Bob.py`, `agent_Carol.py`

**Functions:**
- `snake_case` throughout: `process_guess`, `build_visualisation`, `parse_int_in_range`, `try_parse_json`
- Async methods named after their action: `execute`, `cancel`, `stream`, `invoke`
- Tool functions have plain descriptive names matching their Google ADK registration: `roll_dice`, `check_prime`, `create_request_form`, `reimburse`, `return_form`

**Variables:**
- `snake_case` for all variables and parameters
- Module-level state uses leading underscore prefix for "private" globals: `_target_number`, `_attempts`, `_secret_logged` in `number_guessing_game/utils/game_logic.py`
- Constants in `UPPER_SNAKE_CASE`: `AGENT_ALICE_PORT`, `AGENT_BOB_PORT`, `LITELLM_MODEL`

**Classes:**
- `PascalCase` for all classes: `HelloWorldAgent`, `HelloWorldAgentExecutor`, `SignedAgentExecutor`, `ReimbursementAgent`, `DiceAgent`
- Executors always suffixed with `AgentExecutor`

**Types:**
- Modern union syntax preferred where supported: `int | None`, `str | None`
- `from __future__ import annotations` used in `number_guessing_game/utils/game_logic.py` and `number_guessing_game/utils/helpers.py` to enable forward references
- `Optional[str]` used in `adk_expense_reimbursement/agent.py` (mixed style between sub-packages)

## Code Style

**Formatting:**
- No project-wide formatter config detected; `signing_and_verifying/pyproject.toml` sets `line-length = 110` under `[tool.lint]`
- 4-space indentation throughout
- Trailing commas used in multi-line structures

**Linting:**
- `ruff` referenced in `signing_and_verifying/pyproject.toml` under `[tool.ruff.lint]` with `ignore = ["E203"]`
- No shared root-level linting config — each sub-package is independently configured (or not configured at all)
- `# type: ignore` annotations used liberally to suppress mypy errors for SDK imports: `helloworld/__main__.py`, `number_guessing_game/agent_Bob.py`, `number_guessing_game/agent_Carol.py`, `number_guessing_game/utils/server.py`, `number_guessing_game/utils/protocol_wrappers.py`, `dice_agent_rest/__main__.py`

## Import Organization

**Order (observed pattern):**
1. `from __future__ import annotations` (when used)
2. Standard library imports (`json`, `os`, `random`, `logging`, `uuid`)
3. Third-party SDK imports (`a2a.*`, `google.adk.*`, `google.genai.*`, `httpx`, `uvicorn`, `pydantic`)
4. Local/relative imports (`from config import ...`, `from utils.game_logic import ...`, `from agent_executor import ...`)

**Path Aliases:**
- None detected; local imports use plain relative-style module names (packages run from sub-directory root)

## Error Handling

**Patterns:**
- `execute` methods raise bare `Exception` for unsupported operations (e.g., `cancel` in `helloworld/agent_executor.py`: `raise Exception('cancel not supported')`)
- `signing_and_verifying/agent_executor.py` uses `print('Cancel not supported.')` instead of raising — inconsistent across sub-packages
- Caller scripts (`test_client.py`) use `try/except Exception` with `logger.exception(...)` followed by `raise RuntimeError(...) from e` to re-raise with context
- Helper utilities return `None` or `(False, None)` tuples to signal parse failures rather than raising (see `number_guessing_game/utils/helpers.py`)
- `_key_provider` in `signing_and_verifying/test_client.py` raises bare `ValueError` on missing or unknown keys

## Logging

**Framework:** Python stdlib `logging` module; `print()` used alongside it in agent business logic

**Patterns:**
- Test/client scripts configure `logging.basicConfig(level=logging.INFO)` and use `logger = logging.getLogger(__name__)`
- Agent and game logic code uses bare `print()` for debug output: `print(f'[GameLogic] Guess {guess} -> {hint}')`, `print('[GameLogic] Shuffled history...')`
- No structured logging or log level differentiation within agent internals

## Comments

**When to Comment:**
- Module-level docstrings on all files in `number_guessing_game/` (detailed, describes purpose and public API)
- Function docstrings following Google style: Args/Returns sections with type info in prose
- Inline `# ---` separator comments used to delineate logical sections within files
- `# --8<-- [start:X]` / `# --8<-- [end:X]` markers used in `helloworld/` for documentation snippet extraction

**JSDoc/TSDoc:**
- Not applicable (Python project)

## Function Design

**Size:** Functions are small and focused; game logic helpers (`process_guess`, `build_visualisation`) are ~20-40 lines each

**Parameters:** Positional with type annotations; `Optional[str] = None` defaults used in ADK tool functions; `ToolContext` passed as final arg for ADK tools

**Return Values:**
- Async agent `execute` methods always return `None` (results enqueued via `EventQueue`)
- `stream` methods are `AsyncIterable` generators yielding dicts or tuples `(bool, str)`
- Utility functions return typed primitives or `None` on failure

## Module Design

**Exports:**
- `number_guessing_game/utils/game_logic.py` uses explicit `__all__` list: `['build_visualisation', 'is_sorted_history', 'process_guess', 'process_history_payload']`
- Other modules do not define `__all__`

**Barrel Files:**
- `number_guessing_game/utils/__init__.py` present but content not exported — acts as package marker only
- Each sub-package (`helloworld/`, `dice_agent_rest/`, etc.) is a self-contained Python package with its own `pyproject.toml`

## AgentExecutor Pattern

Every agent implementation follows this contract (defined by `a2a-sdk`):
- Subclass `AgentExecutor` from `a2a.server.agent_execution`
- Implement `async def execute(self, context: RequestContext, event_queue: EventQueue) -> None`
- Implement `async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None`
- Results are communicated exclusively via `event_queue.enqueue_event(...)` — never returned
- Files: `helloworld/agent_executor.py`, `adk_expense_reimbursement/agent_executor.py`, `dice_agent_rest/agent_executor.py`, `signing_and_verifying/agent_executor.py`, `number_guessing_game/agent_Alice.py`

---

*Convention analysis: 2026-06-09*
