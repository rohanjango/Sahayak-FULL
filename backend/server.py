from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
from datetime import datetime, timezone

from database import init_db, save_memory, get_memory, get_execution_history
from autonomous_agent import AutonomousAgent

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app without a prefix
app = FastAPI(title="Sahayak - Autonomous Browser Assistant")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize database on startup
@app.on_event("startup")
async def startup():
    await init_db()
    logging.info("Database initialized")

# Models
class CommandRequest(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    command: str
    mode: str = "guided"  # guided or autonomous

class MemoryRequest(BaseModel):
    user_id: str
    key: str
    value: str

class MemoryQuery(BaseModel):
    user_id: str
    key: Optional[str] = None

class CommandResponse(BaseModel):
    success: bool
    message: str
    execution_log: Optional[List[Dict]] = None
    screenshots: Optional[List[str]] = None
    session_id: Optional[str] = None

# Routes
@api_router.get("/")
async def root():
    return {
        "message": "Sahayak AI Assistant",
        "version": "1.0.0",
        "capabilities": [
            "Browser Automation",
            "Vision-based Navigation",
            "Self-healing Selectors",
            "Memory System",
            "Autonomous Operation"
        ]
    }

@api_router.post("/execute", response_model=CommandResponse)
async def execute_command(request: CommandRequest, background_tasks: BackgroundTasks):
    """Execute a user command"""
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")
        
        session_id = str(uuid.uuid4())
        agent = AutonomousAgent(api_key)
        
        if request.mode == "autonomous":
            # Run autonomous loop
            result = await agent.run_autonomous_loop(
                user_id=request.user_id,
                goal=request.command,
                session_id=session_id
            )
        else:
            # Run guided execution
            result = await agent.execute_command(
                user_id=request.user_id,
                command=request.command,
                session_id=session_id
            )
        
        if result.get('success'):
            return CommandResponse(
                success=True,
                message="Command executed successfully",
                execution_log=result.get('execution_log', []),
                screenshots=result.get('screenshots', []),
                session_id=session_id
            )
        else:
            return CommandResponse(
                success=False,
                message=result.get('error', 'Execution failed'),
                session_id=session_id
            )
    
    except Exception as e:
        logging.error(f"Execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/memory/save")
async def save_user_memory(request: MemoryRequest):
    """Save user memory/preferences"""
    try:
        await save_memory(request.user_id, request.key, request.value)
        return {"success": True, "message": "Memory saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/memory/get")
async def get_user_memory(request: MemoryQuery):
    """Get user memory/preferences"""
    try:
        memory = await get_memory(request.user_id, request.key)
        return {"success": True, "memory": memory}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/history/{user_id}")
async def get_history(user_id: str, limit: int = 10):
    """Get execution history"""
    try:
        history = await get_execution_history(user_id, limit)
        return {"success": True, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sahayak-api"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)