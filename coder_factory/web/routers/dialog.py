"""
Dialog API Router (F002)

Handles interactive requirement confirmation
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Any, List

from ..services.session_manager import SessionManager

router = APIRouter()


class AnswerInput(BaseModel):
    """Answer input model"""
    answer: Any


class ModifyInput(BaseModel):
    """Modify input model"""
    field: str
    value: Any
    reason: Optional[str] = ""


class CancelInput(BaseModel):
    """Cancel input model"""
    reason: Optional[str] = ""


def get_session_manager(request: Request) -> SessionManager:
    """Get session manager from app state"""
    return request.app.state.session_manager


@router.get("/{session_id}/status")
async def get_dialog_status(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get current dialog status

    Returns:
        - state: Current dialog state
        - progress: Confirmation progress
        - unanswered_count: Number of unanswered questions
    """
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    status = await session_manager.get_flow_status(session_id)
    return {
        "session_id": session_id,
        "state": status.get("state", "idle"),
        "dialog_summary": status.get("dialog_summary", {}),
        "unanswered_count": status.get("unanswered_count", 0),
        "changes_count": status.get("changes_count", 0),
    }


@router.get("/{session_id}/question")
async def get_current_question(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get the current question to answer

    Returns the next unanswered question in the confirmation flow
    """
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    question = await session_manager.get_current_question(session_id)

    if not question:
        return {
            "has_question": False,
            "message": "No pending questions",
        }

    return {
        "has_question": True,
        "question": question,
    }


@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: str,
    answer_input: AnswerInput,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Submit answer to current question

    After answering, returns:
        - success: Whether answer was accepted
        - next_question: Next question to answer (if any)
        - state: New dialog state
    """
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await session_manager.answer_question(session_id, answer_input.answer)

    return result


@router.post("/{session_id}/approve")
async def approve_requirement(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Approve the current requirement

    After approval, the requirement is ready for code generation
    """
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await session_manager.approve_requirement(session_id)

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Approval failed")
        )

    return result


@router.post("/{session_id}/modify")
async def modify_requirement(
    session_id: str,
    modify_input: ModifyInput,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Modify a requirement field

    Allows adjusting specific fields before approval
    """
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await session_manager.modify_requirement(
        session_id,
        modify_input.field,
        modify_input.value,
        modify_input.reason
    )

    return result


@router.post("/{session_id}/cancel")
async def cancel_dialog(
    session_id: str,
    cancel_input: CancelInput,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Cancel the current dialog flow"""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await session_manager.cancel_flow(session_id, cancel_input.reason)
    return result


@router.get("/{session_id}/history")
async def get_dialog_history(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get full dialog history for a session"""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history = await session_manager.get_dialog_history(session_id)
    return {
        "session_id": session_id,
        "history": [turn.to_dict() if hasattr(turn, 'to_dict') else turn for turn in history],
    }
