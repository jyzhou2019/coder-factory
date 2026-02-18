"""
WebSocket Router

Handles real-time updates and notifications
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from typing import Dict, Set, Any
import asyncio
import json
from datetime import datetime

router = APIRouter()


class ConnectionManager:
    """
    WebSocket Connection Manager

    Manages active WebSocket connections and broadcasts
    """

    def __init__(self):
        # session_id -> set of websockets
        self._session_connections: Dict[str, Set[WebSocket]] = {}
        # All active connections
        self._active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, session_id: str = None):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self._active_connections.add(websocket)

        if session_id:
            if session_id not in self._session_connections:
                self._session_connections[session_id] = set()
            self._session_connections[session_id].add(websocket)

        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
        })

    def disconnect(self, websocket: WebSocket, session_id: str = None):
        """Remove a WebSocket connection"""
        self._active_connections.discard(websocket)

        if session_id and session_id in self._session_connections:
            self._session_connections[session_id].discard(websocket)
            if not self._session_connections[session_id]:
                del self._session_connections[session_id]

    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send message to a specific connection"""
        try:
            await websocket.send_json(message)
        except Exception:
            pass  # Connection might be closed

    async def broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast message to all connections for a session"""
        if session_id not in self._session_connections:
            return

        message["timestamp"] = datetime.utcnow().isoformat()

        dead_connections = set()
        for websocket in self._session_connections[session_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.add(websocket)

        # Clean up dead connections
        for ws in dead_connections:
            self.disconnect(ws, session_id)

    async def broadcast_all(self, message: dict):
        """Broadcast message to all connections"""
        message["timestamp"] = datetime.utcnow().isoformat()

        dead_connections = set()
        for websocket in self._active_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.add(websocket)

        # Clean up dead connections
        for ws in dead_connections:
            self.disconnect(ws)

    def get_connection_count(self, session_id: str = None) -> int:
        """Get number of active connections"""
        if session_id:
            return len(self._session_connections.get(session_id, set()))
        return len(self._active_connections)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for session-specific updates

    Receives and sends updates about:
        - Dialog progress
        - Task status changes
        - Code generation progress
        - Deployment status
    """
    await manager.connect(websocket, session_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await _handle_message(websocket, session_id, message)
            except json.JSONDecodeError:
                await manager.send_personal({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)


@router.websocket("/global")
async def websocket_global(websocket: WebSocket):
    """
    Global WebSocket endpoint for system-wide updates

    Receives:
        - New session notifications
        - System status updates
        - Task queue updates
    """
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                # Handle global messages (mostly ping/pong)
                if message.get("type") == "ping":
                    await manager.send_personal({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def _handle_message(websocket: WebSocket, session_id: str, message: dict):
    """Handle incoming WebSocket message"""
    msg_type = message.get("type")

    if msg_type == "ping":
        await manager.send_personal({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

    elif msg_type == "subscribe":
        # Client wants to subscribe to specific events
        events = message.get("events", [])
        await manager.send_personal({
            "type": "subscribed",
            "events": events,
            "session_id": session_id
        }, websocket)

    elif msg_type == "get_status":
        # Client requests current status
        await manager.send_personal({
            "type": "status",
            "session_id": session_id,
            "connection_count": manager.get_connection_count(session_id)
        }, websocket)

    else:
        # Unknown message type
        await manager.send_personal({
            "type": "error",
            "message": f"Unknown message type: {msg_type}"
        }, websocket)


# Helper functions for other parts of the application

async def notify_dialog_update(session_id: str, state: str, data: dict = None):
    """Notify clients about dialog state changes"""
    await manager.broadcast_to_session(session_id, {
        "type": "dialog_update",
        "session_id": session_id,
        "state": state,
        "data": data or {}
    })


async def notify_task_update(session_id: str, task_id: str, status: str, progress: int = None):
    """Notify clients about task status changes"""
    message = {
        "type": "task_update",
        "session_id": session_id,
        "task_id": task_id,
        "status": status,
    }
    if progress is not None:
        message["progress"] = progress

    await manager.broadcast_to_session(session_id, message)


async def notify_codegen_progress(session_id: str, progress: int, message: str):
    """Notify clients about code generation progress"""
    await manager.broadcast_to_session(session_id, {
        "type": "codegen_progress",
        "session_id": session_id,
        "progress": progress,
        "message": message
    })


async def notify_deployment_status(
    session_id: str,
    deployment_id: str,
    status: str,
    message: str = None
):
    """Notify clients about deployment status changes"""
    await manager.broadcast_to_session(session_id, {
        "type": "deployment_status",
        "session_id": session_id,
        "deployment_id": deployment_id,
        "status": status,
        "message": message
    })


async def broadcast_system_message(message: str, level: str = "info"):
    """Broadcast a system message to all connections"""
    await manager.broadcast_all({
        "type": "system",
        "level": level,
        "message": message
    })
