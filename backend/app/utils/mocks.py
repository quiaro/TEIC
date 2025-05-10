from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from typing import Any, List, Optional, AsyncIterator

AI_RESPONSE = "La empresa muestra una cultura agradable, amistosa, positiva y colaborativa, con un fuerte énfasis en el trabajo en equipo y el apoyo mutuo entre los miembros del equipo."

class MockCompanyCultureModel(BaseChatModel):
    """Mock chat model for development purposes"""
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Mock response generation (synchronous)"""
        message = AIMessage(content=AI_RESPONSE)
        return ChatResult(generations=[ChatGeneration(message=message)])
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Mock response generation (asynchronous)"""
        message = AIMessage(content=AI_RESPONSE)
        return ChatResult(generations=[ChatGeneration(message=message)])

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> AsyncIterator[AIMessage]:
        """Mock streaming - yields the same message as generate"""
        yield AIMessage(content=AI_RESPONSE)

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "mock-chat-model"