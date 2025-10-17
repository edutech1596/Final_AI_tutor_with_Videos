#!/usr/bin/env python3
"""
Clean Image Processing Service
Uses OpenAI Vision for ALL images with MathPix as fallback
"""

import base64
import io
import logging
import requests
from PIL import Image
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CleanImageService:
    """
    Simple, reliable image processing service
    - OpenAI Vision for ALL images (printed + handwritten)
    - MathPix as fallback (when API key is available)
    """
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key
        self.mathpix_api_key = None  # Not used
        
        if self.openai_api_key and self.openai_api_key.strip():
            logger.info("✅ OpenAI Vision API ready")
        else:
            logger.warning("⚠️ OpenAI API key not provided")
    
    def process_image(self, image_base64: str, processing_type: str = "comprehensive") -> Dict:
        """
        Process image using OpenAI Vision API for ALL images
        
        Args:
            image_base64: Base64 encoded image
            processing_type: Type of processing (ignored, always uses OpenAI Vision)
            
        Returns:
            Dict with analysis results
        """
        try:
            logger.info("🔍 Processing image with OpenAI Vision API (ALL images)")
            
            # Use OpenAI Vision for all images
            if self.openai_api_key:
                result = self._analyze_openai_vision(image_base64)
                if result and result.get('analysis') != 'OpenAI Vision API failed':
                    return result
                else:
                    logger.error("OpenAI Vision API failed")
                    return {"analysis": "OpenAI Vision API failed", "method": "api_error"}
            else:
                logger.error("OpenAI API key not set. Cannot process image.")
                return {
                    "extracted_text": "",
                    "math_equations": [],
                    "vision_analysis": {
                        "analysis": "Error: No OpenAI API key provided",
                        "method": "error"
                    }
                }
                
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
            return {
                "extracted_text": "",
                "math_equations": [],
                "vision_analysis": {
                    "analysis": f"Error: {str(e)}",
                    "method": "error"
                }
            }
    
    def _analyze_openai_vision(self, image_base64: str) -> Dict:
        """
        Analyze image using OpenAI Vision API
        
        Args:
            image_base64: Base64 encoded image
            
        Returns:
            Dict with OpenAI Vision analysis
        """
        logger.info("🔴 EXECUTING: OpenAI Vision API analysis (ALL images)")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this image and provide:
1. All text content (both printed and handwritten)
2. Mathematical expressions and equations
3. Geometric shapes and diagrams
4. Educational context and concepts
5. Any mathematical notation or symbols

Be thorough and accurate in your analysis."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1500
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result['choices'][0]['message']['content']
                
                # Extract text and math equations from the analysis
                extracted_text = self._extract_text_from_analysis(analysis_text)
                math_equations = self._extract_math_from_analysis(analysis_text)
                
                return {
                    "extracted_text": extracted_text,
                    "math_equations": math_equations,
                    "vision_analysis": {
                        "analysis": analysis_text,
                        "method": "openai_vision"
                    }
                }
            else:
                logger.error(f"OpenAI Vision API error: {response.status_code}")
                return {
                    "extracted_text": "",
                    "math_equations": [],
                    "vision_analysis": {
                        "analysis": f"OpenAI Vision API failed with status {response.status_code}",
                        "method": "api_error"
                    }
                }
                
        except Exception as e:
            logger.error(f"OpenAI Vision API failed: {str(e)}")
            return {
                "extracted_text": "",
                "math_equations": [],
                "vision_analysis": {
                    "analysis": f"OpenAI Vision API failed: {str(e)}",
                    "method": "error"
                }
            }
    
    def _analyze_mathpix_fallback(self, image_base64: str) -> Dict:
        """
        Fallback to MathPix API if OpenAI Vision fails
        
        Args:
            image_base64: Base64 encoded image
            
        Returns:
            Dict with MathPix analysis
        """
        if not self.mathpix_api_key:
            logger.warning("MathPix API key not available for fallback")
            return {
                "extracted_text": "",
                "math_equations": [],
                "vision_analysis": {
                    "analysis": "No fallback API available",
                    "method": "no_fallback"
                }
            }
        
        logger.info("🟡 EXECUTING: MathPix API fallback analysis")
        
        try:
            headers = {
                "app_id": "your_app_id",  # Replace with actual app ID
                "app_key": self.mathpix_api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "src": f"data:image/jpeg;base64,{image_base64}",
                "formats": ["latex", "text", "mathml"]
            }
            
            response = requests.post(
                "https://api.mathpix.com/v3/text",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "extracted_text": result.get("text", ""),
                    "math_equations": [result.get("latex", "")],
                    "vision_analysis": {
                        "analysis": f"MathPix analysis: {result.get('text', 'No text extracted')}",
                        "method": "mathpix_fallback"
                    }
                }
            else:
                logger.error(f"MathPix API error: {response.status_code}")
                return {
                    "extracted_text": "",
                    "math_equations": [],
                    "vision_analysis": {
                        "analysis": f"MathPix API failed with status {response.status_code}",
                        "method": "mathpix_error"
                    }
                }
                
        except Exception as e:
            logger.error(f"MathPix API failed: {str(e)}")
            return {
                "extracted_text": "",
                "math_equations": [],
                "vision_analysis": {
                    "analysis": f"MathPix API failed: {str(e)}",
                    "method": "mathpix_error"
                }
            }
    
    def _extract_text_from_analysis(self, analysis_text: str) -> str:
        """Extract plain text from OpenAI analysis"""
        # Simple text extraction - could be improved with more sophisticated parsing
        lines = analysis_text.split('\n')
        text_lines = []
        for line in lines:
            if line.strip() and not line.startswith('**') and not line.startswith('#'):
                text_lines.append(line.strip())
        return ' '.join(text_lines[:5])  # Limit to first 5 lines
    
    def _extract_math_from_analysis(self, analysis_text: str) -> list:
        """Extract mathematical expressions from OpenAI analysis"""
        # Simple math extraction - look for common math patterns
        math_expressions = []
        lines = analysis_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(symbol in line for symbol in ['=', '+', '-', '*', '/', '^', '²', '³', '√', '∫', '∑']):
                math_expressions.append(line)
        
        return math_expressions[:3]  # Limit to first 3 expressions
    
    def get_image_context(self, image_base64: str) -> str:
        """
        Get context from image for LLM integration
        
        Args:
            image_base64: Base64 encoded image
            
        Returns:
            str: Context string for LLM
        """
        try:
            result = self.process_image(image_base64, "comprehensive")
            
            context_parts = []
            
            # Add extracted text
            if result["extracted_text"]:
                context_parts.append(f"📝 Text in image: {result['extracted_text']}")
            
            # Add math equations
            if result["math_equations"]:
                context_parts.append(f"🧮 Math equations: {', '.join(result['math_equations'])}")
            
            # Add vision analysis
            if result["vision_analysis"].get("analysis"):
                context_parts.append(f"👁️ Image analysis: {result['vision_analysis']['analysis']}")
            
            return "\n".join(context_parts) if context_parts else "📷 Image uploaded (processing failed)"
            
        except Exception as e:
            logger.error(f"Context extraction failed: {str(e)}")
            return "📷 Image uploaded (processing failed)"


# Global instance - created in app.py with proper API key
