from playwright.async_api import async_playwright, Browser, Page, ElementHandle
import asyncio
import base64
from typing import Optional, List, Dict, Tuple
import random
from PIL import Image, ImageDraw, ImageFilter
import io
import pytesseract

class BrowserController:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context = None
        
    async def start(self):
        """Start browser instance"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
    async def stop(self):
        """Stop browser instance"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def navigate(self, url: str) -> Dict:
        """Navigate to URL with human-like delay"""
        await self._human_delay()
        try:
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            return {"success": True, "url": self.page.url}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def click_element(self, selector: str, use_fallback: bool = True) -> Dict:
        """Click element with self-healing selector capability"""
        await self._human_delay()
        
        # Try multiple strategies
        strategies = [
            ('css', selector),
            ('text', selector),
            ('xpath', f"//*[contains(text(), '{selector}')]"),
        ]
        
        for strategy_type, strategy_selector in strategies:
            try:
                if strategy_type == 'css':
                    element = await self.page.query_selector(strategy_selector)
                elif strategy_type == 'text':
                    element = await self.page.get_by_text(strategy_selector).first.element_handle()
                elif strategy_type == 'xpath':
                    element = await self.page.query_selector(f"xpath={strategy_selector}")
                
                if element:
                    # Human-like mouse movement
                    box = await element.bounding_box()
                    if box:
                        x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
                        y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)
                        await self.page.mouse.move(x, y, steps=random.randint(10, 30))
                        await self._human_delay(0.1, 0.3)
                        await element.click()
                        return {"success": True, "strategy": strategy_type}
            except Exception as e:
                continue
        
        # If all strategies fail, try OCR-based clicking
        if use_fallback:
            return await self._click_via_ocr(selector)
        
        return {"success": False, "error": "Element not found with any strategy"}
    
    async def type_text(self, selector: str, text: str, is_sensitive: bool = False) -> Dict:
        """Type text with human-like behavior"""
        await self._human_delay()
        
        try:
            element = await self.page.query_selector(selector)
            if not element:
                # Try text-based selector
                element = await self.page.get_by_label(selector).first.element_handle()
            
            if element:
                await element.click()
                await self._human_delay(0.1, 0.3)
                
                # Type character by character with random delays
                for char in text:
                    await self.page.keyboard.type(char)
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                
                return {"success": True, "is_sensitive": is_sensitive}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def take_screenshot(self, blur_sensitive: bool = True) -> str:
        """Take screenshot with optional sensitive data blurring"""
        screenshot_bytes = await self.page.screenshot(full_page=False)
        
        if blur_sensitive:
            screenshot_bytes = await self._blur_sensitive_areas(screenshot_bytes)
        
        return base64.b64encode(screenshot_bytes).decode('utf-8')
    
    async def extract_text_ocr(self, screenshot_base64: str = None) -> str:
        """Extract text from screenshot using OCR"""
        if not screenshot_base64:
            screenshot_base64 = await self.take_screenshot(blur_sensitive=False)
        
        image_bytes = base64.b64decode(screenshot_base64)
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        return text
    
    async def get_page_info(self) -> Dict:
        """Get current page information"""
        return {
            "url": self.page.url,
            "title": await self.page.title(),
        }
    
    async def _human_delay(self, min_delay: float = 0.5, max_delay: float = 2.0):
        """Add human-like random delay"""
        await asyncio.sleep(random.uniform(min_delay, max_delay))
    
    async def _blur_sensitive_areas(self, screenshot_bytes: bytes) -> bytes:
        """Blur sensitive areas (password fields, OTP inputs) in screenshot"""
        try:
            # Convert to PIL Image
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            # Get all input elements
            inputs = await self.page.query_selector_all('input[type="password"], input[name*="otp"], input[name*="pin"], input[autocomplete="one-time-code"]')
            
            draw = ImageDraw.Draw(image)
            
            for input_elem in inputs:
                box = await input_elem.bounding_box()
                if box:
                    # Create blurred region
                    region = image.crop((box['x'], box['y'], box['x'] + box['width'], box['y'] + box['height']))
                    blurred = region.filter(ImageFilter.GaussianBlur(radius=20))
                    image.paste(blurred, (int(box['x']), int(box['y'])))
            
            # Convert back to bytes
            output = io.BytesIO()
            image.save(output, format='PNG')
            return output.getvalue()
        except Exception as e:
            # If blurring fails, return original
            return screenshot_bytes
    
    async def _click_via_ocr(self, text: str) -> Dict:
        """Fallback: Click element by finding text via OCR"""
        try:
            screenshot = await self.take_screenshot(blur_sensitive=False)
            image_bytes = base64.b64decode(screenshot)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Get text positions from OCR
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            for i, word in enumerate(data['text']):
                if text.lower() in word.lower():
                    x = data['left'][i] + data['width'][i] / 2
                    y = data['top'][i] + data['height'][i] / 2
                    await self.page.mouse.click(x, y)
                    return {"success": True, "strategy": "ocr"}
            
            return {"success": False, "error": "Text not found via OCR"}
        except Exception as e:
            return {"success": False, "error": f"OCR failed: {str(e)}"}