# a2a-servers-dev

Development-only fixtures: a small fleet of sample [A2A](https://a2aproject.github.io/A2A/)
(Agent-to-Agent) peer servers that Cinatra's local dev stack uses to exercise its
A2A connector (agent discovery, task send, streaming, signed agent cards).

> **Not for production.** These are throwaway sample agents for local testing only.
> This repository is not a published package and is not consumed at runtime by the
> Cinatra app — only by `cinatra setup` in development.

## Purpose

Cinatra's A2A connector lets users register and invoke external agents. To develop and
test that connector locally — without standing up real third-party agents — this repo
ships a curated set of sample A2A servers that cover the protocol surface Cinatra
exercises: basic message exchange, streaming, LLM-backed tasks, and signed agent cards.

Each agent is a self-contained Python service. Six peer servers run across six distinct
host ports. The number-guessing sample also includes Bob, a CLI client used by the demo,
but Bob is not exposed as an A2A HTTP server and is excluded from Cinatra's active
`a2a-peers` docker-compose profile:

| Agent | What it demonstrates |
|-------|----------------------|
| `helloworld` | Minimal A2A server: message/send, streaming, extended agent card |
| `number_guessing_game` (Alice) | Multi-agent cooperation; stateful task exchange (no LLM) |
| `number_guessing_game` (Carol) | Visualiser/shuffler role; multi-turn task references |
| `dice_agent_rest` | LLM-backed REST agent (Google Gemini / `GOOGLE_API_KEY`) |
| `signing_and_verifying` | AgentCard signing and signature verification |
| `adk_expense_reimbursement` | Google ADK agent with webform-based multi-turn interaction (`GEMINI_API_KEY`) |

The agent source under each `<agent>/` directory is vendored from the upstream
[a2aproject/a2a-samples](https://github.com/a2aproject/a2a-samples) repository
(`samples/python/agents/`), pinned at commit
`df18eeda23e63b6deddf6f41f8f2bebd4aa48e08`. Cinatra-authored additions are the
per-agent `Dockerfile`s, the `run_host*.py` host launchers, and
`number_guessing_game/pyproject.toml`.

## How Cinatra uses this repo

The Cinatra monorepo declares this repo in `package.json` under `cinatra.devApps`.
`cinatra setup {dev,branch,clone}` clones it into the (git-ignored) `dev/a2a-peers/`
directory of the working tree — exactly like the WordPress plugin and Drupal module
dev clones. The `docker-compose.yml` `a2a-peers` profile builds one container per
agent from `./dev/a2a-peers/<agent>`.

Point the clone at a fork or an alternate URL with the
`CINATRA_A2A_SERVERS_DEV_REPO_URL` environment variable (HTTPS or SSH).

## The peers

| Agent | Host port | Notes |
|-------|-----------|-------|
| `helloworld` | 10001 | docker-compose service `a2a-peer-helloworld` (maps container :9999 → 10001) |
| `number_guessing_game` (Alice) | 10002 | `a2a-peer-number-alice`; host launcher `run_host_alice.py` |
| `number_guessing_game` (Bob) | — | `a2a-peer-number-bob`; CLI client, no A2A HTTP endpoint → `a2a-peers-disabled` profile, port 10003 unmapped |
| `number_guessing_game` (Carol) | 10004 | `a2a-peer-number-carol`; host launcher `run_host_carol.py` |
| `dice_agent_rest` | 10005 | `a2a-peer-dice-rest`; needs `GOOGLE_API_KEY` (LLM-backed) |
| `signing_and_verifying` | 10006 | `a2a-peer-signing`; host launcher `run_host.py` |
| `adk_expense_reimbursement` | 10007 | `a2a-peer-adk-reimbursement`; needs `GEMINI_API_KEY` (LLM-backed) |

The two LLM-backed peers need a Google/Gemini API key: `dice_agent_rest` checks
`GOOGLE_API_KEY` (or `GOOGLE_GENAI_USE_VERTEXAI=TRUE`), `adk_expense_reimbursement`
checks `GEMINI_API_KEY`. Under docker-compose the key is forwarded as
`GEMINI_API_KEY` with a `GOOGLE_API_KEY` fallback; Cinatra syncs it from
**Settings → APIs → Gemini** into `.env`. Set **both** env vars to the same key if
you run dice and adk together.

## Running the peers

The reference path is docker-compose — it brings up all six active peers on the
ports above:

```bash
docker compose --profile a2a-peers up -d --build
```

On macOS, Docker Desktop's proxy can cause `ECONNRESET` for Node.js SSE streaming
clients. To work around that, the peers that benefit from host-run ship a launcher
you can run directly (after `cinatra setup dev` has cloned them):

```bash
cd dev/a2a-peers/number_guessing_game  && uv run run_host_alice.py      # 10002
cd dev/a2a-peers/number_guessing_game  && uv run run_host_carol.py      # 10004
cd dev/a2a-peers/dice_agent_rest       && uv run . --host 127.0.0.1 --port 10005
cd dev/a2a-peers/signing_and_verifying && uv run run_host.py            # 10006
cd dev/a2a-peers/adk_expense_reimbursement && source .env && uv run . --host 127.0.0.1 --port 10007
```

`helloworld` has no host launcher (its `__main__.py` binds `:9999`); use the
docker-compose service for the `:10001` mapping, or run `uv run .` and point at
`:9999`.

Then add the peer URLs to `.env.local` so the dev server auto-registers them:

```
CINATRA_A2A_DEV_PEER_URLS=http://localhost:10001,http://localhost:10002,http://localhost:10004,http://localhost:10005,http://localhost:10006,http://localhost:10007
```

Restart the dev server — peers auto-import within ~10s and appear under `/agents/run`.

## Provenance & license

The agent source under each `<agent>/` directory is vendored from the upstream
[a2aproject/a2a-samples](https://github.com/a2aproject/a2a-samples) repository
(`samples/python/agents/`), pinned at commit
`df18eeda23e63b6deddf6f41f8f2bebd4aa48e08`, and is licensed under Apache-2.0.

Cinatra-authored additions (the per-agent `Dockerfile`s, the `run_host*.py` host
launchers, and `number_guessing_game/pyproject.toml`) are also licensed under
Apache-2.0.

See [`LICENSE`](./LICENSE) for the full license text and [`NOTICE`](./NOTICE) for
attribution.
