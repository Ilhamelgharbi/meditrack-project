import os
from PIL import Image
from tqdm import tqdm
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# ----------------------------
# CONFIG
# ----------------------------
IMAGE_FOLDER = r"data\archive\ePillID_data\classification_data\segmented_nih_pills_224"
INDEX_FILE = "pill_images.index"
METADATA_FILE = "pill_metadata.npy"
EMBEDDING_MODEL = "clip-ViT-B-32"  # or another image-text model

# ----------------------------
# Initialize embedding model
# ----------------------------
model = SentenceTransformer(EMBEDDING_MODEL)

# ----------------------------
# Load images and create embeddings
# ----------------------------
embeddings = []
metadata = []

for img_file in tqdm(os.listdir(IMAGE_FOLDER)):
    if img_file.endswith(".jpg") or img_file.endswith(".png"):
        img_path = os.path.join(IMAGE_FOLDER, img_file)
        
        # open and preprocess image
        img = Image.open(img_path).convert("RGB").resize((224,224))
        
        # embed image
        emb = model.encode(np.array(img))  # shape (embedding_dim,)
        embeddings.append(emb)
        
        # store metadata
        ndc_code = img_file.replace("_0_0.jpg", "")  # get NDC from filename
        metadata.append({"file": img_file, "ndc": ndc_code})

# ----------------------------
# Convert to FAISS index
# ----------------------------
embeddings = np.vstack(embeddings).astype("float32")
dim = embeddings.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(embeddings)

# Save index and metadata
faiss.write_index(index, INDEX_FILE)
np.save(METADATA_FILE, metadata)

print("Index and metadata saved!")
