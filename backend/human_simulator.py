"""
Phase 8: Human-Like Behavior Simulation
Adds random delays and varied mouse movements to avoid bot detection
"""

import random
import asyncio
from typing import Tuple

class HumanSimulator:
    def __init__(self):
        self.min_delay = 0.3
        self.max_delay = 1.5
        self.typing_delay_min = 0.05
        self.typing_delay_max = 0.15
    
    async def random_delay(self, min_seconds: float = None, max_seconds: float = None):
        """
        Add random human-like delay between actions
        """
        min_s = min_seconds or self.min_delay
        max_s = max_seconds or self.max_delay
        
        delay = random.uniform(min_s, max_s)
        await asyncio.sleep(delay)
    
    async def typing_delay(self):
        """
        Random delay between keystrokes to simulate human typing
        """
        delay = random.uniform(self.typing_delay_min, self.typing_delay_max)
        await asyncio.sleep(delay)
    
    def generate_mouse_path(self, start_x: int, start_y: int, end_x: int, end_y: int) -> list:
        """
        Generate realistic mouse movement path with bezier curve
        Returns list of (x, y) coordinates
        """
        
        # Number of intermediate points
        num_points = random.randint(10, 20)
        
        # Generate control points for bezier curve
        mid_x = (start_x + end_x) / 2 + random.randint(-50, 50)
        mid_y = (start_y + end_y) / 2 + random.randint(-50, 50)
        
        path = []
        
        for i in range(num_points + 1):
            t = i / num_points
            
            # Quadratic bezier curve
            x = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * mid_x + t ** 2 * end_x
            y = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * mid_y + t ** 2 * end_y
            
            # Add slight randomness
            x += random.uniform(-2, 2)
            y += random.uniform(-2, 2)
            
            path.append((int(x), int(y)))
        
        return path
    
    async def human_like_click(self, page, selector: str):
        """
        Perform a click with human-like mouse movement
        """
        try:
            # Get element bounding box
            element = await page.query_selector(selector)
            if not element:
                return False
            
            box = await element.bounding_box()
            if not box:
                return False
            
            # Calculate click position (slightly randomized within element)
            click_x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
            click_y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)
            
            # Move mouse to element with human-like path
            await page.mouse.move(click_x, click_y)
            
            # Small delay before click
            await self.random_delay(0.1, 0.3)
            
            # Click
            await page.mouse.click(click_x, click_y)
            
            return True
            
        except Exception as e:
            print(f"Human-like click error: {e}")
            return False
    
    async def human_like_typing(self, page, selector: str, text: str):
        """
        Type text with human-like speed and occasional mistakes
        """
        try:
            # Focus on element
            await page.focus(selector)
            await self.random_delay(0.2, 0.5)
            
            # Type character by character with random delays
            for i, char in enumerate(text):
                # Occasionally make a "mistake" and correct it (10% chance)
                if random.random() < 0.1 and i > 0:
                    # Type wrong character
                    wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    await page.keyboard.type(wrong_char)
                    await self.typing_delay()
                    
                    # Delete it
                    await page.keyboard.press('Backspace')
                    await self.typing_delay()
                
                # Type correct character
                await page.keyboard.type(char)
                
                # Random typing speed
                await self.typing_delay()
                
                # Occasional longer pause (like thinking)
                if random.random() < 0.05:
                    await self.random_delay(0.5, 1.0)
            
            return True
            
        except Exception as e:
            print(f"Human-like typing error: {e}")
            return False
    
    async def random_mouse_movement(self, page):
        """
        Perform random mouse movements to simulate human behavior
        """
        try:
            # Get viewport size
            viewport = page.viewport_size
            width = viewport['width']
            height = viewport['height']
            
            # Random starting position
            start_x = random.randint(100, width - 100)
            start_y = random.randint(100, height - 100)
            
            # Random ending position
            end_x = random.randint(100, width - 100)
            end_y = random.randint(100, height - 100)
            
            # Generate path
            path = self.generate_mouse_path(start_x, start_y, end_x, end_y)
            
            # Move mouse along path
            for x, y in path:
                await page.mouse.move(x, y)
                await asyncio.sleep(0.01)
            
        except Exception as e:
            print(f"Random mouse movement error: {e}")
    
    async def simulate_reading(self, page):
        """
        Simulate human reading behavior with scrolling and pauses
        """
        try:
            # Random scroll pattern
            scroll_count = random.randint(2, 5)
            
            for _ in range(scroll_count):
                # Scroll down
                await page.evaluate('window.scrollBy(0, window.innerHeight * 0.7)')
                
                # Pause to "read"
                await self.random_delay(1.0, 3.0)
            
            # Sometimes scroll back up
            if random.random() < 0.3:
                await page.evaluate('window.scrollBy(0, -window.innerHeight * 0.5)')
                await self.random_delay(0.5, 1.5)
            
        except Exception as e:
            print(f"Simulate reading error: {e}")
    
    def get_random_user_agent(self) -> str:
        """
        Return a random realistic user agent
        """
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        return random.choice(user_agents)
    
    def should_add_random_action(self) -> bool:
        """
        Decide whether to add random action (20% chance)
        """
        return random.random() < 0.2
