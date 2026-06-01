"""
Run signing_and_verifying A2A peer directly on the host at port 10006.

Bypasses Docker Desktop macOS ECONNRESET for Node.js SSE streaming clients.
  docker stop cinatra-a2a-peer-signing-1
  cd dev/a2a-peers/signing_and_verifying && uv run run_host.py
"""
import json
from pathlib import Path
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.signing import create_agent_card_signer
from agent_executor import SignedAgentExecutor
from cryptography.hazmat.primitives import asymmetric, serialization
from starlette.responses import FileResponse
from starlette.routing import Route

HOST_PORT = 10006

private_key = asymmetric.ec.generate_private_key(asymmetric.ec.SECP256R1())
public_key = private_key.public_key()
pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode("utf-8")
kid = "my-key"
with Path("public_keys.json").open("w") as f:
    json.dump({kid: pem}, f, indent=2)

skill = AgentSkill(id="reminder", name="Verification Reminder", description="Reminds the user to verify the Agent Card.", tags=["verify me"], examples=["Verify me!"])
public_agent_card = AgentCard(
    name="Signed Agent", description="An Agent that is signed", version="1.0.0",
    default_input_modes=["text"], default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True, extended_agent_card=False),
    supported_interfaces=[AgentInterface(protocol_binding="JSONRPC", url=f"http://localhost:{HOST_PORT}")],
    skills=[skill],
)
request_handler = DefaultRequestHandler(agent_executor=SignedAgentExecutor(), task_store=InMemoryTaskStore())
signer = create_agent_card_signer(signing_key=private_key, protected_header={"kid": kid, "alg": "ES256", "jku": f"http://localhost:{HOST_PORT}/public_keys.json"})
server = A2AStarletteApplication(agent_card=public_agent_card, http_handler=request_handler, card_modifier=signer, enable_v0_3_compat=True)
app = server.build()
app.routes.append(Route("/public_keys.json", endpoint=FileResponse("public_keys.json"), methods=["GET"]))

if __name__ == "__main__":
    print(f"Starting Signed Agent on http://127.0.0.1:{HOST_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=HOST_PORT)
