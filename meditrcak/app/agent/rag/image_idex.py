import os
import numpy as np
import faiss
import torch
from PIL import Image
from tqdm import tqdm
from transformers import CLIPProcessor, CLIPModel

# ==================================================
# CONFIG
# ==================================================
IMAGE_FOLDER = "data/archive/ePillID_data/classification_data/segmented_nih_pills_224"
VECTORSTORE_DIR = "vectorstore"
INDEX_PATH = os.path.join(VECTORSTORE_DIR, "pill_images.faiss")
META_PATH = os.path.join(VECTORSTORE_DIR, "pill_metadata.npy")

MODEL_NAME = "openai/clip-vit-base-patch32"
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
MAX_IMAGES = None  # Limit for faster processing (remove limit by setting to None)

os.makedirs(VECTORSTORE_DIR, exist_ok=True)

# ==================================================
# Load CLIP model
# ==================================================
print(f"Loading CLIP model: {MODEL_NAME}")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained(MODEL_NAME).to(device)
processor = CLIPProcessor.from_pretrained(MODEL_NAME)
print(f"Model loaded on {device}!")

# ==================================================
# Helpers
# ==================================================
def load_image(path: str) -> Image.Image:
    return Image.open(path).convert("RGB").resize(IMAGE_SIZE)

def extract_ndc(filename: str) -> str:
    """
    Expected format: NDC_x_y.jpg → NDC
    """
    # Remove file extensions and suffixes to get clean NDC code
    ndc = filename.replace("_0_0.jpg", "").replace("_0_1.jpg", "").replace(".jpg", "").replace(".png", "")
    return ndc

# ==================================================
# Build embeddings
# ==================================================
embeddings = []
metadata = []
batch_images = []
batch_meta = []

files = [
    f for f in os.listdir(IMAGE_FOLDER)
    if f.lower().endswith((".jpg", ".png"))
]

# Limit number of images if MAX_IMAGES is set
if MAX_IMAGES:
    files = files[:MAX_IMAGES]
    print(f"📊 Processing {len(files)} images (limited to {MAX_IMAGES})")
else:
    print(f"📊 Processing {len(files)} images")

for file in tqdm(files, desc="Embedding pill images"):
    try:
        img_path = os.path.join(IMAGE_FOLDER, file)
        image = load_image(img_path)

        batch_images.append(image)
        batch_meta.append({
            "ndc": extract_ndc(file),
            "file": file
        })

        if len(batch_images) == BATCH_SIZE:
            # Process batch with CLIP
            inputs = processor(images=batch_images, return_tensors="pt").to(device)
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
            batch_emb = image_features.cpu().numpy()
            
            embeddings.extend(batch_emb)
            metadata.extend(batch_meta)

            batch_images.clear()
            batch_meta.clear()

    except Exception as e:
        print(f"⚠️ Skipping {file}: {e}")

# Process remaining images
if batch_images:
    inputs = processor(images=batch_images, return_tensors="pt").to(device)
    with torch.no_grad():
        image_features = model.get_image_features(**inputs)
    batch_emb = image_features.cpu().numpy()
    
    embeddings.extend(batch_emb)
    metadata.extend(batch_meta)

# ==================================================
# Build FAISS index
# ==================================================
embeddings = np.vstack(embeddings).astype("float32")

dim = embeddings.shape[1]
index = faiss.IndexFlatL2(dim)  # L2 distance (Euclidean)
index.add(embeddings)

# ==================================================
# Save index + metadata
# ==================================================
faiss.write_index(index, INDEX_PATH)
np.save(META_PATH, metadata)

print("✅ Image vector store created")
print(f"   Images indexed : {len(embeddings)}")
print(f"   Vector dim     : {dim}")
print(f"   Index path     : {INDEX_PATH}")
