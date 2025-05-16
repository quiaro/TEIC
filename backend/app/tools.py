from typing import Dict, Any, Optional, List
import httpx
import asyncio
from langchain_core.tools import tool
from langchain_core.vectorstores import VectorStoreRetriever
from app.utils.chains import get_interests_rag_chain

from langchain.tools import BaseTool

class TeamMemberInterestsTool(BaseTool):
    name: str = "get_team_member_interests"
    description: str = "Get the interests of a team member."
    vector_store_retriever: VectorStoreRetriever

    def __init__(self, vector_store_retriever: VectorStoreRetriever):
        self.vector_store_retriever = vector_store_retriever
        super().__init__()

    def _run(self, team_member: str) -> str:
        """
        Get the interests of a team member.
        
        Args:
            team_member: The team member's name to get interests for
        
        Returns:
            A string containing the team member's interests
        """
        if not self.vector_store_retriever:
            raise ValueError("Vector store retriever is required")
            
        rag_chain = get_interests_rag_chain(self.vector_store_retriever)
        query_text = f"Cuáles son 5 de los principales intereses de {team_member}?"
        response = rag_chain.invoke({"question": query_text})
        return response

    async def _arun(self, team_member: str) -> str:
        """
        Async implementation of _run.
        Runs the synchronous code in a separate thread to avoid blocking.
        """
        return await asyncio.to_thread(self._run, team_member)
