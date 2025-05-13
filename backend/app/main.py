"""FastAPI server for trending information retrieval."""
import os
import json
from functools import partial
from app.setup.environment import setup

# Call setup to initialize environment
setup()

from typing import Optional
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from app.setup.data import get_company_culture, get_conversations_retriever
from app.tools import TeamMemberInterestsTool

app = FastAPI(title="Trending Information API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO:In real life, this content would come from emails, chats or transcripts.
DATA_FILES = [
    "app/data/_chat_abel_mesen.txt",
    "app/data/_chat_francisco_salas.txt",
    "app/data/_chat_grettel.txt",
    "app/data/_chat_laura_monestel.txt",
    "app/data/_chat_luisa_alfaro.txt",
    "app/data/_chat_maria_jose_alfaro.txt",
    "app/data/_chat_maritza_ortiz.txt",
    "app/data/_chat_paola_mora_lopez.txt",
    "app/data/_chat_robert_monestel.txt",
]

# Valid team members
VALID_TEAM_MEMBERS = [
    "Abel",
    "Francisco Salas",
    "Grettel",
    "Laura Monestel",
    "Luisa Alfaro",
    "David",
    "Maria José Alfaro",
    "Maritza Ortiz",
    "Paola Mora Lopez",
    "Robert Monestel"
]

# Initialize during startup
mr_company_culture = None
vector_store_retriever = None

@app.on_event("startup")
async def startup_event():
    """Initialize company culture and other async components during app startup"""

    # TODO: This data should be more up to date
    global mr_company_culture
    mr_company_culture = await get_company_culture(model="gpt-4.1-mini", data_files=DATA_FILES)
    mr_company_culture = mr_company_culture.content

    global vector_store_retriever
    vector_store_retriever = await get_conversations_retriever(data_files=DATA_FILES, collection_name="overlapped_conversations", k=6)

    if mr_company_culture is None or vector_store_retriever is None:
        raise HTTPException(status_code=503, detail="Failed to initialize application")

@app.get("/api/gift-ideas/{teamMember}")
async def get_gift_ideas(
    teamMember: str = Path(..., description="The team member to get gift ideas for")
):
    """
    Get thoughtful gift ideas for a specific team member based on their interests 
    and aligned with the company culture.
    
    Args:
        teamMember: The team member to get gift ideas for
        
    Returns:
        A list with 3 gift ideas. Each gift idea is a dictionary with the following keys:
        - name: The name of the gift idea
        - description: A description of the gift idea
    """
    model_name = os.getenv("GIFT_SUGGESTIONS_LLM")
    if not model_name:
        raise ValueError("GIFT_SUGGESTIONS_LLM environment variable not set")

    # Validate team member
    if teamMember not in VALID_TEAM_MEMBERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid team member. Must be one of: {', '.join(VALID_TEAM_MEMBERS)}"
        )
    
    # Use a proper ReAct formatted prompt
    AGENT_PROMPT = """Eres un amigo experto regalando regalos. Puedes sugerir ideas de regalos concretas que no sean demasiado caras o puedes responder que no hay suficiente información en caso de que no sepás suficiente sobre los intereses de la persona. El formato del resultado debe ser una lista de ideas de regalos en JSON, donde cada idea es de la forma:
    {{
        name: nombre del regalo,
        description: una explicación simple de por qué es un buen regalo (máximo 30 palabras),
    }}
    
    Tienes acceso a las siguientes herramientas:

    {tools}

    Usa el siguiente formato:

    Question: la pregunta inicial que debes responder
    Thought: siempre debes pensar qué hacer
    Action: la acción a tomar, debe ser una de [{tool_names}]
    Action Input: la entrada para la acción
    Observation: el resultado de la acción
    ... (este Thought/Action/Action Input/Observation puede repetirse N veces)
    Thought: Ahora conozco la respuesta final
    Final Answer: la respuesta final a la pregunta inicial.

    ¡Comienza!

    Question: {input}
    Thought: {agent_scratchpad}"""
    
    prompt_template = PromptTemplate.from_template(AGENT_PROMPT)

    # Create the agent with the required tools
    tools = [TeamMemberInterestsTool(vector_store_retriever)]
    
    # Create the agent using our custom prompt template
    agent = create_react_agent(
        llm=ChatOpenAI(model=model_name, temperature=1.2),
        tools=tools,
        prompt=prompt_template,
    )

    # Initialize the agent with the team member's name
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=7
    )

    # Get the agent's response
    response = await agent_executor.ainvoke(
        {"input": f"Sugiere 3 regalos para {teamMember}"}
    )
    
    # Extract the output
    content = response.get("output", "")
    
    # Try to parse the JSON from the content
    try:
        gift_ideas = json.loads(content)

    except json.JSONDecodeError:
        # If JSON parsing fails, return an error
        raise HTTPException(
            status_code=500,
            detail="Failed to parse gift ideas from the response"
        )
    
    return {"giftIdeas": gift_ideas}


@app.get("/api/teamMembers")
async def get_team_members():
    """
    Get the list of valid team members.
    
    Returns:
        List of valid team members
    """
    return {"teamMembers": VALID_TEAM_MEMBERS}

# Determine the frontend build directory 
# If in Docker, the frontend build is at /app/frontend/build
# If running locally, use relative path ../frontend/build
FRONTEND_BUILD_DIR = "/app/frontend/build"
FRONTEND_STATIC_DIR = os.path.join(FRONTEND_BUILD_DIR, "assets")
FRONTEND_INDEX_HTML = os.path.join(FRONTEND_BUILD_DIR, "index.html")

# Mount the frontend build folder (only in production)
if os.getenv("ENV", "development").lower() == "production":
    print("Production environment detected")
    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(FRONTEND_INDEX_HTML)

    # Catch-all route to serve React Router paths
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        # If the path is an API endpoint, skip this handler
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Check if a static file exists in the build folder
        static_file_path = os.path.join(FRONTEND_BUILD_DIR, full_path)
        if os.path.isfile(static_file_path):
            return FileResponse(static_file_path)
        
        # Otherwise, serve the index.html for client-side routing
        return FileResponse(FRONTEND_INDEX_HTML)

    # Mount static files (JavaScript, CSS, images)
    app.mount("/assets", StaticFiles(directory=FRONTEND_STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    # Get host and port from environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    env = os.getenv("ENV", "development")
    
    # Only enable auto-reload in development
    reload = env.lower() == "development"
    
    uvicorn.run("app.main:app", host=host, port=port, reload=reload) 