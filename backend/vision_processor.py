"""
Phase 4: Vision Capabilities
Integrates OCR and vision models for screen understanding
"""

import pytesseract
from PIL import Image
import io
import requests
from typing import Dict, Any
import base64
import pytesseract

#import pytesseract

# Update this line to your new path
pytesseract.pytesseract.tesseract_cmd = r'D:\tessareact\tesseract.exe'
class VisionProcessor:
    def __init__(self):
        self.hf_api_key = os.getenv("HUGGINGFACE_TOKEN")
        self.vision_model_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
        self.headers = {"Authorization": f"Bearer {self.hf_api_key}"}
        
    async def analyze_screen(self, screenshot_bytes: bytes) -> Dict[str, Any]:
        """
        Analyze screenshot using OCR and vision model
        Returns comprehensive screen analysis
        """
        
        analysis = {
            'text': '',
            'description': '',
            'elements': [],
            'page_loaded': True,
            'screen_changed': True
        }
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            # OCR Text Extraction
            ocr_text = await self._extract_text_ocr(image)
            analysis['text'] = ocr_text
            
            # Vision Model Description
            description = await self._get_image_description(screenshot_bytes)
            analysis['description'] = description
            
            # Detect UI Elements
            elements = await self._detect_elements(image, ocr_text)
            analysis['elements'] = elements
            
            # Page state detection
            analysis['page_loaded'] = self._check_page_loaded(ocr_text)
            
        except Exception as e:
            print(f"Vision analysis error: {e}")
        
        return analysis
    
    async def _extract_text_ocr(self, image: Image) -> str:
        """
        Extract text from image using Tesseract OCR
        """
        try:
            # Use Tesseract for OCR
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"OCR error: {e}")
            # Fallback: basic text extraction
            return ""
    
    async def _get_image_description(self, image_bytes: bytes) -> str:
        """
        Get image description using Hugging Face vision model
        """
        try:
            response = requests.post(
                self.vision_model_url,
                headers=self.headers,
                data=image_bytes,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '')
                return str(result)
        except Exception as e:
            print(f"Vision model error: {e}")
        
        return "Screen analysis in progress"
    
    async def _detect_elements(self, image: Image, ocr_text: str) -> list:
        """
        Detect UI elements from image and OCR text
        """
        elements = []
        
        # Extract clickable elements from OCR text
        lines = ocr_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 2:
                # Detect buttons, links, forms
                if any(keyword in line.lower() for keyword in ['button', 'click', 'submit', 'search', 'login', 'sign']):
                    elements.append({
                        'type': 'button',
                        'text': line,
                        'confidence': 0.8
                    })
                elif '@' in line or 'email' in line.lower():
                    elements.append({
                        'type': 'email_field',
                        'text': line,
                        'confidence': 0.7
                    })
                elif 'password' in line.lower():
                    elements.append({
                        'type': 'password_field',
                        'text': line,
                        'confidence': 0.9
                    })
        
        return elements
    
    def _check_page_loaded(self, text: str) -> bool:
        """
        Check if page has loaded successfully
        """
        # Simple heuristic: page loaded if there's substantial text
        return len(text.strip()) > 50
    
    async def find_element_by_text(self, screenshot_bytes: bytes, target_text: str) -> Dict:
        """
        Find element location by text using OCR with bounding boxes
        """
        try:
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            # Get OCR data with bounding boxes
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Search for target text
            for i, text in enumerate(ocr_data['text']):
                if target_text.lower() in text.lower():
                    return {
                        'found': True,
                        'x': ocr_data['left'][i],
                        'y': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i],
                        'confidence': ocr_data['conf'][i]
                    }
            
            return {'found': False}
            
        except Exception as e:
            print(f"Element search error: {e}")
            return {'found': False}
    
    async def compare_screenshots(self, screenshot1: bytes, screenshot2: bytes) -> Dict:
        """
        Compare two screenshots to detect changes
        """
        try:
            img1 = Image.open(io.BytesIO(screenshot1))
            img2 = Image.open(io.BytesIO(screenshot2))
            
            # Simple comparison using image hashing
            from PIL import ImageChops
            diff = ImageChops.difference(img1, img2)
            
            # Calculate difference percentage
            diff_pixels = sum(diff.getdata())
            total_pixels = img1.size[0] * img1.size[1] * 3
            difference_pct = (diff_pixels / total_pixels) * 100
            
            return {
                'changed': difference_pct > 1.0,  # More than 1% change
                'difference_percentage': difference_pct
            }
            
        except Exception as e:
            print(f"Screenshot comparison error: {e}")
            return {'changed': True, 'difference_percentage': 0}
