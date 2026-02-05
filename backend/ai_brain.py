"""
Phase 2: AI Brain Integration
Converts natural language commands into actionable step plans
"""

import os
from typing import Dict, List, Any
import requests
import json

class AIBrain:
    def __init__(self):
        self.api_key = "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"
        self.api_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
    async def create_action_plan(self, command: str, user_context: Dict = None) -> Dict:
        """
        Convert user command into structured action plan
        """
        
        # Build prompt with context
        prompt = self._build_planning_prompt(command, user_context)
        
        # Call Hugging Face LLM
        try:
            plan = await self._call_llm(prompt)
            return self._parse_plan(plan)
        except Exception as e:
            # Fallback to rule-based parsing
            return self._fallback_plan(command)
    
    def _build_planning_prompt(self, command: str, context: Dict = None) -> str:
        """Build the prompt for the LLM"""
        
        context_str = ""
        if context:
            context_str = f"\nUser Context:\n{json.dumps(context, indent=2)}\n"
        
        prompt = f"""You are an AI assistant that converts user commands into browser automation steps.

{context_str}
User Command: {command}

Create a detailed step-by-step plan to accomplish this task. Return ONLY a JSON object with this structure:
{{
    "goal": "brief description of the goal",
    "steps": [
        {{
            "action": "navigate|click|type|wait|scroll",
            "element": "CSS selector or description",
            "value": "value to type (if applicable)",
            "description": "human-readable description",
            "verification": "what to check to confirm success"
        }}
    ]
}}

Examples:
Command: "Search for latest AI news on Google"
{{
    "goal": "Search for latest AI news on Google",
    "steps": [
        {{"action": "navigate", "element": "", "value": "https://google.com", "description": "Navigate to Google", "verification": "Google search page loaded"}},
        {{"action": "click", "element": "textarea[name='q']", "value": "", "description": "Click search box", "verification": "Search box is focused"}},
        {{"action": "type", "element": "textarea[name='q']", "value": "latest AI news", "description": "Type search query", "verification": "Query text appears in search box"}},
        {{"action": "click", "element": "input[name='btnK']", "value": "", "description": "Click search button", "verification": "Search results page loaded"}}
    ]
}}

Now create a plan for: {command}"""

        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """Call Hugging Face Inference API"""
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1000,
                "temperature": 0.3,
                "top_p": 0.9,
                "return_full_text": False
            }
        }
        
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '')
            return str(result)
        else:
            raise Exception(f"LLM API error: {response.status_code}")
    
    def _parse_plan(self, llm_response: str) -> Dict:
        """Parse LLM response into structured plan"""
        
        try:
            # Try to extract JSON from response
            if '{' in llm_response:
                json_start = llm_response.index('{')
                json_end = llm_response.rindex('}') + 1
                json_str = llm_response[json_start:json_end]
                plan = json.loads(json_str)
                return plan
        except:
            pass
        
        # If parsing fails, return default structure
        return {
            "goal": "Execute user command",
            "steps": []
        }
    
    def _fallback_plan(self, command: str) -> Dict:
        """
        Fallback rule-based planning when LLM fails
        """
        
        command_lower = command.lower()
        
        # Google search pattern
        if "search" in command_lower and "google" in command_lower:
            query = command_lower.replace("search", "").replace("google", "").replace("for", "").replace("on", "").strip()
            return {
                "goal": f"Search Google for: {query}",
                "steps": [
                    {
                        "action": "navigate",
                        "element": "",
                        "value": "https://google.com",
                        "description": "Navigate to Google",
                        "verification": "Google search page loaded"
                    },
                    {
                        "action": "type",
                        "element": "textarea[name='q']",
                        "value": query,
                        "description": f"Type search query: {query}",
                        "verification": "Query entered in search box"
                    },
                    {
                        "action": "click",
                        "element": "input[name='btnK']",
                        "value": "",
                        "description": "Click search button",
                        "verification": "Search results displayed"
                    }
                ]
            }
        
        # Navigate pattern
        elif "go to" in command_lower or "open" in command_lower or "visit" in command_lower:
            url = self._extract_url(command)
            return {
                "goal": f"Navigate to {url}",
                "steps": [
                    {
                        "action": "navigate",
                        "element": "",
                        "value": url,
                        "description": f"Navigate to {url}",
                        "verification": f"Page loaded successfully"
                    }
                ]
            }
        
        # Default plan
        return {
            "goal": "Execute command",
            "steps": [
                {
                    "action": "wait",
                    "element": "",
                    "value": "1",
                    "description": "Processing command",
                    "verification": "Command received"
                }
            ]
        }
    
    def _extract_url(self, command: str) -> str:
        """Extract URL from command"""
        words = command.split()
        for word in words:
            if "." in word and any(tld in word for tld in ['.com', '.org', '.net', '.io', '.ai']):
                if not word.startswith('http'):
                    return f"https://{word}"
                return word
        return "https://google.com"
    
    async def verify_step_completion(self, step: Dict, vision_analysis: Dict) -> bool:
        """
        Verify if a step was completed successfully using vision analysis
        """
        
        verification = step.get('verification', '').lower()
        screen_text = vision_analysis.get('text', '').lower()
        
        # Check if verification criteria appears in screen
        if verification and verification in screen_text:
            return True
        
        # Check action-specific success criteria
        action = step.get('action')
        
        if action == "navigate":
            # Check if URL changed or page loaded
            return vision_analysis.get('page_loaded', False)
        
        elif action == "click":
            # Check if screen changed after click
            return vision_analysis.get('screen_changed', False)
        
        elif action == "type":
            # Check if typed text appears on screen
            typed_value = step.get('value', '').lower()
            return typed_value in screen_text
        
        # Default: assume success
        return True
