"""
Run AgentAlice directly on the host at port 10002 (matches Docker external mapping).

  docker stop cinatra-a2a-peer-number-alice-1
  cd dev/a2a-peers/number_guessing_game && uv run run_host_alice.py
"""
import uvicorn
from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import AgentCard
from agent_Alice import NumberGuessExecutor, alice_card_dict

HOST_PORT = 10002

card_dict = dict(alice_card_dict)
card_dict["url"] = f"http://localhost:{HOST_PORT}/a2a/v1"
agent_card = AgentCard.model_validate(card_dict)

handler = DefaultRequestHandler(NumberGuessExecutor(), InMemoryTaskStore())
app = A2AStarletteApplication(agent_card=agent_card, http_handler=handler, enable_v0_3_compat=True).build(rpc_url="/a2a/v1")

if __name__ == "__main__":
    print(f"AgentAlice listening on http://127.0.0.1:{HOST_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=HOST_PORT)
