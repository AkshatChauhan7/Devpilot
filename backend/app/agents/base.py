"""Base agent class and state management."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class AgentState(str, Enum):
    """Agent execution states."""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentMessage:
    """Message between agents."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender: str = ""
    recipient: str = ""
    type: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentContext:
    """Shared context for agent execution."""
    repository_id: int
    task_id: int
    user_id: int
    github_token: Optional[str] = None
    repository_path: Optional[str] = None
    files: Dict[str, str] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.state = AgentState.IDLE
        self.context: Optional[AgentContext] = None
        self.messages: List[AgentMessage] = []
        self._client = None

    @property
    def client(self):
        """Get Anthropic client."""
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    @abstractmethod
    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        """Execute the agent's main logic."""
        pass

    async def think(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Use Claude to think/reason."""
        self.state = AgentState.THINKING
        try:
            messages = [{"role": "user", "content": prompt}]
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})

            response = await self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.2),
                messages=messages,
            )
            return response.content[0].text if response.content else ""
        finally:
            self.state = AgentState.IDLE

    async def act(self, action: str, **kwargs) -> Any:
        """Perform an action."""
        self.state = AgentState.ACTING
        try:
            return await self._perform_action(action, **kwargs)
        finally:
            self.state = AgentState.IDLE

    @abstractmethod
    async def _perform_action(self, action: str, **kwargs) -> Any:
        """Perform a specific action."""
        pass

    def send_message(self, recipient: str, msg_type: str, content: Dict[str, Any]):
        """Send message to another agent."""
        message = AgentMessage(
            sender=self.name,
            recipient=recipient,
            type=msg_type,
            content=content,
        )
        self.messages.append(message)

    def get_messages(self, msg_type: Optional[str] = None) -> List[AgentMessage]:
        """Get received messages."""
        if msg_type:
            return [m for m in self.messages if m.type == msg_type]
        return self.messages

    def clear_messages(self):
        """Clear message queue."""
        self.messages.clear()


class AgentRegistry:
    """Registry for managing agents."""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        """Register an agent."""
        self._agents[agent.name] = agent

    def get(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name."""
        return self._agents.get(name)

    def get_all(self) -> List[BaseAgent]:
        """Get all registered agents."""
        return list(self._agents.values())

    def clear(self):
        """Clear registry."""
        self._agents.clear()


# Global registry
agent_registry = AgentRegistry()