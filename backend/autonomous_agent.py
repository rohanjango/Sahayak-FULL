from browser_automation import BrowserController
from ai_brain import AIBrain
from database import save_execution, save_memory, get_memory
import asyncio
from typing import Dict, List
import json

class AutonomousAgent:
    def __init__(self, api_key: str):
        self.browser = BrowserController()
        self.ai = AIBrain(api_key)
        self.max_iterations = 20  # Prevent infinite loops
        
    async def execute_command(self, user_id: str, command: str, session_id: str) -> Dict:
        """Main execution flow: Plan -> Execute -> Verify"""
        try:
            # Start browser
            await self.browser.start()
            
            # Get user context from memory
            user_context = await get_memory(user_id)
            
            # Create plan
            plan_result = await self.ai.create_plan(command, session_id, user_context)
            
            if not plan_result.get('success'):
                return {
                    "success": False,
                    "error": "Failed to create plan",
                    "details": plan_result
                }
            
            plan = plan_result['plan']
            steps = plan.get('steps', [])
            goal = plan.get('goal', command)
            
            # Execute steps
            execution_log = []
            screenshots = []
            
            for i, step in enumerate(steps):
                step_result = await self._execute_step(step)
                execution_log.append({
                    "step": i + 1,
                    "action": step,
                    "result": step_result
                })
                
                # Take screenshot after each important action
                if step.get('action') in ['navigate', 'click', 'type']:
                    screenshot = await self.browser.take_screenshot()
                    screenshots.append(screenshot)
                    
                    # Analyze screenshot
                    analysis = await self.ai.analyze_screenshot(
                        screenshot, 
                        session_id,
                        f"After {step.get('action')} on {step.get('target')}"
                    )
                    
                    execution_log.append({
                        "step": f"{i + 1}_analysis",
                        "analysis": analysis
                    })
                    
                    # Check if we need to adjust
                    if analysis.get('success') and not analysis.get('analysis', {}).get('success', True):
                        # Something went wrong, try to recover
                        execution_log.append({
                            "step": f"{i + 1}_recovery",
                            "message": "Detected issue, attempting recovery"
                        })
                
                await asyncio.sleep(0.5)  # Small delay between steps
            
            # Save execution history
            await save_execution(user_id, command, execution_log, "completed")
            
            return {
                "success": True,
                "goal": goal,
                "execution_log": execution_log,
                "screenshots": screenshots
            }
            
        except Exception as e:
            await save_execution(user_id, command, [], "failed", str(e))
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            await self.browser.stop()
    
    async def run_autonomous_loop(self, user_id: str, goal: str, session_id: str) -> Dict:
        """Autonomous loop: Observe -> Decide -> Act -> Verify"""
        try:
            await self.browser.start()
            
            iteration = 0
            goal_achieved = False
            execution_log = []
            
            while iteration < self.max_iterations and not goal_achieved:
                iteration += 1
                
                # Observe: Take screenshot
                screenshot = await self.browser.take_screenshot()
                page_info = await self.browser.get_page_info()
                
                # Decide: Ask AI what to do next
                decision_result = await self.ai.decide_next_action(
                    goal=goal,
                    current_state=json.dumps(page_info),
                    screenshot_base64=screenshot,
                    session_id=session_id
                )
                
                if not decision_result.get('success'):
                    execution_log.append({
                        "iteration": iteration,
                        "error": "Decision failed",
                        "details": decision_result
                    })
                    break
                
                decision = decision_result['decision']
                goal_achieved = decision.get('goal_achieved', False)
                
                execution_log.append({
                    "iteration": iteration,
                    "decision": decision,
                    "page_state": page_info
                })
                
                if goal_achieved:
                    break
                
                # Act: Execute the decided action
                next_action = decision.get('next_action', {})
                if next_action:
                    action_result = await self._execute_step(next_action)
                    execution_log.append({
                        "iteration": iteration,
                        "action_result": action_result
                    })
                
                await asyncio.sleep(1)  # Small delay between iterations
            
            await save_execution(user_id, goal, execution_log, "completed" if goal_achieved else "max_iterations")
            
            return {
                "success": True,
                "goal_achieved": goal_achieved,
                "iterations": iteration,
                "execution_log": execution_log
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            await self.browser.stop()
    
    async def _execute_step(self, step: Dict) -> Dict:
        """Execute a single step"""
        action = step.get('action')
        target = step.get('target')
        value = step.get('value')
        
        if action == 'navigate':
            return await self.browser.navigate(target)
        elif action == 'click':
            return await self.browser.click_element(target)
        elif action == 'type':
            is_sensitive = step.get('sensitive', False)
            return await self.browser.type_text(target, value, is_sensitive)
        elif action == 'wait':
            wait_time = step.get('duration', 1)
            await asyncio.sleep(wait_time)
            return {"success": True, "waited": wait_time}
        elif action == 'screenshot':
            screenshot = await self.browser.take_screenshot()
            return {"success": True, "screenshot": screenshot}
        else:
            return {"success": False, "error": f"Unknown action: {action}"}