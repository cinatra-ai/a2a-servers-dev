"""
Run AgentCarol directly on the host at port 10004 (matches Docker external mapping).

  docker stop cinatra-a2a-peer-number-carol-1
  cd dev/a2a-peers/number_guessing_game && uv run run_host_carol.py
"""
import uvicorn
from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from agent_Carol import HistoryHelperExecutor, carol_card

HOST_PORT = 10004

# carol_card is already a validated AgentCard; override only its advertised URL
# so it points at the host port (mirrors run_host_alice.py).
agent_card = carol_card.model_copy(update={"url": f"http://localhost:{HOST_PORT}/a2a/v1"})

handler = DefaultRequestHandler(HistoryHelperExecutor(), InMemoryTaskStore())
app = A2AStarletteApplication(agent_card=agent_card, http_handler=handler, enable_v0_3_compat=True).build(rpc_url="/a2a/v1")

if __name__ == "__main__":
    print(f"AgentCarol listening on http://127.0.0.1:{HOST_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=HOST_PORT)
