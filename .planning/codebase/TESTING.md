# Testing Patterns

**Analysis Date:** 2026-06-09

## Test Framework

**Runner:**
- No automated test framework detected (no `pytest`, `unittest`, `pytest.ini`, `conftest.py`, or `setup.cfg` with test configuration found in any sub-package)
- No `pyproject.toml` contains a `[tool.pytest]` or `[tool.pytest.ini_options]` section

**Assertion Library:**
- Not applicable — no test suite exists

**Run Commands:**
- Not applicable — no test runner configured

## Test File Organization

**Location:**
- Two manual integration/smoke-test client scripts exist:
  - `helloworld/test_client.py` — manual client that connects to a running helloworld server and exercises both streaming and non-streaming calls
  - `signing_and_verifying/test_client.py` — manual client that fetches a signed agent card and verifies the JWK signature

**Naming:**
- Named `test_client.py` but these are runnable scripts (`if __name__ == '__main__': asyncio.run(main())`), not test functions discovered by pytest

**Structure:**
- Single `async def main()` function per file, run directly via `asyncio.run(main())`
- No `describe`/`it` or `class Test*` structure

## Test Structure

**Suite Organization:**
- Not applicable — no test suite

**Patterns:**
- Manual integration testing via live HTTP calls against a locally running agent server
- `helloworld/test_client.py` exercises: public agent card fetch, non-streaming `message/send`, streaming `message/send`, extended card fetch
- `signing_and_verifying/test_client.py` exercises: public card fetch with signature verification, extended card fetch with JWK signature verification, non-streaming `message/send`

**Example pattern from `helloworld/test_client.py`:**
```python
async def main() -> None:
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        try:
            _public_card = await resolver.get_agent_card()
        except Exception as e:
            logger.exception('Critical error fetching public agent card.')
            raise RuntimeError('Failed to fetch the public agent card.') from e

        client = client_factory.create(_public_card)
        response = client.send_message(request)
        async for chunk in response:
            task, _ = chunk
            print(task)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

## Mocking

**Framework:** Not applicable — no mocking library in use

**Patterns:**
- No mocking detected in any file
- Tests rely on real live services (actual HTTP server must be running before `test_client.py` scripts work)

**What to Mock:**
- Not established — no convention exists

**What NOT to Mock:**
- Not established — no convention exists

## Fixtures and Factories

**Test Data:**
- Hardcoded inline in client scripts: `base_url = 'http://localhost:9999'`, fixed `Part(text='Say hello.')` message
- No shared fixture files or factory helpers

**Location:**
- No separate fixtures directory

## Coverage

**Requirements:** None enforced — no coverage tooling configured in any `pyproject.toml`

**View Coverage:**
- Not applicable

## Test Types

**Unit Tests:**
- None present

**Integration Tests:**
- Manual integration scripts only: `helloworld/test_client.py`, `signing_and_verifying/test_client.py`
- Must be run manually against a live server process

**E2E Tests:**
- Not formally present; the manual client scripts serve as informal end-to-end smoke tests

## Common Patterns

**Async Testing:**
- All client scripts use `asyncio.run(main())` entry point pattern — not compatible with pytest-asyncio without modification

**Error Testing:**
- Not present in test scripts; errors surface as exceptions printed to console

## Gap Summary

This repository has no automated test suite. All verification is done through manual execution of integration client scripts that require a running server. Adding automated tests would require:

1. Choosing a test framework (pytest + pytest-asyncio recommended given async-heavy codebase)
2. Adding unit tests for pure logic in `number_guessing_game/utils/game_logic.py` and `number_guessing_game/utils/helpers.py` (these are already transport-agnostic and easy to test in isolation)
3. Converting `helloworld/test_client.py` and `signing_and_verifying/test_client.py` into proper pytest integration tests with a server fixture

---

*Testing analysis: 2026-06-09*
