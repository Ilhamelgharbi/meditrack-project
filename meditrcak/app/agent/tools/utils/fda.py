import requests

def get_drug_info(ndc_code=None, drug_name=None):
    # ---------------------------
    # 1. Get basic info from NDC
    # ---------------------------
    if ndc_code:
        ndc_url = f"https://api.fda.gov/drug/ndc.json?search=product_ndc:{ndc_code}"
        ndc_response = requests.get(ndc_url)
        ndc_data = ndc_response.json()
        
        if ndc_data.get("results"):
            ndc_info = ndc_data["results"][0]
            brand_name = ndc_info.get("brand_name", "Unknown")
            generic_name = ndc_info.get("generic_name", "Unknown")
            dosage_form = ndc_info.get("dosage_form", "Unknown")
            route = ndc_info.get("route", "Unknown")
            manufacturer = ndc_info.get("labeler_name", "Unknown")
        else:
            return f"No NDC data found for code {ndc_code}"
    else:
        return "NDC code is required."

    # If drug_name not provided, use brand_name from NDC
    if not drug_name:
        drug_name = brand_name

    # -----------------------------------
    # 2. Get detailed label info
    # -----------------------------------
    label_url = f"https://api.fda.gov/drug/label.json?search={drug_name}&limit=1"
    label_response = requests.get(label_url)
    label_data = label_response.json()

    if label_data.get("results"):
        label_info = label_data["results"][0]
        warnings = label_info.get("warnings", ["No warnings found"])
        adverse_reactions = label_info.get("adverse_reactions", ["No adverse reactions found"])
        dosage_and_strengths = label_info.get("dosage_and_administration", ["No dosage info found"])
    else:
        warnings = ["No warnings found"]
        adverse_reactions = ["No adverse reactions found"]
        dosage_and_strengths = ["No dosage info found"]

    # ---------------------------
    # 3. Combine and return info
    # ---------------------------
    drug_data = {
        "brand_name": brand_name,
        "generic_name": generic_name,
        "dosage_form": dosage_form,
        "route": route,
        "manufacturer": manufacturer,
        "warnings": warnings,
        "adverse_reactions": adverse_reactions,
        "dosage_and_administration": dosage_and_strengths
    }

    return drug_data


# ---------------------------
# Example usage
# ---------------------------
ndc_code_input = "0002-3250"
drug_info = get_drug_info(ndc_code=ndc_code_input)
for key, value in drug_info.items():
    print(f"{key}: {value}\n")
