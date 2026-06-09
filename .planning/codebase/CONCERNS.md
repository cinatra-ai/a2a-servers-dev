# Codebase Concerns

**Analysis Date:** 2026-06-09

## Tech Debt

**Module-level mutable global state in game_logic:**
- Issue: `_target_number`, `_attempts`, and `_secret_logged` are module-level globals in `number_guessing_game/utils/game_logic.py` (lines 29-31). The target number is picked once at import time via `random.randint(1, 100)`. If the game is restarted within the same process, or if the module is imported multiple times across threads, state leaks between sessions.
- Files: `number_guessing_game/utils/game_logic.py`
- Impact: No way to reset a game without restarting the process. Multi-instance or concurrent use would produce inconsistent results.
- Fix approach: Encapsulate game state in a `GameSession` class; instantiate per request context.

**Global `_client_factory` singleton in protocol_wrappers:**
- Issue: `_client_factory = ClientFactory(ClientConfig())` is a module-level singleton in `number_guessing_game/utils/protocol_wrappers.py` (line 31), shared across all invocations.
- Files: `number_guessing_game/utils/protocol_wrappers.py`
- Impact: Cannot configure different client settings per call; not safe if `ClientFactory` maintains per-session state.
- Fix approach: Accept an optional `ClientFactory` parameter or create per-call.

**`HistoryHelperExecutor` instance state is not isolated per task:**
- Issue: `HistoryHelperExecutor._last_history` is stored on the executor instance in `number_guessing_game/agent_Carol.py` (line 89). The executor is a single shared instance (instantiated once in `__main__`). Concurrent requests would corrupt each other's shuffle history.
- Files: `number_guessing_game/agent_Carol.py`
- Impact: Race conditions when multiple clients use AgentCarol simultaneously.
- Fix approach: Store per-task state in a dict keyed by `task_id`, or rely on a task store.

**`request_ids` is a module-level set in the expense agent:**
- Issue: `request_ids = set()` is module-global in `adk_expense_reimbursement/agent.py` (line 21). Request IDs are never expired; the set grows unboundedly in a long-running server.
- Files: `adk_expense_reimbursement/agent.py`
- Impact: Memory leak for long-running deployments; also not safe across multiple worker processes.
- Fix approach: Use a persistent data store (e.g., database or Redis) for request ID validation.

**Hardcoded localhost URLs and ports in server entrypoints:**
- Issue: `helloworld/__main__.py` and `signing_and_verifying/__main__.py` hardcode `http://localhost:9999` in `AgentCard` fields (`icon_url`, `url`, `jku`). These are not configurable via CLI flags or environment variables.
- Files: `helloworld/__main__.py`, `signing_and_verifying/__main__.py`
- Impact: Agent cards advertise wrong URLs if deployed anywhere other than localhost on port 9999; breaks inter-agent discovery.
- Fix approach: Derive the public URL from CLI `--host`/`--port` arguments (as `adk_expense_reimbursement` and `dice_agent_rest` already do correctly).

**`send_text` event-loop fallback uses deprecated `asyncio.get_event_loop()`:**
- Issue: `send_text` and `cancel_task` in `number_guessing_game/utils/protocol_wrappers.py` (lines 124-135, 192-197) call `asyncio.get_event_loop()` as a fallback when inside a running loop. This pattern is deprecated in Python 3.10+ and raises `DeprecationWarning`; it will error in future Python versions.
- Files: `number_guessing_game/utils/protocol_wrappers.py`
- Impact: Compatibility break on Python ≥ 3.12 in environments with a running event loop (e.g., Jupyter, FastAPI).
- Fix approach: Use `asyncio.get_running_loop()` and schedule as a `Task`, or expose only the async API.

## Known Bugs

**Negotiation loop exit does not guarantee task is in `completed` state:**
- Symptoms: In `agent_Bob.py` `_negotiate_sorted_history`, when the history is sorted, a "Well done!" follow-up is sent and the `while` loop breaks. The returned `resp_task` from the `send_followup` call is not checked; the code discards it (line 106). Carol's `_handle_followup` completes the task on "Well done", but Bob has no confirmation.
- Files: `number_guessing_game/agent_Bob.py`
- Trigger: Normal operation — the bug is silent but means Bob cannot detect a failure on the Carol side at game end.
- Workaround: None; the game proceeds regardless.

**`MAX_NEGOTIATION_ATTEMPTS = 400` is extremely high for a random shuffle:**
- Symptoms: A list of n items has n! permutations; the probability of hitting sorted order by random shuffle is 1/n!. For a history of 10+ guesses the expected number of shuffles before sorted order is enormous. The cap of 400 means the task is typically cancelled without success.
- Files: `number_guessing_game/agent_Bob.py` (line 35)
- Trigger: Playing the game for more than a few guesses.
- Workaround: The game still functions, but the multi-turn shuffle negotiation rarely terminates successfully.

## Security Considerations

**Ephemeral key pair for signing_and_verifying — no persistent identity:**
- Risk: `signing_and_verifying/__main__.py` generates a fresh EC key pair on every process start (line 27). There is no mechanism to load a pre-existing private key.
- Files: `signing_and_verifying/__main__.py`
- Current mitigation: `public_keys.json` is written to disk and gitignored; the key is used only for the demo.
- Recommendations: For any non-demo use, load the private key from a secrets manager or environment variable; do not generate ephemeral keys in production.

**`public_keys.json` served as a static file with no caching headers:**
- Risk: `signing_and_verifying/__main__.py` appends a `FileResponse` route for `public_keys.json` (line 125). If the file is missing (e.g., first request before the key is written), Starlette returns a 404 or an unhandled error.
- Files: `signing_and_verifying/__main__.py`
- Current mitigation: File is written before the server starts in the same `__main__` block.
- Recommendations: Serve the public key from memory rather than reading a file off disk; add error handling for missing file.

**No authentication on A2A endpoints:**
- Risk: All agents (`helloworld`, `dice_agent_rest`, `number_guessing_game`, `adk_expense_reimbursement`) bind to `0.0.0.0` and expose unauthenticated endpoints. Any process on the network can send tasks.
- Files: `helloworld/__main__.py`, `dice_agent_rest/__main__.py`, `number_guessing_game/utils/server.py`, `adk_expense_reimbursement/__main__.py`
- Current mitigation: These are explicitly demo/sample projects; `signing_and_verifying` demonstrates the signing pattern but does not enforce bearer-token or mTLS authentication on the server side.
- Recommendations: Add middleware for API key or JWT validation before shipping outside localhost.

**GEMINI_API_KEY / GOOGLE_API_KEY validated only at startup:**
- Risk: If the environment variable is set but the value is invalid (empty string, revoked key), the server starts successfully and only fails at runtime when the LLM is invoked.
- Files: `adk_expense_reimbursement/__main__.py`, `dice_agent_rest/__main__.py`
- Current mitigation: Startup check rejects missing variable; `.env` file support via `python-dotenv`.
- Recommendations: Validate key format at startup (non-empty string check at minimum).

## Performance Bottlenecks

**Synchronous `asyncio.run()` wrapper in hot path:**
- Problem: Every call to `send_text` or `cancel_task` in `number_guessing_game` spawns a new event loop via `asyncio.run()`. During a game, `play_game()` calls these synchronously in a loop, creating and tearing down an event loop for every guess and every shuffle attempt.
- Files: `number_guessing_game/utils/protocol_wrappers.py`
- Cause: The number-guessing agent CLI (`agent_Bob.py`) is purely synchronous; wrappers bridge to async SDK.
- Improvement path: Rewrite `agent_Bob.py` as a top-level `async def main()` and keep a single running event loop for the session lifetime.

**InMemoryTaskStore used in all server agents:**
- Problem: All A2A server agents use `InMemoryTaskStore` with no eviction policy. Long-running deployments accumulate all tasks in memory.
- Files: `helloworld/__main__.py`, `signing_and_verifying/__main__.py`, `adk_expense_reimbursement/__main__.py`, `dice_agent_rest/__main__.py`
- Cause: Intentional for demo simplicity.
- Improvement path: Use a persistent or TTL-based task store for production.

## Fragile Areas

**`extract_text` relies on undocumented internal `part.root.text` attribute:**
- Files: `number_guessing_game/utils/protocol_wrappers.py` (lines 215-217)
- Why fragile: The code uses `hasattr(part, 'root') and hasattr(part.root, 'text')` to navigate the SDK's internal discriminated-union structure. If the SDK changes its internal `Part` representation, this silently returns `''`.
- Safe modification: Pin the a2a-sdk version in all `pyproject.toml` files and add integration tests for text extraction.
- Test coverage: No tests cover this path.

**`process_history_payload` silent fallback to empty visualisation:**
- Files: `number_guessing_game/utils/game_logic.py` (lines 132-170)
- Why fragile: Any JSON input that is not a dict with `action=shuffle` and not a plain list returns `build_visualisation([])` with no error signal. Callers cannot distinguish between "no guesses yet" and "bad input".
- Safe modification: Return a structured result or raise; do not silently swallow unexpected payloads.
- Test coverage: No automated tests exist in the repository.

**`HistoryHelperExecutor._handle_followup` falls through to shuffle on any non-"well done" text:**
- Files: `number_guessing_game/agent_Carol.py` (lines 95-123)
- Why fragile: Any unexpected message causes Carol to shuffle again and stay in `input_required`, potentially looping indefinitely if the peer sends unexpected data.
- Safe modification: Add explicit pattern matching with an error/cancel path for unrecognised follow-up text.
- Test coverage: No automated tests exist.

## Scaling Limits

**Single-process, no horizontal scaling:**
- Current capacity: Each agent is a single uvicorn process with no worker configuration.
- Limit: Cannot scale beyond one CPU core without additional infrastructure; `InMemoryTaskStore` and module-level globals make multi-process deployment incorrect (state is not shared).
- Scaling path: Replace `InMemoryTaskStore` and global state with an external store; use uvicorn with `--workers` or deploy behind a load balancer only after fixing shared state.

## Dependencies at Risk

**`google-adk` (ADK) dependency pinned only in `adk_expense_reimbursement`:**
- Risk: `adk_expense_reimbursement/pyproject.toml` depends on `google-adk` but the version constraint is not visible from the repo (requires reading pyproject.toml). The ADK is rapidly evolving; breaking changes between minor versions are common.
- Impact: Agent startup failures or behavior changes on dependency update.
- Migration plan: Pin to a specific minor version and test upgrades explicitly.

**`asyncio.get_event_loop()` usage deprecated since Python 3.10:**
- Risk: Python 3.12+ emits `DeprecationWarning`; 3.14 will likely remove the fallback behavior.
- Impact: `send_text` and `cancel_task` break in Jupyter or any environment with a running loop on Python 3.12+.
- Migration plan: Replace with `asyncio.get_running_loop()` pattern (see tech debt section).

## Missing Critical Features

**No automated tests anywhere in the repository:**
- Problem: There are no `pytest`, `unittest`, or any other automated test files. `helloworld/test_client.py` and `signing_and_verifying/test_client.py` are manual integration scripts (require a live server), not automated tests. No `pytest.ini`, `conftest.py`, or test discovery configuration exists.
- Blocks: CI/CD validation, regression detection, safe refactoring.

**No Docker Compose or orchestration for multi-agent demos:**
- Problem: The `number_guessing_game` demo requires three separate agents (Alice, Bob, Carol) started in the correct order on specific ports. There is no `docker-compose.yml` or script to start all three together.
- Blocks: Easy onboarding; demo reliability.

**No input validation on A2A message text:**
- Problem: Agents parse raw text from incoming A2A messages with minimal validation. `process_guess` in `game_logic.py` handles invalid integers gracefully, but most agents pass raw text directly to downstream logic or LLMs without sanitizing.
- Blocks: Prompt injection defense for LLM-backed agents (`adk_expense_reimbursement`).

## Test Coverage Gaps

**All agent execution paths are untested:**
- What's not tested: `AgentExecutor.execute()` and `AgentExecutor.cancel()` implementations in every agent.
- Files: `helloworld/agent_executor.py`, `dice_agent_rest/agent_executor.py`, `adk_expense_reimbursement/agent_executor.py`, `signing_and_verifying/agent_executor.py`, `number_guessing_game/agent_Carol.py`, `number_guessing_game/agent_Alice.py`
- Risk: Regressions in A2A protocol handling go undetected.
- Priority: High

**Game logic utilities are untested:**
- What's not tested: `process_guess`, `build_visualisation`, `is_sorted_history`, `process_history_payload` in `number_guessing_game/utils/game_logic.py`; `parse_int_in_range`, `try_parse_json` in `number_guessing_game/utils/helpers.py`.
- Files: `number_guessing_game/utils/game_logic.py`, `number_guessing_game/utils/helpers.py`
- Risk: Subtle edge cases (empty input, out-of-range values, malformed JSON) are uncaught.
- Priority: Medium

**`extract_text` utility is untested:**
- What's not tested: The `extract_text` function in `number_guessing_game/utils/protocol_wrappers.py` that navigates SDK internals.
- Files: `number_guessing_game/utils/protocol_wrappers.py`
- Risk: Silent empty-string returns when SDK structure changes.
- Priority: Medium

---

*Concerns audit: 2026-06-09*
