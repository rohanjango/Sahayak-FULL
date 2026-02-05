"""
Phase 3: Browser Control Automation
Uses Playwright for real browser control
"""

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from typing import Dict, Optional
import asyncio
import base64

class BrowserController:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.last_screenshot = None
        
    async def initialize(self):
        """Initialize Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = await self.context.new_page()
            print("Browser initialized successfully")
        except Exception as e:
            print(f"Browser initialization error: {e}")
    
    async def execute_action(self, step: Dict) -> Dict:
        """
        Execute a single browser action
        """
        if not self.page:
            await self.initialize()
        
        action = step.get('action', '').lower()
        element = step.get('element', '')
        value = step.get('value', '')
        
        try:
            if action == 'navigate':
                await self._navigate(value)
                
            elif action == 'click':
                await self._click(element)
                
            elif action == 'type':
                await self._type(element, value)
                
            elif action == 'scroll':
                await self._scroll(value)
                
            elif action == 'wait':
                await self._wait(float(value) if value else 1.0)
                
            elif action == 'press':
                await self._press_key(value)
            
            return {"status": "success", "action": action}
            
        except Exception as e:
            return {"status": "error", "action": action, "error": str(e)}
    
    async def _navigate(self, url: str):
        """Navigate to URL"""
        if not url.startswith('http'):
            url = f'https://{url}'
        await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(1)  # Wait for page to settle
    
    async def _click(self, selector: str):
        """Click an element"""
        try:
            # Wait for element to be visible
            await self.page.wait_for_selector(selector, timeout=10000, state='visible')
            await self.page.click(selector)
            await asyncio.sleep(0.5)
        except Exception as e:
            # Try clicking by text if selector fails
            await self._click_by_text(selector)
    
    async def _click_by_text(self, text: str):
        """Click element by text content"""
        element = await self.page.query_selector(f'text="{text}"')
        if element:
            await element.click()
            await asyncio.sleep(0.5)
        else:
            raise Exception(f"Element not found: {text}")
    
    async def _type(self, selector: str, text: str):
        """Type text into an element"""
        try:
            await self.page.wait_for_selector(selector, timeout=10000, state='visible')
            await self.page.fill(selector, text)
            await asyncio.sleep(0.3)
        except Exception as e:
            # Try focusing and typing if fill fails
            await self.page.focus(selector)
            await self.page.keyboard.type(text, delay=50)
    
    async def _scroll(self, direction: str):
        """Scroll the page"""
        if direction.lower() == 'down':
            await self.page.evaluate('window.scrollBy(0, window.innerHeight)')
        elif direction.lower() == 'up':
            await self.page.evaluate('window.scrollBy(0, -window.innerHeight)')
        await asyncio.sleep(0.5)
    
    async def _wait(self, seconds: float):
        """Wait for specified seconds"""
        await asyncio.sleep(seconds)
    
    async def _press_key(self, key: str):
        """Press a keyboard key"""
        await self.page.keyboard.press(key)
        await asyncio.sleep(0.3)
    
    async def capture_screenshot(self) -> bytes:
        """
        Capture current page screenshot
        Returns: Screenshot as bytes
        """
        if not self.page:
            return b''
        
        try:
            screenshot = await self.page.screenshot(full_page=False)
            self.last_screenshot = screenshot
            return screenshot
        except Exception as e:
            print(f"Screenshot error: {e}")
            return b''
    
    async def get_page_text(self) -> str:
        """Extract all text from current page"""
        try:
            text = await self.page.evaluate('document.body.innerText')
            return text
        except:
            return ""
    
    async def get_page_html(self) -> str:
        """Get page HTML"""
        try:
            html = await self.page.content()
            return html
        except:
            return ""
    
    async def execute_javascript(self, script: str) -> any:
        """Execute custom JavaScript"""
        try:
            result = await self.page.evaluate(script)
            return result
        except Exception as e:
            return None
    
    async def find_elements(self, selector: str) -> list:
        """Find all matching elements"""
        try:
            elements = await self.page.query_selector_all(selector)
            return elements
        except:
            return []
    
    async def close(self):
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("Browser closed")
