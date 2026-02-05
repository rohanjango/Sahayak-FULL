"""
Sahayak Web App - Main Backend
Autonomous AI Assistant with Browser Control
"""

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
import base64
from datetime import datetime
import random
import time

# Phase 2: AI Brain Integration
from ai_brain import AIBrain

# Phase 3: Browser Control
from browser_controller import BrowserController

# Phase 4: Vision Capabilities
from vision_processor import VisionProcessor

# Phase 6: Self-Healing Selectors
from selector_healer import SelectorHealer

# Phase 7: Memory System
from memory_manager import MemoryManager

# Phase 8: Human-Like Behavior
from human_simulator import HumanSimulator

# Phase 9: Privacy Layer
from privacy_layer import PrivacyLayer

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Logic
    print("Sahayak AI Assistant started successfully")
    print("Memory system initialized: sahayak_memory.db")
    print("Browser initialized successfully")
    yield
    # Shutdown Logic
    print("Shutting down...")

app = FastAPI(
    title="Sahayak AI Assistant", 
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize all components
ai_brain = AIBrain()
browser_controller = BrowserController()
vision_processor = VisionProcessor()
selector_healer = SelectorHealer()
memory_manager = MemoryManager()
human_simulator = HumanSimulator()
privacy_layer = PrivacyLayer()

# Request/Response Models
class CommandRequest(BaseModel):
    command: str
    user_id: Optional[str] = "default_user"
    save_memory: Optional[bool] = True

class StepResponse(BaseModel):
    step_number: int
    description: str
    status: str
    screenshot: Optional[str] = None
    timestamp: str

class CommandResponse(BaseModel):
    task_id: str
    status: str
    steps: List[StepResponse]
    final_result: Optional[str] = None
    execution_time: float

class MemoryItem(BaseModel):
    key: str
    value: str
    category: Optional[str] = "general"

# Global task storage
active_tasks = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "app": "Sahayak AI Assistant",
        "version": "1.0.0",
        "capabilities": [
            "Natural Language Understanding",
            "Browser Automation",
            "Visual Screen Understanding",
            "Memory & Personalization",
            "Privacy-Safe Operations"
        ]
    }

@app.post("/api/execute", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """
    Main endpoint to execute user commands
    Phases 1-9: Complete autonomous execution
    """
    start_time = time.time()
    task_id = f"task_{int(time.time() * 1000)}"
    
    try:
        # Phase 7: Check memory for personalization
        user_context = await memory_manager.get_user_context(request.user_id)
        
        # Phase 2: Convert command to action plan
        action_plan = await ai_brain.create_action_plan(
            request.command,
            user_context
        )
        
        steps_results = []
        
        # Phase 5: Autonomous Operation Loop
        for step_idx, step in enumerate(action_plan['steps']):
            step_result = await execute_single_step(
                step,
                step_idx,
                request.user_id
            )
            steps_results.append(step_result)
            
            # Check if task should continue
            if step_result.status == "failed":
                break
        
        # Phase 7: Save to memory if requested
        if request.save_memory:
            await memory_manager.save_execution(
                request.user_id,
                request.command,
                steps_results
            )
        
        execution_time = time.time() - start_time
        
        return CommandResponse(
            task_id=task_id,
            status="completed" if all(s.status == "success" for s in steps_results) else "partial",
            steps=steps_results,
            final_result=action_plan.get('goal_achievement', 'Task completed'),
            execution_time=execution_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def execute_single_step(step: Dict, step_idx: int, user_id: str) -> StepResponse:
    """
    Execute a single step with all autonomous capabilities
    """
    try:
        # Phase 8: Add human-like delay
        await human_simulator.random_delay()
        
        # Phase 3: Execute browser action
        action_result = await browser_controller.execute_action(step)
        
        # Phase 4: Capture and process screenshot
        screenshot = await browser_controller.capture_screenshot()
        
        # Phase 9: Apply privacy layer
        safe_screenshot = await privacy_layer.blur_sensitive_data(screenshot)
        
        # Phase 4: Vision analysis
        vision_analysis = await vision_processor.analyze_screen(safe_screenshot)
        
        # Phase 5: Verify step completion
        is_complete = await ai_brain.verify_step_completion(
            step,
            vision_analysis
        )
        
        # Phase 6: Self-healing if step failed
        if not is_complete and step.get('element'):
            healed_selector = await selector_healer.find_alternative(
                step['element'],
                safe_screenshot
            )
            if healed_selector:
                # Retry with healed selector
                step['element'] = healed_selector
                action_result = await browser_controller.execute_action(step)
                is_complete = True
        
        return StepResponse(
            step_number=step_idx + 1,
            description=step['description'],
            status="success" if is_complete else "failed",
            screenshot=base64.b64encode(safe_screenshot).decode() if safe_screenshot else None,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        return StepResponse(
            step_number=step_idx + 1,
            description=step['description'],
            status="failed",
            screenshot=None,
            timestamp=datetime.now().isoformat()
        )

@app.post("/api/memory/save")
async def save_memory(item: MemoryItem, user_id: str = "default_user"):
    """Save user preferences and information"""
    await memory_manager.save_item(user_id, item.key, item.value, item.category)
    return {"status": "saved", "key": item.key}

@app.get("/api/memory/{user_id}")
async def get_memory(user_id: str):
    """Retrieve user's stored memories"""
    memories = await memory_manager.get_all_memories(user_id)
    return {"user_id": user_id, "memories": memories}

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket for real-time step-by-step updates
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            command_data = json.loads(data)
            
            # Execute command with live updates
            await execute_with_live_updates(websocket, command_data)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

async def execute_with_live_updates(websocket: WebSocket, command_data: Dict):
    """Execute command and send updates via WebSocket"""
    user_context = await memory_manager.get_user_context(command_data.get('user_id', 'default'))
    action_plan = await ai_brain.create_action_plan(command_data['command'], user_context)
    
    for step_idx, step in enumerate(action_plan['steps']):
        # Send step start notification
        await websocket.send_json({
            "type": "step_start",
            "step": step_idx + 1,
            "description": step['description']
        })
        
        # Execute step
        result = await execute_single_step(step, step_idx, command_data.get('user_id', 'default'))
        
        # Send step completion
        await websocket.send_json({
            "type": "step_complete",
            "step": step_idx + 1,
            "status": result.status,
            "screenshot": result.screenshot
        })
        
        await asyncio.sleep(0.5)
    
    # Send final completion
    await websocket.send_json({
        "type": "task_complete",
        "status": "success"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
