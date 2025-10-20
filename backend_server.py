#!/usr/bin/env python3
"""
FastAPI Backend Server for GST Grievance Resolution System
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Import the GST resolution system
try:
    from src.workflows.gst_workflow import GSTGrievanceResolver, process_gst_grievance
    from src.utils.embeddings import initialize_all
except ImportError:
    # If running from different directory
    import sys
    sys.path.append('.')
    from src.workflows.gst_workflow import GSTGrievanceResolver, process_gst_grievance
    from src.utils.embeddings import initialize_all

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GST Grievance Resolution API",
    description="API for GST Grievance Resolution Multi-Agent System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
resolver: Optional[GSTGrievanceResolver] = None
active_sessions: Dict[str, Dict[str, Any]] = {}
websocket_connections: Dict[str, WebSocket] = {}
agent_progress: Dict[str, Dict[str, Any]] = {}  # New: Track agent progress per session
pending_websocket_messages: Dict[str, List[dict]] = {}
event_loop: Optional[asyncio.AbstractEventLoop] = None

def get_pending_queue(session_id: str) -> List[dict]:
    """Return the pending message queue for a session."""
    return pending_websocket_messages.setdefault(session_id, [])

async def flush_websocket_messages(session_id: str):
    """Flush pending WebSocket messages for a session if a connection is available."""
    if session_id not in websocket_connections:
        return

    websocket = websocket_connections[session_id]
    queue = pending_websocket_messages.get(session_id, [])

    while queue:
        message = queue[0]
        try:
            await websocket.send_text(json.dumps(message))
            logger.info(f"📡 Sent WebSocket message to session {session_id}: {message['type']}")
            queue.pop(0)
        except Exception as exc:
            logger.error(f"❌ Failed to send WebSocket message for session {session_id}: {exc}")
            break

    if not queue:
        pending_websocket_messages.pop(session_id, None)

async def enqueue_websocket_message(session_id: str, message: dict):
    """Add a message to the session queue and try to flush immediately."""
    queue = get_pending_queue(session_id)
    queue.append(message)
    logger.debug(f"🌀 Queued WebSocket message for session {session_id}: {message['type']}")
    await flush_websocket_messages(session_id)

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    category: str

class QueryResponse(BaseModel):
    sessionId: str
    status: str
    message: str

class StatusResponse(BaseModel):
    initialized: bool
    agentsReady: bool
    agentCount: int
    lastHealthCheck: str
    errors: List[str]

class HealthResponse(BaseModel):
    status: str
    timestamp: str

# Progress callback for WebSocket and simple storage
def progress_callback(session_id: str, agent_name: str, description: str, progress: float):
    """Synchronous progress callback that schedules async processing."""
    logger.info(f"🔄 Progress update: {agent_name} - {description} ({progress:.1%})")
    agent_progress[session_id] = {
        "current_agent": agent_name,
        "description": description,
        "progress": progress,
        "timestamp": datetime.now().isoformat(),
        "agents_completed": agent_progress.get(session_id, {}).get("agents_completed", [])
    }
    if progress >= 1.0 and agent_name not in agent_progress[session_id]["agents_completed"]:
        agent_progress[session_id]["agents_completed"].append(agent_name)

    message = {
        "type": "agent_status",
        "data": {
            "session_id": session_id,
            "agent_name": agent_name,
            "description": description,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        }
    }

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(enqueue_websocket_message(session_id, message))
        logger.info(f"📡 Scheduled progress update for {agent_name} to session {session_id}")
    except RuntimeError:
        if event_loop:
            asyncio.run_coroutine_threadsafe(enqueue_websocket_message(session_id, message), event_loop)
            logger.info(f"📡 Scheduled cross-thread progress update for {agent_name} to session {session_id}")
        else:
            logger.error("❌ Event loop not initialized; dropping progress update")

async def send_websocket_message(websocket: WebSocket, message: dict):
    """Async function to send WebSocket message"""
    try:
        await websocket.send_text(json.dumps(message))
    except Exception as e:
        logger.error(f"❌ Failed to send WebSocket message: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize the GST resolution system on startup"""
    global resolver
    global event_loop

    try:
        logger.info("🚀 Starting GST Grievance Resolution Server...")
        event_loop = asyncio.get_running_loop()

        # Initialize models
        if not initialize_all():
            logger.error("❌ Failed to initialize system components")
            return

        # Initialize resolver
        resolver = GSTGrievanceResolver()
        logger.info("✅ GST Grievance Resolution System initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize system: {e}")

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/status")
async def get_system_status():
    """Get system status"""
    global resolver

    errors = []
    initialized = resolver is not None
    agents_ready = False
    agent_count = 0

    if resolver:
        try:
            agents_ready = hasattr(resolver, 'app') and resolver.app is not None
            if hasattr(resolver.app, 'graph') and hasattr(resolver.app.graph, 'nodes'):
                agent_count = len(resolver.app.graph.nodes)
        except Exception as e:
            errors.append(f"Error checking agent status: {str(e)}")

    status_data = {
        "initialized": initialized,
        "agentsReady": agents_ready,
        "agentCount": agent_count,
        "lastHealthCheck": datetime.now().isoformat(),
        "errors": errors
    }

    return {
        "success": True,
        "data": status_data
    }

@app.post("/api/query")
async def submit_query(request: QueryRequest):
    """Submit a new query for processing"""
    global resolver

    if not resolver:
        raise HTTPException(status_code=503, detail="System not initialized")

    # Generate session ID
    session_id = str(uuid.uuid4())

    # Store session info
    active_sessions[session_id] = {
        "query": request.query,
        "category": request.category,
        "status": "processing",
        "created_at": datetime.now().isoformat(),
        "result": None
    }

    # Start processing in background
    asyncio.create_task(process_query_background(session_id, request.query, request.category))

    response_data = {
        "sessionId": session_id,
        "status": "processing",
        "message": "Query submitted successfully"
    }

    return {
        "success": True,
        "data": response_data
    }

async def process_query_background(session_id: str, query: str, category: str):
    """Process query in background with progress updates"""
    global resolver

    try:
        logger.info(f"🚀 Starting background processing for session {session_id}")

        # Wait a moment for WebSocket connection to be established
        await asyncio.sleep(1.0)

        # Set up progress callback
        resolver.set_progress_callback(
            lambda agent_name, description, progress: progress_callback(
                session_id, agent_name, description, progress
            )
        )

        # Process the query in a worker thread to avoid blocking the event loop
        result = await asyncio.to_thread(resolver.process_query, query, session_id, category)

        # Store result
        if session_id in active_sessions:
            active_sessions[session_id]["status"] = "completed"
            active_sessions[session_id]["result"] = result
            active_sessions[session_id]["completed_at"] = datetime.now().isoformat()
            if isinstance(result, dict) and "processingTime" in result:
                active_sessions[session_id]["processing_time"] = result.get("processingTime")

        message = {
            "type": "query_result",
            "data": {
                "session_id": session_id,
                "status": "completed",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        }
        await enqueue_websocket_message(session_id, message)

        logger.info(f"✅ Background processing completed for session {session_id}")

    except Exception as e:
        logger.error(f"❌ Error processing query for session {session_id}: {e}")

        # Store error
        if session_id in active_sessions:
            active_sessions[session_id]["status"] = "error"
            active_sessions[session_id]["error"] = str(e)
            active_sessions[session_id]["completed_at"] = datetime.now().isoformat()

        message = {
            "type": "error",
            "data": {
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        }
        await enqueue_websocket_message(session_id, message)

@app.get("/api/query/{session_id}/result")
async def get_query_result(session_id: str):
    """Get the result of a processed query"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]

    if session["status"] == "processing":
        return {
            "success": True,
            "data": {"status": "processing", "message": "Query is being processed"}
        }

    if session["status"] == "error":
        return {
            "success": False,
            "data": {
                "status": "error",
                "error": session.get("error", "Unknown error occurred")
            }
        }

    if session["status"] == "completed" and session["result"]:
        return {
            "success": True,
            "data": {
                "status": "completed",
                "result": session["result"]
            }
        }

    raise HTTPException(status_code=500, detail="Unexpected session state")

@app.get("/api/query/{session_id}/progress")
async def get_query_progress(session_id: str):
    """Get real-time agent progress for a query"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    progress = agent_progress.get(session_id, {})

    # Default progress if not started yet
    if not progress:
        return {
            "success": True,
            "data": {
                "status": "processing",
                "current_agent": "🔍 Agent 1: Preprocessing",
                "description": "Initializing...",
                "progress": 0.1,
                "agents_completed": [],
                "timestamp": datetime.now().isoformat()
            }
        }

    return {
        "success": True,
        "data": {
            "status": session["status"],
            "current_agent": progress.get("current_agent", "Unknown"),
            "description": progress.get("description", "Processing..."),
            "progress": progress.get("progress", 0.0),
            "agents_completed": progress.get("agents_completed", []),
            "timestamp": progress.get("timestamp", datetime.now().isoformat())
        }
    }

@app.post("/api/query/{session_id}/cancel")
async def cancel_query(session_id: str):
    """Cancel a query processing"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]

    if session["status"] == "processing":
        session["status"] = "cancelled"
        session["cancelled_at"] = datetime.now().isoformat()

        # Send cancellation notification via WebSocket
        message = {
            "type": "error",
            "data": {
                "session_id": session_id,
                "error": "Query was cancelled by user",
                "timestamp": datetime.now().isoformat()
            }
        }
        await enqueue_websocket_message(session_id, message)

    return {"status": "success", "message": "Query cancelled"}

@app.get("/api/history")
async def get_query_history():
    """Get query history"""
    history = []

    for session_id, session in active_sessions.items():
        processing_time = session.get("processing_time") or session.get("processingTime")
        history.append({
            "id": session_id,
            "query": session["query"],
            "category": session["category"],
            "status": session["status"],
            "timestamp": session["created_at"],
            "processingTime": processing_time,
            "result": session.get("result")
        })

    # Sort by timestamp descending
    history.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "success": True,
        "data": history
    }

@app.delete("/api/history")
async def clear_history():
    """Clear query history"""
    global active_sessions

    # Close all WebSocket connections
    for session_id in list(websocket_connections.keys()):
        try:
            websocket = websocket_connections[session_id]
            await websocket.close()
        except Exception:
            pass

    active_sessions.clear()
    websocket_connections.clear()
    agent_progress.clear()
    pending_websocket_messages.clear()

    return {"status": "success", "message": "History cleared"}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    logger.info(f"🔌 WebSocket connection established for session {session_id}")

    # Store WebSocket connection
    websocket_connections[session_id] = websocket

    try:
        # Send initial connection message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "data": {
                "session_id": session_id,
                "message": "Connected to GST Grievance Resolution System",
                "timestamp": datetime.now().isoformat()
            }
        }))
        logger.info(f"✅ Sent connection confirmation for session {session_id}")
        await flush_websocket_messages(session_id)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for incoming messages with longer timeout since we send in real-time
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)

                # Handle incoming messages (e.g., ping/pong)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))

            except asyncio.TimeoutError:
                # Send periodic ping to keep connection alive
                try:
                    await websocket.send_text(json.dumps({
                        "type": "ping",
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception:
                    break
                continue

            except WebSocketDisconnect:
                logger.info(f"🔌 WebSocket disconnected for session {session_id}")
                break

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for session {session_id}: {e}")
    finally:
        # Clean up connection
        if session_id in websocket_connections:
            del websocket_connections[session_id]
            logger.info(f"🧹 Cleaned up WebSocket connection for session {session_id}")

if __name__ == "__main__":
    uvicorn.run(
        "backend_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
