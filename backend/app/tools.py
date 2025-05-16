from typing import Dict, Any, Optional, List
import httpx
import asyncio
from langchain_core.tools import tool
from langchain_core.vectorstores import VectorStoreRetriever
from app.utils.chains import get_interests_rag_chain

from langchain.tools import BaseTool

class TeamMemberInterestsTool(BaseTool):
    """Tool to get interests of a team member."""
    
    def __init__(self, vector_store_retriever: VectorStoreRetriever):
        super().__init__(
            name="get_team_member_interests",
            description="Get the interests of a team member."
        )
        self._vector_store_retriever = vector_store_retriever

    @property
    def vector_store_retriever(self) -> VectorStoreRetriever:
        return self._vector_store_retriever

    def _run(self, team_member: str) -> str:
        """
        Get the interests of a team member.
        
        Args:
            team_member: The team member's name to get interests for
        
        Returns:
            A string containing the team member's interests
        """
        if not self._vector_store_retriever:
            raise ValueError("Vector store retriever is required")
            
        rag_chain = get_interests_rag_chain(self._vector_store_retriever)
        query_text = f"Cuáles son 5 de los principales intereses de {team_member}?"
        response = rag_chain.invoke({"question": query_text})
        return response

    async def _arun(self, team_member: str) -> str:
        """
        Async implementation of _run.
        Runs the synchronous code in a separate thread to avoid blocking.
        """
        return await asyncio.to_thread(self._run, team_member)
