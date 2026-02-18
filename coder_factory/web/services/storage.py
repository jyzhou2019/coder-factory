"""
Data Storage Service

SQLite-based persistence for sessions and tasks
"""

from datetime import datetime
from typing import Optional
import json

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import select

Base = declarative_base()


class SessionModel(Base):
    """Session database model"""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    status = Column(String(20), default="idle")
    requirement_data = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = relationship("TaskModel", back_populates="session", cascade="all, delete-orphan")
    dialog_turns = relationship("DialogTurnModel", back_populates="session", cascade="all, delete-orphan")


class TaskModel(Base):
    """Task database model"""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id"))
    title = Column(String(255))
    description = Column(Text, default="")
    task_type = Column(String(20), default="unknown")
    priority = Column(String(5), default="P2")
    status = Column(String(20), default="pending")
    progress = Column(Integer, default=0)
    parent_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("SessionModel", back_populates="tasks")
    subtasks = relationship("TaskModel", backref="parent", remote_side=[id])


class DialogTurnModel(Base):
    """Dialog turn database model"""
    __tablename__ = "dialog_turns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id"))
    turn_id = Column(Integer)
    user_input = Column(Text, default="")
    system_response = Column(Text, default="")
    state_before = Column(String(20))
    state_after = Column(String(20))
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("SessionModel", back_populates="dialog_turns")


class DeliveredProjectModel(Base):
    """Delivered project database model"""
    __tablename__ = "delivered_projects"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id"))
    name = Column(String(255))
    description = Column(Text)
    output_path = Column(String(500))
    tech_stack = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)


class StorageService:
    """
    Async storage service using SQLAlchemy + aiosqlite
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.async_session = None

    async def init_db(self):
        """Initialize database"""
        self.engine = create_async_engine(self.database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()

    # Session operations
    async def create_session(self, session_id: str, **kwargs) -> SessionModel:
        """Create a new session"""
        async with self.async_session() as session:
            db_session = SessionModel(
                id=session_id,
                status=kwargs.get("status", "idle"),
                requirement_data=json.dumps(kwargs.get("requirement_data", {})),
            )
            session.add(db_session)
            await session.commit()
            await session.refresh(db_session)
            return db_session

    async def get_session(self, session_id: str) -> Optional[SessionModel]:
        """Get session by ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(SessionModel).where(SessionModel.id == session_id)
            )
            return result.scalar_one_or_none()

    async def update_session(self, session_id: str, **kwargs) -> Optional[SessionModel]:
        """Update session"""
        async with self.async_session() as session:
            db_session = await session.execute(
                select(SessionModel).where(SessionModel.id == session_id)
            )
            db_session = db_session.scalar_one_or_none()
            if db_session:
                if "status" in kwargs:
                    db_session.status = kwargs["status"]
                if "requirement_data" in kwargs:
                    db_session.requirement_data = json.dumps(kwargs["requirement_data"])
                db_session.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(db_session)
            return db_session

    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        async with self.async_session() as session:
            db_session = await session.execute(
                select(SessionModel).where(SessionModel.id == session_id)
            )
            db_session = db_session.scalar_one_or_none()
            if db_session:
                await session.delete(db_session)
                await session.commit()
                return True
            return False

    async def list_sessions(self, status: Optional[str] = None, limit: int = 100) -> list:
        """List sessions"""
        async with self.async_session() as session:
            query = select(SessionModel).order_by(SessionModel.created_at.desc()).limit(limit)
            if status:
                query = query.where(SessionModel.status == status)
            result = await session.execute(query)
            return result.scalars().all()

    # Task operations
    async def create_task(self, task_id: str, session_id: str, **kwargs) -> TaskModel:
        """Create a new task"""
        async with self.async_session() as session:
            task = TaskModel(
                id=task_id,
                session_id=session_id,
                title=kwargs.get("title", ""),
                description=kwargs.get("description", ""),
                task_type=kwargs.get("task_type", "unknown"),
                priority=kwargs.get("priority", "P2"),
                status=kwargs.get("status", "pending"),
                progress=kwargs.get("progress", 0),
                parent_id=kwargs.get("parent_id"),
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task

    async def get_task(self, task_id: str) -> Optional[TaskModel]:
        """Get task by ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(TaskModel).where(TaskModel.id == task_id)
            )
            return result.scalar_one_or_none()

    async def update_task(self, task_id: str, **kwargs) -> Optional[TaskModel]:
        """Update task"""
        async with self.async_session() as session:
            task = await session.execute(
                select(TaskModel).where(TaskModel.id == task_id)
            )
            task = task.scalar_one_or_none()
            if task:
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                if kwargs.get("status") == "completed":
                    task.completed_at = datetime.utcnow()
                task.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(task)
            return task

    async def list_tasks(
        self,
        session_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """List tasks"""
        async with self.async_session() as session:
            query = select(TaskModel).order_by(TaskModel.created_at.desc()).limit(limit)
            if session_id:
                query = query.where(TaskModel.session_id == session_id)
            if status:
                query = query.where(TaskModel.status == status)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_running_tasks(self) -> list:
        """Get all running tasks"""
        async with self.async_session() as session:
            result = await session.execute(
                select(TaskModel).where(TaskModel.status == "in_progress")
            )
            return result.scalars().all()

    # Dialog operations
    async def add_dialog_turn(
        self,
        session_id: str,
        turn_id: int,
        user_input: str,
        system_response: str,
        state_before: str,
        state_after: str
    ) -> DialogTurnModel:
        """Add a dialog turn"""
        async with self.async_session() as session:
            turn = DialogTurnModel(
                session_id=session_id,
                turn_id=turn_id,
                user_input=user_input,
                system_response=system_response,
                state_before=state_before,
                state_after=state_after,
            )
            session.add(turn)
            await session.commit()
            await session.refresh(turn)
            return turn

    async def get_dialog_history(self, session_id: str) -> list:
        """Get dialog history for a session"""
        async with self.async_session() as session:
            result = await session.execute(
                select(DialogTurnModel)
                .where(DialogTurnModel.session_id == session_id)
                .order_by(DialogTurnModel.turn_id)
            )
            return result.scalars().all()

    # Delivered project operations
    async def create_delivered_project(
        self,
        project_id: str,
        session_id: str,
        **kwargs
    ) -> DeliveredProjectModel:
        """Create a delivered project record"""
        async with self.async_session() as session:
            project = DeliveredProjectModel(
                id=project_id,
                session_id=session_id,
                name=kwargs.get("name", ""),
                description=kwargs.get("description", ""),
                output_path=kwargs.get("output_path", ""),
                tech_stack=json.dumps(kwargs.get("tech_stack", {})),
            )
            session.add(project)
            await session.commit()
            await session.refresh(project)
            return project

    async def list_delivered_projects(self, limit: int = 50) -> list:
        """List delivered projects"""
        async with self.async_session() as session:
            result = await session.execute(
                select(DeliveredProjectModel)
                .order_by(DeliveredProjectModel.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()

    # Statistics
    async def get_stats(self) -> dict:
        """Get storage statistics"""
        async with self.async_session() as session:
            sessions_result = await session.execute(select(SessionModel))
            sessions = sessions_result.scalars().all()

            tasks_result = await session.execute(select(TaskModel))
            tasks = tasks_result.scalars().all()

            projects_result = await session.execute(select(DeliveredProjectModel))
            projects = projects_result.scalars().all()

            return {
                "total_sessions": len(sessions),
                "active_sessions": len([s for s in sessions if s.status not in ["completed", "cancelled"]]),
                "total_tasks": len(tasks),
                "running_tasks": len([t for t in tasks if t.status == "in_progress"]),
                "completed_tasks": len([t for t in tasks if t.status == "completed"]),
                "delivered_projects": len(projects),
            }
