from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
import os
import json
import base64
from typing import List, Dict, Optional

class AIBrain:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.planner_chat = None
        self.vision_chat = None
        
    def _init_planner(self, session_id: str):
        """Initialize planner LLM (Gemini 3 Flash)"""
        self.planner_chat = LlmChat(
            api_key=self.api_key,
            session_id=f"planner_{session_id}",
            system_message="""
You are Sahayak, an intelligent browser automation assistant. Your role is to:
1. Convert user commands into detailed step-by-step action plans
2. Each step should be a concrete browser action
3. Return plans in JSON format with this structure:
{
  "steps": [
    {"action": "navigate", "target": "https://example.com"},
    {"action": "click", "target": "button.submit"},
    {"action": "type", "target": "input#email", "value": "user@example.com", "sensitive": false},
    {"action": "screenshot", "reason": "verify login"}
  ],
  "goal": "description of end goal"
}

Available actions: navigate, click, type, screenshot, wait
Always include screenshots after important actions to verify success.
"""
        ).with_model("gemini", "gemini-3-flash-preview")
    
    def _init_vision(self, session_id: str):
        """Initialize vision LLM (OpenAI GPT Image 1)"""
        self.vision_chat = LlmChat(
            api_key=self.api_key,
            session_id=f"vision_{session_id}",
            system_message="""
You are a visual analysis expert for browser automation. Analyze screenshots and:
1. Describe what you see on the page
2. Identify if the expected action was successful
3. Suggest next actions or corrections needed
4. Detect error messages or unexpected states
5. Identify interactive elements (buttons, inputs, links)

Respond in JSON format:
{
  "description": "what you see",
  "success": true/false,
  "next_action": "suggested next step",
  "elements_found": ["list of interactive elements"],
  "errors": ["any error messages visible"]
}
"""
        ).with_model("openai", "gpt-5.2")
    
    async def create_plan(self, user_command: str, session_id: str, user_context: Dict = None) -> Dict:
        """Convert user command into actionable step plan"""
        if not self.planner_chat:
            self._init_planner(session_id)
        
        context_info = ""
        if user_context:
            context_info = f"\n\nUser saved information: {json.dumps(user_context, indent=2)}"
        
        prompt = f"User command: {user_command}{context_info}\n\nCreate a detailed step-by-step browser automation plan."
        
        try:
            response = await self.planner_chat.send_message(UserMessage(text=prompt))
            
            # Parse JSON response
            # Try to extract JSON from response
            response_text = response.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            plan = json.loads(response_text)
            return {"success": True, "plan": plan}
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw response
            return {
                "success": False,
                "error": "Failed to parse plan",
                "raw_response": response
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def analyze_screenshot(self, screenshot_base64: str, session_id: str, context: str = "") -> Dict:
        """Analyze screenshot and provide insights"""
        if not self.vision_chat:
            self._init_vision(session_id)
        
        prompt = f"Analyze this browser screenshot.{' Context: ' + context if context else ''}"
        
        try:
            image_content = ImageContent(image_base64=screenshot_base64)
            
            response = await self.vision_chat.send_message(
                UserMessage(
                    text=prompt,
                    file_contents=[image_content]
                )
            )
            
            # Try to parse JSON response
            response_text = response.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(response_text)
            return {"success": True, "analysis": analysis}
        except json.JSONDecodeError:
            return {
                "success": True,
                "analysis": {
                    "description": response,
                    "success": True,
                    "next_action": "continue"
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def decide_next_action(self, goal: str, current_state: str, screenshot_base64: str, session_id: str) -> Dict:
        """Autonomous decision making based on current state"""
        if not self.vision_chat:
            self._init_vision(session_id)
        
        prompt = f"""
Goal: {goal}
Current State: {current_state}

Based on the screenshot, decide:
1. Has the goal been achieved? 
2. What is the next action needed?
3. What element should be interacted with?

Respond in JSON:
{{
  "goal_achieved": true/false,
  "next_action": {{"action": "click/type/navigate", "target": "selector or URL", "value": "text if typing"}},
  "reasoning": "why this action"
}}
"""
        
        try:
            image_content = ImageContent(image_base64=screenshot_base64)
            
            response = await self.vision_chat.send_message(
                UserMessage(
                    text=prompt,
                    file_contents=[image_content]
                )
            )
            
            response_text = response.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            decision = json.loads(response_text)
            return {"success": True, "decision": decision}
        except Exception as e:
            return {"success": False, "error": str(e)}