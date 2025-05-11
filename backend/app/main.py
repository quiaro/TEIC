"""FastAPI server for trending information retrieval."""
import os
from app.setup.environment import setup

# Call setup to initialize environment
setup()

from typing import Optional
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.graph import build_graph
from app.setup.data import get_company_culture, get_conversations_retriever

graph = build_graph()

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
    "app/data/_chat_abel_mesén.txt",
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
        - link: A link to where it can be purchased
    """
    gift_ideas = []

    # Validate team member
    if teamMember not in VALID_TEAM_MEMBERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid team member. Must be one of: {', '.join(VALID_TEAM_MEMBERS)}"
        )
    
    return gift_ideas


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