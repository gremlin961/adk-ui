import os
import json
import asyncio
import logging

from pathlib import Path
from typing import Dict # For type hinting active_websockets

from google.genai.types import (
    Part,
    Content,
)

from google.adk.runners import Runner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
from starlette.websockets import WebSocketState
# --- Agent Imports for the Google ADK ---
from chat_agent.agent import root_agent # Using the agent from chat_agent
# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


APP_NAME = "ADK Chat App" # Updated App Name
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()

# Global store for active websockets, mapping session_id to WebSocket object
active_websockets: Dict[str, WebSocket] = {}

async def start_agent_session(session_id: str): # Changed to async def
    """Starts an ADK agent session."""
    logger.info(f"[{session_id}] Attempting to start agent session.")
    session = await session_service.create_session( # Added await
        app_name=APP_NAME,
        user_id=session_id,
        session_id=session_id,
    )
    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
        artifact_service=artifact_service,
    )
    run_config = RunConfig(response_modalities=["TEXT"])
    live_request_queue = LiveRequestQueue()
    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    logger.info(f"[{session_id}] Agent session started. Live events queue created.")
    return live_events, live_request_queue

async def agent_to_client_messaging(websocket: WebSocket, live_events, session_id: str):
    """Handles messages from ADK agent to the WebSocket client."""
    async for event in live_events:
        message_to_send = None
        server_log_detail = None
        if event.turn_complete:
            server_log_detail = "Agent turn complete."
            message_to_send = {"type": "agent_turn_complete", "turn_complete": True}
        elif event.interrupted:
            server_log_detail = "Agent turn interrupted."
            message_to_send = {"type": "agent_interrupted", "interrupted": True}
        else:
            part: Part = (event.content and event.content.parts and event.content.parts[0])
            if part and part.text:
                text = part.text
                message_to_send = {"type": "agent_message", "message": text}

        if server_log_detail:
            logger.info(f"[{session_id}] AGENT->CLIENT_TASK: {server_log_detail}")
            # Removed call to send_server_log_to_client

        if message_to_send:
            await websocket.send_text(json.dumps(message_to_send))
    logger.info(f"[{session_id}] Live events stream from agent finished.")
    logger.info(f"[{session_id}] Agent-to-client messaging task finished.")

async def client_to_agent_messaging(websocket: WebSocket, live_request_queue: LiveRequestQueue, session_id: str):
    """Handles messages from WebSocket client to the ADK agent."""
    try:
        while True:
            text = await websocket.receive_text()
            logger.info(f"[{session_id}] CLIENT->AGENT_TASK: Received text: '{text}'")
            content = Content(role="user", parts=[Part.from_text(text=text)])
            live_request_queue.send_content(content=content)
    except WebSocketDisconnect:
        logger.info(f"[{session_id}] WebSocket disconnected by client.")
    except asyncio.CancelledError:
        logger.info(f"[{session_id}] Client-to-agent messaging task cancelled.")
    finally:
        if live_request_queue: # Ensure queue is closed if it exists
            live_request_queue.close()
        logger.info(f"[{session_id}] Client-to-agent messaging task finished.")

app = FastAPI(title=APP_NAME, version="0.1.0")

origins = ["*",]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    logger.info(f"Static files mounted from {STATIC_DIR}")
else:
    logger.error(f"Static directory or index.html not found at {STATIC_DIR}. Frontend may not load.")

@app.get("/")
async def root_path():
    index_html_path = STATIC_DIR / "index.html"
    if index_html_path.is_file():
        return FileResponse(index_html_path)
    logger.error(f"index.html not found at {index_html_path}")
    return {"error": "index.html not found"}, 404

@app.websocket("/ws/{session_id_from_path}")
async def websocket_endpoint(websocket: WebSocket, session_id_from_path: str):
    session_id = session_id_from_path
    await websocket.accept()
    active_websockets[session_id] = websocket
    logger.info(f"[{session_id}] Client connected. Added to active list for status broadcasts.")
    # Removed call to send_server_log_to_client

    live_events = None
    live_request_queue = None
    agent_to_client_task = None
    client_to_agent_task = None

    try:
        logger.info(f"[{session_id}] Initializing agent session backend.")
        live_events, live_request_queue = await start_agent_session(session_id)

        agent_to_client_task = asyncio.create_task(
            agent_to_client_messaging(websocket, live_events, session_id),
            name=f"agent_to_client_{session_id}"
        )
        client_to_agent_task = asyncio.create_task(
            client_to_agent_messaging(websocket, live_request_queue, session_id),
            name=f"client_to_agent_{session_id}"
        )
        
        done, pending = await asyncio.wait(
            {agent_to_client_task, client_to_agent_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in done:
            if task.exception() and not isinstance(task.exception(), (WebSocketDisconnect, asyncio.CancelledError)):
                 logger.warning(f"[{session_id}] Task {task.get_name()} encountered an exception: {task.exception()}")
            else:
                 logger.info(f"[{session_id}] Task {task.get_name()} completed.")
    finally:
        logger.info(f"[{session_id}] Client disconnecting / cleaning up tasks...")
        removed_ws = active_websockets.pop(session_id, None)
        if removed_ws: logger.info(f"[{session_id}] WebSocket removed from active list.")

        # Simpler task cancellation
        all_tasks = []
        if agent_to_client_task: all_tasks.append(agent_to_client_task)
        if client_to_agent_task: all_tasks.append(client_to_agent_task)
        if 'pending' in locals() and pending: all_tasks.extend(list(pending))
        
        for task in all_tasks:
            if task and not task.done():
                logger.info(f"[{session_id}] Cancelling task: {task.get_name()}")
                task.cancel()
                # No need to await cancellation for simplicity in this example

        if live_request_queue:
            logger.info(f"[{session_id}] Closing ADK live_request_queue.")
            live_request_queue.close() # Simplified: no try-except
        
        if websocket.client_state == WebSocketState.CONNECTED:
            logger.info(f"[{session_id}] Server explicitly closing WebSocket.")
            await websocket.close(code=1000) # Simplified: no try-except
        logger.info(f"[{session_id}] Client cleanup finished.")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Uvicorn server on http://0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, app_dir=str(Path(__file__).parent))
