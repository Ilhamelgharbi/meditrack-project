# tools/image_analysis.py
"""
Cloud-Based Image Analysis Tool - Deployment Ready

Supported Providers (Online APIs):
- Groq Vision API: Fast, uses existing GROQ_API_KEY (if available)
- OpenAI GPT-4 Vision: Premium quality image understanding
- Replicate: Various vision models via API

No Local Processing - 100% Cloud-Based:
- No model downloads (no 605MB CLIP models!)
- No GPU/CPU intensive processing
- Lightweight and scalable
- Perfect for serverless/container deployment
"""

import logging
import sys
import base64
from typing import Dict, Any
from pathlib import Path
from langchain.tools import tool, ToolRuntime

# Add parent directory to path for config import when running standalone

from app.config.settings import settings

logger = logging.getLogger(__name__)


def _encode_image_to_base64(image_path: Path) -> str:
    """
    Encode image to base64 for API transmission.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Base64 encoded image string
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


@tool("identify_pill", description="Identify a pill from an image using cloud vision API. Provide image path. Returns pill description and characteristics.")
def identify_pill(runtime: ToolRuntime, image_path: str, provider: str = "groq") -> Dict[str, Any]:
    """
    Identify a pill from an image using cloud vision APIs.
    
    Perfect for deployment: No local models, no GPU needed, pure cloud processing.
    
    Args:
        runtime: Tool runtime context
        image_path: Path to the pill image
        provider: API provider - "groq" (default) or "openai"
    
    Returns:
        Dict with pill identification results
    """
    # Check API key
    if provider == "groq" and not settings.GROQ_API_KEY:
        return {
            "error": "Groq API key not configured",
            "message": "Set GROQ_API_KEY in .env file",
            "alternative": "Use provider='openai' with OpenAI API key"
        }
    
    try:
        # Validate image path
        img_path = Path(image_path)
        if not img_path.exists():
            return {
                "error": "Image file not found",
                "path": image_path
            }
        
        if img_path.suffix.lower() not in settings.ALLOWED_IMAGE_EXTENSIONS:
            return {
                "error": "Invalid image format",
                "allowed_formats": settings.ALLOWED_IMAGE_EXTENSIONS,
                "received": img_path.suffix
            }
        
        # Use Groq Vision API (if available)
        if provider == "groq":
            # Check if Groq supports vision
            try:
                from groq import Groq
                client = Groq(api_key=settings.GROQ_API_KEY)
                
                # Encode image
                base64_image = _encode_image_to_base64(img_path)
                
                # Call Groq vision API
                response = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",  # Updated Groq vision model
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this pill image. Describe: 1) Shape (round/oval/capsule), 2) Color, 3) Size estimate, 4) Any markings or imprints, 5) Type (tablet/capsule/gel). Be specific and concise."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }],
                    max_tokens=300
                )
                
                analysis = response.choices[0].message.content
                
                return {
                    "success": True,
                    "image_path": str(img_path),
                    "provider": "Groq Vision API",
                    "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                    "analysis": analysis,
                    "disclaimer": "AI-based identification. Always verify with a pharmacist or healthcare provider."
                }
                
            except Exception as e:
                logger.error(f"Groq vision error: {e}")
                return {
                    "error": "Groq vision not available",
                    "details": str(e),
                    "fallback": "Try provider='openai' or use a specialized pill identification service"
                }
        
        else:
            return {
                "error": f"Provider '{provider}' not implemented yet",
                "supported": ["groq"],
                "note": "OpenAI vision support coming soon"
            }
        
    except Exception as e:
        logger.error(f"Pill identification error: {e}")
        return {
            "error": str(e),
            "image_path": image_path
        }


@tool("analyze_medical_image", description="Analyze medical images using cloud vision API. Provide image path and query about what to analyze.")
def analyze_medical_image(runtime: ToolRuntime, image_path: str, query: str = "general medical condition") -> Dict[str, Any]:
    """
    Analyze medical images using cloud vision APIs.
    
    Perfect for deployment: No local models, pure cloud processing.
    
    Args:
        runtime: Tool runtime context
        image_path: Path to the medical image
        query: What to analyze (e.g., "skin rash", "wound", "x-ray findings")
    
    Returns:
        Dict with image analysis results
    """
    if not settings.GROQ_API_KEY:
        return {
            "error": "Groq API key not configured",
            "message": "Set GROQ_API_KEY in .env file"
        }
    
    try:
        img_path = Path(image_path)
        if not img_path.exists():
            return {"error": "Image not found", "path": image_path}
        
        # Use Groq Vision API
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            
            # Encode image
            base64_image = _encode_image_to_base64(img_path)
            
            # Call Groq vision API with medical context
            response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": f"Analyze this medical image focusing on: {query}. Provide: 1) Visual observations, 2) Notable features, 3) General assessment. Be objective and clinical. Note: This is NOT a diagnosis."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }],
                max_tokens=400
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "success": True,
                "image_path": str(img_path),
                "query": query,
                "provider": "Groq Vision API",
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "analysis": analysis,
                "disclaimer": "AI analysis is NOT a medical diagnosis. Always consult a qualified healthcare provider for medical advice."
            }
            
        except Exception as e:
            logger.error(f"Groq vision error: {e}")
            return {
                "error": "Vision API unavailable",
                "details": str(e),
                "fallback": "Use a specialized medical imaging service or consult a healthcare provider"
            }
        
    except Exception as e:
        logger.error(f"Medical image analysis error: {e}")
        return {"error": str(e), "image_path": image_path}


# Example usage
if __name__ == "__main__":
    from unittest.mock import MagicMock
    
    print("Image Analysis Tools")
    print("=" * 60)
    
    runtime = MagicMock()
    
    # print("\n1. Pill Identification:")
    # result = identify_pill.func(runtime, "uploads/images/pill.jpg")
    # if "error" in result:
    #     print(f"   Error: {result['error']}")
    # else:
    #     print(f"   Analysis: {result['analysis']}")
    #     print(f"   Provider: {result['provider']} ({result['model']})")
    
    # print("\n2. Medical Image Analysis:")
    result2 = analyze_medical_image.func(runtime, "uploads/images/skin_rash.jpg", "skin rash")
    if "error" in result2:
        print(f"   Error: {result2['error']}")
    else:
        print(f"   Analysis: {result2['analysis']}")
        print(f"   Provider: {result2['provider']} ({result2['model']})")
