"""
Phase 6: Self-Healing Selectors
Finds alternative element selection methods when primary approach fails
"""

from typing import Dict, Optional, List
import re

class SelectorHealer:
    def __init__(self):
        self.selector_strategies = [
            'css_selector',
            'xpath',
            'text_match',
            'placeholder',
            'aria_label',
            'id_pattern',
            'class_pattern',
            'ocr_location'
        ]
    
    async def find_alternative(self, original_selector: str, screenshot: bytes = None) -> Optional[str]:
        """
        Find alternative selector when original fails
        Returns: New selector or None
        """
        
        alternatives = []
        
        # Strategy 1: Try different CSS selectors
        css_alternatives = self._generate_css_alternatives(original_selector)
        alternatives.extend(css_alternatives)
        
        # Strategy 2: Try XPath
        xpath_alternative = self._css_to_xpath(original_selector)
        if xpath_alternative:
            alternatives.append(xpath_alternative)
        
        # Strategy 3: Try text-based selectors
        text_alternatives = self._generate_text_selectors(original_selector)
        alternatives.extend(text_alternatives)
        
        # Strategy 4: Try attribute-based selectors
        attr_alternatives = self._generate_attribute_selectors(original_selector)
        alternatives.extend(attr_alternatives)
        
        # Return first alternative (in real implementation, would test each)
        return alternatives[0] if alternatives else None
    
    def _generate_css_alternatives(self, selector: str) -> List[str]:
        """Generate alternative CSS selectors"""
        alternatives = []
        
        # If selector has ID, try class variations
        if '#' in selector:
            # Extract ID and create variations
            id_part = selector.split('#')[1].split('.')[0].split('[')[0]
            alternatives.append(f'[id="{id_part}"]')
            alternatives.append(f'[id*="{id_part}"]')
        
        # If selector has class, try variations
        if '.' in selector:
            class_part = selector.split('.')[1].split('[')[0].split(':')[0]
            alternatives.append(f'[class*="{class_part}"]')
            alternatives.append(f'.{class_part}')
        
        # If selector has attribute
        if '[' in selector:
            # Extract attribute
            attr_match = re.search(r'\[([^=]+)=?"?([^"\]]+)"?\]', selector)
            if attr_match:
                attr_name, attr_value = attr_match.groups()
                alternatives.append(f'[{attr_name}*="{attr_value}"]')
                alternatives.append(f'*[{attr_name}="{attr_value}"]')
        
        # Generic fallback based on tag
        tag_match = re.match(r'^([a-z]+)', selector)
        if tag_match:
            tag = tag_match.group(1)
            alternatives.append(tag)
        
        return alternatives
    
    def _css_to_xpath(self, css_selector: str) -> Optional[str]:
        """Convert CSS selector to XPath"""
        
        # Simple CSS to XPath conversion
        xpath = css_selector
        
        # Replace # with @id
        if '#' in xpath:
            xpath = xpath.replace('#', '[@id="') + '"]'
        
        # Replace . with contains(@class)
        if '.' in css_selector and '#' not in css_selector:
            parts = css_selector.split('.')
            if len(parts) == 2:
                tag, class_name = parts
                xpath = f'//{tag or "*"}[contains(@class, "{class_name}")]'
        
        # If no special characters, just use tag
        if xpath == css_selector and not any(c in xpath for c in ['#', '.', '[', ':']):
            xpath = f'//{css_selector}'
        
        return xpath if xpath != css_selector else None
    
    def _generate_text_selectors(self, selector: str) -> List[str]:
        """Generate text-based selectors"""
        alternatives = []
        
        # Extract potential text from selector
        text_match = re.search(r'text[=*]"([^"]+)"', selector)
        if text_match:
            text = text_match.group(1)
            alternatives.append(f'text="{text}"')
            alternatives.append(f'text*="{text}"')
            alternatives.append(f'//*[contains(text(), "{text}")]')
        
        # Common button/link texts
        common_texts = ['submit', 'login', 'search', 'click', 'button', 'sign in']
        for text in common_texts:
            if text in selector.lower():
                alternatives.append(f'text="{text}"')
                alternatives.append(f'//button[contains(text(), "{text}")]')
        
        return alternatives
    
    def _generate_attribute_selectors(self, selector: str) -> List[str]:
        """Generate attribute-based selectors"""
        alternatives = []
        
        # Common form attributes
        if 'input' in selector.lower() or 'textarea' in selector.lower():
            alternatives.extend([
                '[name]',
                '[placeholder]',
                '[aria-label]',
                '[type="text"]',
                '[type="email"]',
                '[type="password"]',
                'input:visible',
                'textarea:visible'
            ])
        
        # Button alternatives
        if 'button' in selector.lower():
            alternatives.extend([
                'button[type="submit"]',
                'input[type="submit"]',
                '[role="button"]',
                'button:visible'
            ])
        
        # Link alternatives
        if 'a' in selector or 'link' in selector.lower():
            alternatives.extend([
                'a[href]',
                '[role="link"]',
                'a:visible'
            ])
        
        return alternatives
    
    async def heal_selector_with_ocr(self, target_text: str, ocr_result: Dict) -> Optional[str]:
        """
        Use OCR results to generate selector for element with specific text
        """
        if ocr_result.get('found'):
            # Generate click coordinates selector
            x = ocr_result['x'] + ocr_result['width'] // 2
            y = ocr_result['y'] + ocr_result['height'] // 2
            
            # Return special coordinate-based selector
            return f'coords:{x},{y}'
        
        return None
    
    def get_fallback_selectors(self, element_type: str) -> List[str]:
        """
        Get fallback selectors for common element types
        """
        fallbacks = {
            'search_box': [
                'input[type="search"]',
                'input[name*="search"]',
                'input[placeholder*="search"]',
                '[aria-label*="search"]',
                'input[id*="search"]'
            ],
            'login_button': [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("login")',
                'button:has-text("sign in")',
                '[aria-label*="login"]'
            ],
            'email_field': [
                'input[type="email"]',
                'input[name*="email"]',
                'input[placeholder*="email"]',
                '[aria-label*="email"]'
            ],
            'password_field': [
                'input[type="password"]',
                'input[name*="password"]',
                '[aria-label*="password"]'
            ]
        }
        
        return fallbacks.get(element_type, [])
