"""Engines module initialization"""

from .claude_client import ClaudeCodeClient, ClaudeCodeResult
from .requirement_parser import RequirementParser, ParseResult
from .interaction_manager import (
    InteractionManager,
    DialogState,
    QuestionType,
    Question,
    DialogTurn,
    ChangeRecord,
    DialogStateMachine,
)
from .confirmation_flow import ConfirmationFlow
from .tech_stack_kb import (
    TechStackKnowledgeBase,
    ProjectCategory,
    ScaleLevel,
    TechOption,
    TechStackTemplate,
    TECH_OPTIONS,
    TECH_STACK_TEMPLATES,
)
from .architecture_designer import (
    ArchitectureDesigner,
    ArchitectureDesign,
    ArchitectureComponent,
)
from .deployment_engine import (
    DeploymentEngine,
    DockerfileGenerator,
    DockerComposeGenerator,
    DockerConfig,
    ComposeService,
    DOCKER_TEMPLATES,
)
from .delivery_pipeline import (
    DeliveryPipeline,
    ChecklistGenerator,
    DocumentGenerator,
    ReleaseManager,
    DeliveryChecklist,
    CheckItem,
    CheckStatus,
    CheckCategory,
    ReleaseNote,
)

__all__ = [
    # Claude Client
    "ClaudeCodeClient",
    "ClaudeCodeResult",
    # Requirement Parser
    "RequirementParser",
    "ParseResult",
    # Interaction Manager
    "InteractionManager",
    "DialogState",
    "QuestionType",
    "Question",
    "DialogTurn",
    "ChangeRecord",
    "DialogStateMachine",
    # Confirmation Flow
    "ConfirmationFlow",
    # Tech Stack KB
    "TechStackKnowledgeBase",
    "ProjectCategory",
    "ScaleLevel",
    "TechOption",
    "TechStackTemplate",
    "TECH_OPTIONS",
    "TECH_STACK_TEMPLATES",
    # Architecture Designer
    "ArchitectureDesigner",
    "ArchitectureDesign",
    "ArchitectureComponent",
    # Deployment Engine
    "DeploymentEngine",
    "DockerfileGenerator",
    "DockerComposeGenerator",
    "DockerConfig",
    "ComposeService",
    "DOCKER_TEMPLATES",
    # Delivery Pipeline
    "DeliveryPipeline",
    "ChecklistGenerator",
    "DocumentGenerator",
    "ReleaseManager",
    "DeliveryChecklist",
    "CheckItem",
    "CheckStatus",
    "CheckCategory",
    "ReleaseNote",
]
