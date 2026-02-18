"""
Session Manager Service

Manages active sessions and integrates with the existing engines
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio

from .storage import StorageService
from ...engines.confirmation_flow import ConfirmationFlow
from ...engines.requirement_parser import RequirementParser
from ...core.factory import CoderFactory


class SessionManager:
    """
    Session Manager

    Manages the lifecycle of coding sessions, integrating with:
    - ConfirmationFlow (F002)
    - RequirementParser (F001)
    - CoderFactory (core)
    """

    def __init__(self, storage: StorageService):
        self.storage = storage
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._confirmation_flows: Dict[str, ConfirmationFlow] = {}
        self._factories: Dict[str, CoderFactory] = {}

    async def create_session(self, session_id: Optional[str] = None) -> dict:
        """
        Create a new session

        Args:
            session_id: Optional custom session ID

        Returns:
            dict: Session info
        """
        sid = session_id or str(uuid.uuid4())

        # Create in database
        await self.storage.create_session(sid, status="idle")

        # Create session objects
        self._active_sessions[sid] = {
            "id": sid,
            "status": "idle",
            "created_at": datetime.utcnow(),
            "requirement": None,
        }

        return {
            "session_id": sid,
            "status": "idle",
            "created_at": datetime.utcnow().isoformat(),
        }

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session info"""
        # Check memory first
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]

        # Check database
        db_session = await self.storage.get_session(session_id)
        if db_session:
            return {
                "id": db_session.id,
                "status": db_session.status,
                "created_at": db_session.created_at.isoformat(),
                "updated_at": db_session.updated_at.isoformat(),
            }
        return None

    async def start_requirement_flow(
        self,
        session_id: str,
        requirement: str
    ) -> dict:
        """
        Start requirement parsing and confirmation flow

        Args:
            session_id: Session ID
            requirement: Raw requirement text

        Returns:
            dict: Flow status
        """
        # Update session status
        await self.storage.update_session(session_id, status="parsing")
        self._active_sessions[session_id]["status"] = "parsing"

        # Create confirmation flow
        workspace = f"./workspace/{session_id}"
        flow = ConfirmationFlow(workspace)
        self._confirmation_flows[session_id] = flow

        # Start the flow
        result = flow.start(requirement)

        if result["success"]:
            # Update session
            self._active_sessions[session_id]["status"] = result["state"]
            self._active_sessions[session_id]["requirement"] = result

            await self.storage.update_session(
                session_id,
                status=result["state"],
                requirement_data=result
            )

        return result

    async def get_current_question(self, session_id: str) -> Optional[dict]:
        """Get current question for confirmation flow"""
        flow = self._confirmation_flows.get(session_id)
        if not flow:
            return None

        return flow.get_current_question()

    async def answer_question(self, session_id: str, answer: Any) -> dict:
        """Answer current question"""
        flow = self._confirmation_flows.get(session_id)
        if not flow:
            return {"success": False, "error": "No active confirmation flow"}

        result = flow.answer(answer)

        if result["success"]:
            # Update session state
            self._active_sessions[session_id]["status"] = result["state"]
            await self.storage.update_session(
                session_id,
                status=result["state"],
                requirement_data=result.get("summary", {})
            )

        return result

    async def approve_requirement(self, session_id: str) -> dict:
        """Approve current requirement"""
        flow = self._confirmation_flows.get(session_id)
        if not flow:
            return {"success": False, "error": "No active confirmation flow"}

        result = flow.approve()

        if result["success"]:
            # Create factory for this session
            workspace = f"./workspace/{session_id}"
            factory = CoderFactory(workspace)
            self._factories[session_id] = factory

            # Update session
            self._active_sessions[session_id]["status"] = "approved"
            await self.storage.update_session(
                session_id,
                status="approved",
                requirement_data=result.get("requirement", {})
            )

        return result

    async def modify_requirement(
        self,
        session_id: str,
        field: str,
        value: Any,
        reason: str = ""
    ) -> dict:
        """Modify requirement field"""
        flow = self._confirmation_flows.get(session_id)
        if not flow:
            return {"success": False, "error": "No active confirmation flow"}

        return flow.modify(field, value, reason)

    async def cancel_flow(self, session_id: str, reason: str = "") -> dict:
        """Cancel current flow"""
        flow = self._confirmation_flows.get(session_id)
        if flow:
            result = flow.cancel(reason)
        else:
            result = {"success": True}

        # Update session
        self._active_sessions[session_id]["status"] = "cancelled"
        await self.storage.update_session(session_id, status="cancelled")

        # Cleanup
        if session_id in self._confirmation_flows:
            del self._confirmation_flows[session_id]

        return result

    async def get_flow_status(self, session_id: str) -> dict:
        """Get current flow status"""
        flow = self._confirmation_flows.get(session_id)
        if not flow:
            return {"state": "idle", "error": "No active flow"}

        return flow.get_status()

    async def get_dialog_history(self, session_id: str) -> list:
        """Get dialog history"""
        flow = self._confirmation_flows.get(session_id)
        if not flow:
            return []

        return flow.manager.get_dialog_history()

    # Code generation methods
    async def start_code_generation(self, session_id: str) -> dict:
        """Start code generation for approved requirement"""
        factory = self._factories.get(session_id)
        if not factory:
            return {"success": False, "error": "No approved requirement"}

        self._active_sessions[session_id]["status"] = "generating"
        await self.storage.update_session(session_id, status="generating")

        result = factory.generate_code(confirm=False)

        if result.success:
            self._active_sessions[session_id]["status"] = "generated"
            await self.storage.update_session(session_id, status="generated")
        else:
            self._active_sessions[session_id]["status"] = "error"
            await self.storage.update_session(session_id, status="error")

        return {
            "success": result.success,
            "message": result.message,
            "output_path": result.output_path,
            "error": result.error,
        }

    async def run_tests(self, session_id: str) -> dict:
        """Run tests for generated code"""
        factory = self._factories.get(session_id)
        if not factory:
            return {"success": False, "error": "No factory available"}

        result = factory.run_tests()
        return {
            "success": result.success,
            "message": result.message,
            "error": result.error,
        }

    async def deploy(self, session_id: str, method: str = "docker") -> dict:
        """Deploy the project"""
        factory = self._factories.get(session_id)
        if not factory:
            return {"success": False, "error": "No factory available"}

        result = factory.deploy(method)

        if result.success:
            self._active_sessions[session_id]["status"] = "deployed"
            await self.storage.update_session(session_id, status="deployed")

            # Record delivered project
            await self.storage.create_delivered_project(
                str(uuid.uuid4()),
                session_id,
                name=factory._current_requirement.project_type if factory._current_requirement else "project",
                description=factory._current_requirement.summary if factory._current_requirement else "",
                output_path=str(factory.output_dir),
                tech_stack=factory._current_requirement.metadata.get("suggested_tech_stack", {}).to_dict()
                if factory._current_requirement and factory._current_requirement.metadata.get("suggested_tech_stack")
                else {}
            )

        return {
            "success": result.success,
            "message": result.message,
            "error": result.error,
        }

    async def get_task_summary(self, session_id: str) -> dict:
        """Get task summary for session"""
        factory = self._factories.get(session_id)
        if not factory:
            return {"error": "No factory available"}

        return factory.get_task_summary()

    async def list_sessions(self, status: Optional[str] = None) -> list:
        """List all sessions"""
        return await self.storage.list_sessions(status=status)

    async def cleanup_session(self, session_id: str):
        """Cleanup session resources"""
        if session_id in self._confirmation_flows:
            del self._confirmation_flows[session_id]
        if session_id in self._factories:
            del self._factories[session_id]
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
