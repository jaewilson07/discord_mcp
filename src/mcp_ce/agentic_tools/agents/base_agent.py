"""
Base Agent Class for Pydantic-AI Agents.

Provides common functionality:
- Error handling and retries
- Rate limiting protection
- Logging and monitoring with Logfire
- Standard dependency injection
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Any
import asyncio

import logfire
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

logger = logging.getLogger(__name__)


@dataclass
class AgentDependencies:
    """Base dependencies for all agents."""
    
    # All fields have defaults to allow inheritance with required fields
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    trace_id: Optional[str] = None


DepsT = TypeVar("DepsT", bound=AgentDependencies)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseAgent(ABC, Generic[DepsT, OutputT]):
    """
    Base class for all Pydantic-AI agents.

    Provides common functionality:
    - Error handling and retries
    - Rate limiting protection
    - Logging and monitoring with Logfire
    - Standard dependency injection
    """

    def __init__(
        self,
        model: str = "openai:gpt-4o",
        name: Optional[str] = None,
        retries: int = 3,
        enable_rate_limiting: bool = True,
        **agent_kwargs,
    ):
        self.model = model
        self.name = name or self.__class__.__name__
        self.retries = retries
        self.enable_rate_limiting = enable_rate_limiting
        self._agent = self._create_agent(**agent_kwargs)

    @abstractmethod
    def _create_agent(self, **kwargs) -> Agent:
        """Create and configure the Pydantic-AI agent."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the base system prompt for this agent."""
        pass

    async def run(
        self, user_prompt: str, deps: DepsT, **run_kwargs
    ) -> OutputT:
        """
        Run the agent with rate limiting and error handling.

        Args:
            user_prompt: User's input prompt
            deps: Agent dependencies
            **run_kwargs: Additional arguments to pass to agent.run()

        Returns:
            Agent output (validated Pydantic model)

        Raises:
            Exception: If all retries fail
        """
        with logfire.span(f"{self.name}.run", user_prompt=user_prompt[:100]):
            for attempt in range(self.retries):
                try:
                    logfire.info(
                        f"Running {self.name}",
                        attempt=attempt + 1,
                        retries=self.retries,
                        request_id=deps.request_id,
                    )

                    result = await self._agent.run(
                        user_prompt, deps=deps, **run_kwargs
                    )

                    logfire.info(
                        f"{self.name} completed successfully",
                        attempt=attempt + 1,
                        request_id=deps.request_id,
                    )

                    return result.data

                except Exception as e:
                    logger.error(
                        f"{self.name} attempt {attempt + 1} failed: {e}",
                        exc_info=True,
                    )
                    logfire.error(
                        f"{self.name} attempt failed",
                        attempt=attempt + 1,
                        error=str(e),
                        request_id=deps.request_id,
                    )

                    if attempt == self.retries - 1:
                        raise

                    # Exponential backoff for rate limiting
                    if self.enable_rate_limiting:
                        wait_time = 2 ** attempt
                        logfire.info(
                            f"Rate limit backoff: waiting {wait_time}s",
                            attempt=attempt + 1,
                        )
                        await asyncio.sleep(wait_time)

            # Should never reach here, but type checker needs it
            raise RuntimeError(f"{self.name} failed after {self.retries} attempts")

