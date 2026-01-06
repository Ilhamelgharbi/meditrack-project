# app/agent/tools/fda_drug_tool.py
"""
FDA Drug Information Tool - Searches FDA database for medication information.
Provides patient-friendly summaries about drugs including uses, warnings, and side effects.
"""

import requests
from langchain_core.tools import tool
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def _search_fda_by_name(drug_name: str) -> dict:
    """Search FDA database by drug name."""
    try:
        # Search in drug labels (most comprehensive info)
        label_url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{drug_name}+openfda.generic_name:{drug_name}&limit=1"
        response = requests.get(label_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                return {"source": "label", "data": data["results"][0]}
        
        # Fallback: broader search
        fallback_url = f"https://api.fda.gov/drug/label.json?search={drug_name}&limit=1"
        response = requests.get(fallback_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                return {"source": "label", "data": data["results"][0]}
        
        return {"error": f"No FDA data found for: {drug_name}"}
        
    except Exception as e:
        logger.error(f"FDA API error: {e}")
        return {"error": f"FDA API error: {str(e)}"}


def _search_fda_by_ndc(ndc_code: str) -> dict:
    """Search FDA database by NDC code."""
    try:
        ndc_url = f"https://api.fda.gov/drug/ndc.json?search=product_ndc:{ndc_code}&limit=1"
        response = requests.get(ndc_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                ndc_info = data["results"][0]
                # Get additional label info using brand name
                brand_name = ndc_info.get("brand_name", "")
                if brand_name:
                    label_data = _search_fda_by_name(brand_name)
                    return {
                        "source": "ndc+label",
                        "ndc_data": ndc_info,
                        "label_data": label_data.get("data", {})
                    }
                return {"source": "ndc", "ndc_data": ndc_info}
        
        return {"error": f"No FDA data found for NDC: {ndc_code}"}
        
    except Exception as e:
        logger.error(f"FDA NDC API error: {e}")
        return {"error": f"FDA API error: {str(e)}"}


def _extract_first_paragraph(text_list: list, max_length: int = 300) -> str:
    """Extract and truncate first paragraph from FDA text array."""
    if not text_list or not isinstance(text_list, list):
        return "Not available"
    
    text = text_list[0] if text_list else ""
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text


def _format_patient_summary(raw_data: dict) -> str:
    """Format FDA data into a patient-friendly summary."""
    
    if "error" in raw_data:
        return raw_data["error"]
    
    label_data = raw_data.get("label_data", raw_data.get("data", {}))
    ndc_data = raw_data.get("ndc_data", {})
    openfda = label_data.get("openfda", {})
    
    # Get basic drug info
    brand_name = (
        ndc_data.get("brand_name") or 
        (openfda.get("brand_name", [""])[0] if openfda.get("brand_name") else "") or
        "Unknown"
    )
    
    generic_name = (
        ndc_data.get("generic_name") or
        (openfda.get("generic_name", [""])[0] if openfda.get("generic_name") else "") or
        "Unknown"
    )
    
    manufacturer = (
        ndc_data.get("labeler_name") or
        (openfda.get("manufacturer_name", [""])[0] if openfda.get("manufacturer_name") else "") or
        "Unknown"
    )
    
    dosage_form = ndc_data.get("dosage_form", "Unknown")
    route = ndc_data.get("route", ["Unknown"])
    if isinstance(route, list):
        route = ", ".join(route) if route else "Unknown"
    
    # Get label information
    purpose = _extract_first_paragraph(label_data.get("purpose", label_data.get("indications_and_usage", [])))
    warnings = _extract_first_paragraph(label_data.get("warnings", label_data.get("warnings_and_cautions", [])))
    dosage = _extract_first_paragraph(label_data.get("dosage_and_administration", []))
    side_effects = _extract_first_paragraph(label_data.get("adverse_reactions", []))
    
    # Build patient-friendly summary
    summary = f"""💊 **{brand_name}** ({generic_name})

**Manufacturer:** {manufacturer}
**Form:** {dosage_form} | **Route:** {route}

**What it's for:**
{purpose}

**⚠️ Important Warnings:**
{warnings}

**How to take it:**
{dosage}

**Possible side effects:**
{side_effects}

_This is general information. Always follow your doctor's instructions._"""
    
    return summary


@tool("fda_drug_lookup", description="""
Search the FDA database for drug/medication information.

Use this tool when a patient asks about:
- What a medication is used for (indications)
- Side effects or adverse reactions
- Warnings or precautions for a medication
- How to take a medication (dosage instructions)
- Drug manufacturer information
- General information about any medication by name or NDC code

Args:
    query: Drug name (e.g., "Lisinopril", "Metformin", "Aspirin") OR 
           NDC code (e.g., "0002-3250", "12345-678-90")

Returns:
    Patient-friendly summary including uses, warnings, dosage, and side effects.

Examples:
    - "Lisinopril" - Blood pressure medication lookup
    - "Metformin" - Diabetes medication lookup
    - "0002-3250" - Search by NDC code
""")
def fda_drug_lookup(query: str) -> str:
    """Search FDA database for drug information."""
    query = query.strip()
    
    if not query:
        return "Please provide a drug name or NDC code to search."
    
    logger.info(f"FDA Drug Lookup: {query}")
    
    # Determine if query is NDC code
    is_ndc = bool(
        query.replace("-", "").isdigit() or 
        (len(query.split("-")) >= 2 and all(part.isdigit() for part in query.split("-")))
    )
    
    if is_ndc:
        raw_data = _search_fda_by_ndc(query)
    else:
        raw_data = _search_fda_by_name(query)
    
    return _format_patient_summary(raw_data)
