"""FastAPI server for trending information retrieval."""
import os
from app.utils.setup import setup

# Call setup to initialize environment
setup()

from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import markdown
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import build_graph, create_agent_state
from datetime import datetime

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

# Valid team members
VALID_TEAM_MEMBERS = [
    "Abel Mesén",
    "Francisco Salas",
    "Grettel",
    "Laura Monestel",
    "Luisa Alfaro",
    "David Quirós",
    "Maria José Alfaro",
    "Maritza Ortiz",
    "Paola Mora Lopez",
    "Robert Monestel"
]

async def stream_agent_response(teamMember: str):
    """
    Stream the agent's response for a given team member.
    
    Args:
        teamMember: The trending team member to query
        
    Yields:
        Chunks of the agent's response as HTML
    """
    # Create the initial prompt
    prompt = f"Find the top trending topic in Google Trends in the United States related to {teamMember.lower()} in the past 24 hours. Then, get the most relevant information related to this topic from Google and Reddit. The information provided must be up to date. Today is {datetime.now().strftime('%B')} {datetime.now().day}, {datetime.now().year}. "
    
    # Initialize state
    state = create_agent_state(messages=[HumanMessage(content=prompt)])
    
    # Process through the graph
    try:
        async for chunk in graph.astream(state, stream_mode="updates"):
            for node, values in chunk.items():
                # Only yield messages from the agent
                if node == "agent":
                    last_message = values["messages"][-1].text()
                    if last_message != "":
                        # Convert markdown to HTML
                        html_content = markdown.markdown(last_message)
                        yield html_content

    except Exception as e:
        # Log the error but don't raise it to avoid breaking the stream
        print(f"Error in streaming response: {str(e)}")
        yield f"\n\nError during response generation: {str(e)}"


@app.get("/api/trending/{teamMember}")
async def get_trending(
    teamMember: str = Path(..., description="The team member to get trending information for")
):
    """
    Get trending information for a specific team member.
    
    Args:
        teamMember: The team member to get trending information for
        
    Returns:
        A streaming response with trending information as HTML
    """
    # Validate team member
    if teamMember not in VALID_TEAM_MEMBERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid team member. Must be one of: {', '.join(VALID_TEAM_MEMBERS)}"
        )
    
    # Return streaming response
    return StreamingResponse(
        stream_agent_response(teamMember),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",  # Disable buffering for Nginx
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

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