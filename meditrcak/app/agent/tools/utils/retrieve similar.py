import faiss
import numpy as np
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import sys
import os
import requests

# Helper function to get FDA drug info by NDC
def get_drug_info_by_ndc(ndc_code: str) -> dict:
    """Get FDA drug information by NDC code."""
    try:
        url = "https://api.fda.gov/drug/label.json"
        params = {
            "search": f'openfda.product_ndc:{ndc_code}',
            "limit": 1
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("results"):
            return {"error": f"No FDA data found for NDC: {ndc_code}"}
        
        result = data["results"][0]
        openfda = result.get("openfda", {})
        
        return {
            "brand_name": openfda.get("brand_name", ["N/A"])[0] if openfda.get("brand_name") else "N/A",
            "generic_name": openfda.get("generic_name", ["N/A"])[0] if openfda.get("generic_name") else "N/A",
            "manufacturer": openfda.get("manufacturer_name", ["N/A"])[0] if openfda.get("manufacturer_name") else "N/A",
            "purpose": result.get("purpose", ["N/A"])[0] if result.get("purpose") else "N/A",
            "warnings": result.get("warnings", ["N/A"])[0][:200] + "..." if result.get("warnings") and len(result.get("warnings", [""])[0]) > 200 else result.get("warnings", ["N/A"])[0] if result.get("warnings") else "N/A"
        }
    except Exception as e:
        return {"error": str(e)}

# ----------------------------
# CONFIG
# ----------------------------
INDEX_FILE = "vectorstore/pill_images.faiss"
METADATA_FILE = "vectorstore/pill_metadata.npy"
EMBEDDING_MODEL = "openai/clip-vit-base-patch32"
TOP_K = 5

# ----------------------------
# Load index and metadata
# ----------------------------
print(f"Loading FAISS index from {INDEX_FILE}...")
index = faiss.read_index(INDEX_FILE)
metadata = np.load(METADATA_FILE, allow_pickle=True)
print(f"Loaded {index.ntotal} pill embeddings")

print(f"Loading CLIP model: {EMBEDDING_MODEL}...")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained(EMBEDDING_MODEL).to(device)
processor = CLIPProcessor.from_pretrained(EMBEDDING_MODEL)
print("Model loaded!")

# ----------------------------
# Query image
# ----------------------------
query_img_path = r"data/archive/ePillID_data/classification_data/fcn_mix_weight/dc_224/0.jpg"
print(f"\nSearching for similar pills to: {query_img_path}")

img = Image.open(query_img_path).convert("RGB")
inputs = processor(images=img, return_tensors="pt").to(device)

with torch.no_grad():
    query_emb = model.get_image_features(**inputs)

query_emb = query_emb.cpu().numpy().astype("float32")

# ----------------------------
# Search
# ----------------------------
distances, indices = index.search(query_emb, TOP_K)

print(f"\nTop {TOP_K} similar pills:")
print("-" * 60)
for rank, (idx, dist) in enumerate(zip(indices[0], distances[0]), 1):
    meta = metadata[idx]
    ndc_raw = meta['ndc']
    # Clean NDC code - remove file extensions and extra suffixes
    ndc_code = ndc_raw.replace('_0_0.jpg', '').replace('_0_1.jpg', '').replace('.jpg', '')
    print(f"{rank}. NDC: {ndc_code}")
    print(f"   File: {meta['file']}")
    print(f"   Distance: {dist:.4f}")
    
    # Get FDA info for this pill
    print(f"\n   FDA Drug Information:")
    drug_info = get_drug_info_by_ndc(ndc_code)
    if "error" in drug_info:
        print(f"   {drug_info['error']}")
    else:
        for key, value in drug_info.items():
            print(f"   {key}: {value}")
    print()

# ----------------------------
# Example 2: Search by NDC directly
# ----------------------------
print("\n" + "=" * 60)
ndc_input = "51285-0092"
print(f"FDA info for NDC {ndc_input}:")
drug_info = get_drug_info_by_ndc(ndc_input)
if "error" in drug_info:
    print(drug_info['error'])
else:
    for key, value in drug_info.items():
        print(f"{key}: {value}")

#     def __init__(self, index_file, metadata_file, embedding_model="clip-ViT-B-32"):
#         # Load FAISS index and metadata
#         self.index = faiss.read_index(index_file)
#         self.metadata = np.load(metadata_file, allow_pickle=True)
        
#         # Load embedding model
#         self.model = SentenceTransformer(embedding_model)
    
#     def _vector_from_image(self, image_path):
#         img = Image.open(image_path).convert("RGB").resize((224,224))
#         return self.model.encode(np.array(img)).astype("float32")
    
#     def _vector_from_text(self, text):
#         return self.model.encode([text])[0].astype("float32")
    
#     def search_by_vector(self, query_vector, top_k=5):
#         query_vector = query_vector.reshape(1, -1)
#         distances, indices = self.index.search(query_vector, top_k)
#         results = []
#         for idx, dist in zip(indices[0], distances[0]):
#             if idx != -1:
#                 results.append({"metadata": self.metadata[idx].item(), "distance": dist})
#         return results
    
#     def search_by_image(self, image_path, top_k=5):
#         vec = self._vector_from_image(image_path)
#         return self.search_by_vector(vec, top_k)
    
#     def search_by_ndc(self, ndc_code, top_k=5):
#         vec = self._vector_from_text(ndc_code)
#         return self.search_by_vector(vec, top_k)

# # ----------------------------
# # Usage example
# # ----------------------------
# INDEX_FILE = "pill_images.index"
# METADATA_FILE = "pill_metadata.npy"

# retriever = PillRetriever(INDEX_FILE, METADATA_FILE)

# # Search by image
# image_results = retriever.search_by_image("data/your_image.jpg")
# print("Search by image:")
# for r in image_results:
#     print(f"NDC: {r['metadata']['ndc']}, File: {r['metadata']['file']}, Distance: {r['distance']:.4f}")

# # Search by NDC
# ndc_results = retriever.search_by_ndc("0002-3228")
# print("\nSearch by NDC:")
# for r in ndc_results:
#     print(f"NDC: {r['metadata']['ndc']}, File: {r['metadata']['file']}, Distance: {r['distance']:.4f}")
