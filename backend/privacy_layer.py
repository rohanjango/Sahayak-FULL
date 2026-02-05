"""
Phase 9: Privacy Layer
Blurs sensitive information (passwords, OTPs, credit cards) before AI processes screenshots
"""

from PIL import Image, ImageFilter, ImageDraw
import io
import re
from typing import List, Tuple, Dict
import pytesseract

class PrivacyLayer:
    def __init__(self):
        self.sensitive_patterns = {
            'password': r'password|pwd|pass|secret',
            'otp': r'otp|code|verification|2fa|mfa',
            'credit_card': r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}',
            'cvv': r'cvv|cvc|security code',
            'ssn': r'\d{3}[-\s]?\d{2}[-\s]?\d{4}',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'\+?\d{1,3}?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'api_key': r'api[_-]?key|token|secret[_-]?key',
            'account_number': r'account.*\d{8,}',
        }
        
        self.blur_radius = 20
    
    async def blur_sensitive_data(self, screenshot_bytes: bytes) -> bytes:
        """
        Blur sensitive information in screenshot
        Returns: Modified screenshot with sensitive data blurred
        """
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            # Detect sensitive regions
            sensitive_regions = await self._detect_sensitive_regions(image)
            
            # Blur detected regions
            if sensitive_regions:
                image = self._apply_blur(image, sensitive_regions)
            
            # Convert back to bytes
            output = io.BytesIO()
            image.save(output, format='PNG')
            return output.getvalue()
            
        except Exception as e:
            print(f"Privacy layer error: {e}")
            # Return original screenshot if processing fails
            return screenshot_bytes
    
    async def _detect_sensitive_regions(self, image: Image) -> List[Tuple[int, int, int, int]]:
        """
        Detect regions containing sensitive information
        Returns: List of (x, y, width, height) tuples
        """
        
        regions = []
        
        try:
            # Get OCR data with bounding boxes
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            num_boxes = len(ocr_data['text'])
            
            for i in range(num_boxes):
                text = ocr_data['text'][i].lower()
                
                if not text.strip():
                    continue
                
                # Check if text matches sensitive patterns
                is_sensitive = False
                
                for pattern_name, pattern in self.sensitive_patterns.items():
                    if re.search(pattern, text, re.IGNORECASE):
                        is_sensitive = True
                        break
                
                if is_sensitive:
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    
                    # Expand region slightly
                    padding = 10
                    regions.append((
                        max(0, x - padding),
                        max(0, y - padding),
                        w + 2 * padding,
                        h + 2 * padding
                    ))
            
            # Also detect input fields that might contain sensitive data
            input_regions = self._detect_input_fields(image, ocr_data)
            regions.extend(input_regions)
            
            # Merge overlapping regions
            regions = self._merge_overlapping_regions(regions)
            
        except Exception as e:
            print(f"Sensitive region detection error: {e}")
        
        return regions
    
    def _detect_input_fields(self, image: Image, ocr_data: dict) -> List[Tuple[int, int, int, int]]:
        """
        Detect input field boxes that might contain sensitive data
        """
        
        input_regions = []
        
        # Look for password/email/security related labels
        sensitive_labels = ['password', 'email', 'card', 'cvv', 'ssn', 'otp', 'code', 'pin']
        
        num_boxes = len(ocr_data['text'])
        
        for i in range(num_boxes):
            text = ocr_data['text'][i].lower()
            
            if any(label in text for label in sensitive_labels):
                # Blur area below/next to the label (where input field would be)
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]
                
                # Create region for potential input field
                # Usually below or to the right of label
                input_regions.append((
                    x,
                    y + h,
                    w * 2,  # Wider to cover input field
                    h * 2   # Taller to cover input field
                ))
        
        return input_regions
    
    def _merge_overlapping_regions(self, regions: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        Merge overlapping bounding boxes
        """
        
        if not regions:
            return []
        
        merged = []
        sorted_regions = sorted(regions, key=lambda r: (r[0], r[1]))
        
        current = list(sorted_regions[0])
        
        for region in sorted_regions[1:]:
            x, y, w, h = region
            
            # Check if regions overlap
            if (x < current[0] + current[2] and 
                y < current[1] + current[3]):
                # Merge regions
                right = max(current[0] + current[2], x + w)
                bottom = max(current[1] + current[3], y + h)
                current[0] = min(current[0], x)
                current[1] = min(current[1], y)
                current[2] = right - current[0]
                current[3] = bottom - current[1]
            else:
                merged.append(tuple(current))
                current = list(region)
        
        merged.append(tuple(current))
        return merged
    
    def _apply_blur(self, image: Image, regions: List[Tuple[int, int, int, int]]) -> Image:
        """
        Apply blur to specified regions
        """
        
        img_copy = image.copy()
        
        for x, y, w, h in regions:
            # Extract region
            region = img_copy.crop((x, y, x + w, y + h))
            
            # Apply strong blur
            blurred_region = region.filter(ImageFilter.GaussianBlur(radius=self.blur_radius))
            
            # Paste back
            img_copy.paste(blurred_region, (x, y))
            
            # Optionally add privacy indicator (black box)
            # draw = ImageDraw.Draw(img_copy)
            # draw.rectangle([x, y, x+w, y+h], fill='black')
        
        return img_copy
    
    async def sanitize_text(self, text: str) -> str:
        """
        Remove sensitive information from text
        """
        
        sanitized = text
        
        # Replace credit card numbers
        sanitized = re.sub(self.sensitive_patterns['credit_card'], '[CARD REDACTED]', sanitized)
        
        # Replace SSNs
        sanitized = re.sub(self.sensitive_patterns['ssn'], '[SSN REDACTED]', sanitized)
        
        # Replace emails
        sanitized = re.sub(self.sensitive_patterns['email'], '[EMAIL REDACTED]', sanitized)
        
        # Replace phone numbers
        sanitized = re.sub(self.sensitive_patterns['phone'], '[PHONE REDACTED]', sanitized)
        
        return sanitized
    
    def is_sensitive_field(self, field_name: str) -> bool:
        """
        Check if a field name indicates sensitive data
        """
        
        field_lower = field_name.lower()
        
        sensitive_keywords = [
            'password', 'pwd', 'pass', 'secret',
            'otp', 'code', '2fa', 'mfa',
            'card', 'cvv', 'cvc',
            'ssn', 'social',
            'pin', 'token', 'key'
        ]
        
        return any(keyword in field_lower for keyword in sensitive_keywords)
    
    async def mask_value(self, value: str, field_type: str = 'general') -> str:
        """
        Mask sensitive values for storage
        """
        
        if not value:
            return value
        
        if field_type in ['password', 'pin', 'cvv']:
            return '*' * len(value)
        
        if field_type == 'email':
            if '@' in value:
                local, domain = value.split('@')
                return f"{local[:2]}***@{domain}"
            return value
        
        if field_type == 'card':
            if len(value) >= 4:
                return f"****-****-****-{value[-4:]}"
            return value
        
        if field_type == 'phone':
            if len(value) >= 4:
                return f"***-***-{value[-4:]}"
            return value
        
        return value
