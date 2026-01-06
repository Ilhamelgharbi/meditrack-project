"""
Pill Identification Pipeline

Complete pill identification system using:
- CLIP embeddings for initial retrieval
- Vision API for detailed comparison and ranking
- FDA API for drug information

Architecture:
1. Vector similarity search (FAISS)
2. Vision-based reranking (Groq API)
3. FDA information retrieval
4. Response formatting
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from typing import Dict, Any, List, Tuple
import numpy as np
import faiss
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

# Local imports
from app.config.settings import settings
from tools.fda_api import get_drug_info
from tools.image_analysis import _encode_image_to_base64

logger = logging.getLogger(__name__)

# ==================================================
# CONFIGURATION
# ==================================================
# Use absolute paths based on this file's location
_BASE_DIR = Path(__file__).parent.parent  # app/agent/
VECTORSTORE_DIR = _BASE_DIR / "vectorstore"
INDEX_PATH = VECTORSTORE_DIR / "pill_images.faiss"
META_PATH = VECTORSTORE_DIR / "pill_metadata.npy"
IMAGE_FOLDER = _BASE_DIR / "data" / "archive" / "ePillID_data" / "classification_data" / "segmented_nih_pills_224"

CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
TOP_K_INITIAL = 5  # Initial retrieval candidates
TOP_K_FINAL = 2     # After vision reranking

# ==================================================
# GLOBAL COMPONENTS (lazy loaded)
# ==================================================
_clip_model = None
_clip_processor = None
_faiss_index = None
_metadata = None

def _load_components():
    """Lazy load CLIP model, FAISS index, and metadata."""
    global _clip_model, _clip_processor, _faiss_index, _metadata

    if _clip_model is None:
        logger.info("Loading CLIP model...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _clip_model = CLIPModel.from_pretrained(CLIP_MODEL_NAME).to(device)
        _clip_processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
        logger.info(f"CLIP model loaded on {device}")

    if _faiss_index is None:
        logger.info(f"Loading FAISS index from: {INDEX_PATH}")
        _faiss_index = faiss.read_index(str(INDEX_PATH))
        _metadata = np.load(str(META_PATH), allow_pickle=True)
        logger.info(f"Loaded {_faiss_index.ntotal} pill embeddings")

# ==================================================
# IMAGE EMBEDDING
# ==================================================
def embed_image(image_path: str) -> np.ndarray:
    """Generate CLIP embedding for an image."""
    _load_components()

    img = Image.open(image_path).convert("RGB").resize((224, 224))
    inputs = _clip_processor(images=img, return_tensors="pt")

    device = next(_clip_model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        features = _clip_model.get_image_features(**inputs)

    return features.cpu().numpy().astype("float32").flatten()

# ==================================================
# INITIAL RETRIEVAL
# ==================================================
def retrieve_similar_pills(query_embedding: np.ndarray, top_k: int = TOP_K_INITIAL) -> List[Tuple[int, float, Dict]]:
    """
    Retrieve similar pills using FAISS.

    Returns:
        List of (index, distance, metadata) tuples
    """
    _load_components()

    query_embedding = query_embedding.reshape(1, -1)
    distances, indices = _faiss_index.search(query_embedding, top_k)

    results = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx != -1:  # Valid result
            results.append((idx, dist, _metadata[idx]))

    return results

# ==================================================
# VISION-BASED COMPARISON
# ==================================================
def compare_pills_vision(input_image_path: str, candidate_image_path: str) -> Dict[str, Any]:
    """
    Compare two pill images using vision API.

    Returns:
        Dict with similarity scores and analysis
    """
    if not settings.GROQ_API_KEY:
        return {"error": "Groq API key not configured"}

    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)

        # Encode both images
        input_b64 = _encode_image_to_base64(Path(input_image_path))
        candidate_b64 = _encode_image_to_base64(Path(candidate_image_path))

        # Compare prompt
        prompt = """Compare these two pill images side by side.

Rate the similarity (0-100) for each aspect:
- Shape: How similar are the overall shapes?
- Color: How similar are the colors?
- Imprint/Markings: How similar are any text, numbers, or symbols?

Provide an overall match score (0-100) considering all aspects.
Be specific about differences and similarities.

Format your response as:
Shape similarity: [score]/100
Color similarity: [score]/100
Imprint similarity: [score]/100
Overall match: [score]/100
Brief explanation: [2-3 sentences]"""

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{input_b64}"}
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{candidate_b64}"}
                    }
                ]
            }],
            max_tokens=400
        )

        analysis = response.choices[0].message.content

        # Parse scores (simple extraction)
        scores = {
            "shape_score": 0,
            "color_score": 0,
            "imprint_score": 0,
            "overall_score": 0
        }

        lines = analysis.split('\n')
        for line in lines:
            line = line.lower().strip()
            if 'shape similarity:' in line:
                try:
                    scores["shape_score"] = int(line.split('/')[0].split(':')[1].strip())
                except: pass
            elif 'color similarity:' in line:
                try:
                    scores["color_score"] = int(line.split('/')[0].split(':')[1].strip())
                except: pass
            elif 'imprint similarity:' in line:
                try:
                    scores["imprint_score"] = int(line.split('/')[0].split(':')[1].strip())
                except: pass
            elif 'overall match:' in line:
                try:
                    scores["overall_score"] = int(line.split('/')[0].split(':')[1].strip())
                except: pass

        return {
            "success": True,
            "scores": scores,
            "analysis": analysis,
            "combined_score": sum(scores.values()) / len(scores)  # Average of all scores
        }

    except Exception as e:
        logger.error(f"Vision comparison error: {e}")
        return {"error": str(e)}

# ==================================================
# FDA INFORMATION
# ==================================================
def get_pill_fda_info(ndc_code: str) -> Dict[str, Any]:
    """Get FDA drug information for a pill by NDC."""
    try:
        drug_data = get_drug_info(ndc_code=ndc_code)

        if isinstance(drug_data, str):  # Error message
            return {"error": drug_data}

        # Create comprehensive patient information summary
        brand = drug_data.get('brand_name', 'Unknown')
        generic = drug_data.get('generic_name', 'Unknown')
        form = drug_data.get('dosage_form', 'Unknown')
        route = drug_data.get('route', ['Unknown'])
        if isinstance(route, list):
            route = ', '.join(route)
        manufacturer = drug_data.get('manufacturer', 'Unknown')
        
        # Get indications (what the drug is used for)
        indications = drug_data.get('indications_and_usage', [])
        indication_text = ""
        if indications and len(indications) > 0 and indications[0] != 'No indications found':
            indication_text = indications[0][:200].strip()  # First 200 chars
            if len(indications[0]) > 200:
                indication_text += "..."
        
        # Get key warnings (first 150 chars if available)
        warnings = drug_data.get('warnings', [])
        warning_text = ""
        if warnings and len(warnings) > 0 and warnings[0] != 'No warnings found':
            warning_text = warnings[0][:150].strip()
            if len(warnings[0]) > 150:
                warning_text += "..."
        
        # Get dosage information
        dosage_info = drug_data.get('dosage_and_administration', [])
        dosage_text = ""
        if dosage_info and len(dosage_info) > 0 and dosage_info[0] != 'No dosage info found':
            dosage_text = dosage_info[0][:150].strip()
            if len(dosage_info[0]) > 150:
                dosage_text += "..."
        
        # Get side effects information
        side_effects = drug_data.get('adverse_reactions', [])
        side_effects_text = ""
        if side_effects and len(side_effects) > 0 and side_effects[0] != 'No adverse reactions found':
            side_effects_text = side_effects[0][:150].strip()
            if len(side_effects[0]) > 150:
                side_effects_text += "..."
        
        # Build comprehensive patient summary
        summary_parts = [
            f"💊 **{brand}** ({generic})",
            f"**Form:** {form} | **Route:** {route}",
            f"**Manufacturer:** {manufacturer}",
        ]
        
        if indication_text:
            summary_parts.append(f"**What it's for:** {indication_text}")
        
        if warning_text:
            summary_parts.append(f"⚠️ **Important Warnings:** {warning_text}")
        
        if dosage_text:
            summary_parts.append(f"**How to take it:** {dosage_text}")
        
        if side_effects_text:
            summary_parts.append(f"**Possible side effects:** {side_effects_text}")
        
        summary_parts.append("_This is general information. Always follow your doctor's instructions._")
        
        summary = "\n\n".join(summary_parts)

        return {
            "success": True,
            "summary": summary,
            "details": drug_data
        }

    except Exception as e:
        logger.error(f"FDA lookup error: {e}")
        return {"error": str(e)}

# ==================================================
# MAIN PIPELINE
# ==================================================
def identify_pill(input_image_path: str) -> Dict[str, Any]:
    """
    Complete pill identification pipeline.

    Args:
        input_image_path: Path to the pill image to identify

    Returns:
        Dict with identification results
    """
    try:
        # Validate input
        if not Path(input_image_path).exists():
            return {"error": f"Input image not found: {input_image_path}"}

        logger.info(f"Starting pill identification for: {input_image_path}")

        # Step 1: Embed input image
        logger.info("Generating embedding for input image...")
        query_embedding = embed_image(input_image_path)

        # Step 2: Initial retrieval
        logger.info(f"Retrieving top {TOP_K_INITIAL} similar pills...")
        candidates = retrieve_similar_pills(query_embedding, TOP_K_INITIAL)

        if not candidates:
            return {"error": "No similar pills found in database"}

        # Step 3: Vision-based reranking
        logger.info("Reranking with vision analysis...")
        reranked = []

        for idx, dist, meta in candidates:
            candidate_path = os.path.join(IMAGE_FOLDER, meta['file'])

            if not Path(candidate_path).exists():
                logger.warning(f"Candidate image not found: {candidate_path}")
                continue

            # Compare with vision API
            comparison = compare_pills_vision(input_image_path, candidate_path)

            if "error" in comparison:
                logger.warning(f"Vision comparison failed: {comparison['error']}")
                continue

            reranked.append({
                "index": idx,
                "vector_distance": dist,
                "metadata": meta,
                "image_path": candidate_path,
                "vision_scores": comparison["scores"],
                "combined_score": comparison["combined_score"],
                "vision_analysis": comparison["analysis"]
            })

        # Sort by combined score (higher is better)
        reranked.sort(key=lambda x: x["combined_score"], reverse=True)

        # Take top candidates
        top_candidates = reranked[:TOP_K_FINAL]

        if not top_candidates:
            return {"error": "Vision analysis failed for all candidates"}

        # Step 4: Final selection and FDA lookup
        best_match = top_candidates[0]
        ndc_code = best_match["metadata"]["ndc"]

        logger.info(f"Best match NDC: {ndc_code}")
        fda_info = get_pill_fda_info(ndc_code)

        # Get FDA details (truncate long fields to avoid token limits)
        fda_details = fda_info.get("details", {}) if "success" in fda_info else {}
        
        # Create a compact FDA summary for the LLM (avoid sending full text)
        compact_fda = {
            "brand_name": fda_details.get("brand_name", "N/A"),
            "generic_name": fda_details.get("generic_name", "N/A"),
            "manufacturer": fda_details.get("manufacturer", "N/A"),
            "dosage_form": fda_details.get("dosage_form", "N/A"),
            "route": fda_details.get("route", "N/A"),
        }

        # Step 5: Format comprehensive patient response
        response = {
            "success": True,
            "input_image": input_image_path,
            "identified_pill": {
                "ndc_code": ndc_code,
                "brand_name": best_match["metadata"].get("brand", "Unknown"),
                "generic_name": best_match["metadata"].get("generic", "Unknown"),
                "confidence": round(best_match["combined_score"] / 100.0, 2),
                "identification_method": "Image similarity + FDA database verification"
            },
            "patient_information": {
                "medication_name": f"{fda_info.get('details', {}).get('brand_name', 'Unknown')} ({fda_info.get('details', {}).get('generic_name', 'Unknown')})",
                "purpose": fda_info.get('details', {}).get('indications_and_usage', ['Not available'])[0][:300] if fda_info.get('details', {}).get('indications_and_usage') else "Not available",
                "warnings": fda_info.get('details', {}).get('warnings', ['Not available'])[0][:300] if fda_info.get('details', {}).get('warnings') else "Not available",
                "dosage": fda_info.get('details', {}).get('dosage_and_administration', ['Not available'])[0][:300] if fda_info.get('details', {}).get('dosage_and_administration') else "Not available",
                "side_effects": fda_info.get('details', {}).get('adverse_reactions', ['Not available'])[0][:300] if fda_info.get('details', {}).get('adverse_reactions') else "Not available",
                "manufacturer": fda_info.get('details', {}).get('manufacturer', 'Not available'),
                "form": fda_info.get('details', {}).get('dosage_form', 'Not available')
            },
            "summary": fda_info.get("summary", "FDA information not available") if "success" in fda_info else fda_info.get("error", "FDA lookup failed"),
            "alternative_matches": [
                {
                    "ndc_code": cand["metadata"]["ndc"],
                    "brand_name": cand["metadata"].get("brand", "Unknown"),
                    "confidence": round(cand["combined_score"] / 100.0, 2)
                }
                for cand in top_candidates[1:3]
            ],
            "disclaimer": "This identification is for informational purposes only. Always consult your healthcare provider before taking any medication."
        }

        logger.info(f"Identification complete. Confidence: {response['identified_pill']['confidence']:.2f}")
        return response

    except Exception as e:
        logger.error(f"Pill identification error: {e}")
        return {"error": str(e)}

# ==================================================
# LANGCHAIN TOOL INTEGRATION
# ==================================================
from langchain.tools import tool

@tool("identify_pill_complete", description="Complete pill identification using image similarity and FDA database. Provide path to pill image.")
def identify_pill_complete(image_path: str) -> Dict[str, Any]:
    """
    LangChain tool for complete pill identification.

    Args:
        image_path: Path to pill image file

    Returns:
        Dict with identification results
    """
    return identify_pill(image_path)

# ==================================================
# STANDALONE TESTING
# ==================================================
if __name__ == "__main__":
    # Test with sample image
    test_image = "uploads/images/pill.jpg"  # Adjust path as needed

    if Path(test_image).exists():
        print("Testing pill identification...")
        result = identify_pill(test_image)

        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print("SUCCESS!")
            print(f"NDC: {result['identified_pill']['ndc_code']}")
            print(f"Confidence: {result['confidence']:.2f}")
            # print(f"Summary: {result['summary']}")
    else:
        print(f"Test image not found: {test_image}")
        print("Please provide a valid pill image path for testing.")