import os
import json
import faiss
import numpy as np
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gimini_embedings import get_text_embedding
from database import get_item_by_image_path

FAISS_FOLDER = "faiss_data"
IMAGE_PATHS_FILE = os.path.join(FAISS_FOLDER, "image_paths.json")
TEXT_INDEX_FILE = os.path.join(FAISS_FOLDER, "text_index.faiss")


def build_text_index():
    os.makedirs(FAISS_FOLDER, exist_ok=True)

    if not os.path.exists(IMAGE_PATHS_FILE):
        print("image_paths.json not found! Build image index first.")
        return

    with open(IMAGE_PATHS_FILE, "r") as f:
        image_paths = json.load(f)

    print(f"Building FAISS text index for {len(image_paths)} items...")

    embeddings = []

    for path in image_paths:
        item = get_item_by_image_path(path)
        if item:
            name = item.get("name", "Item")
            description = item.get("description", "")
            category = item.get("category", "")
            text_rep = f"{name} | {description} | {category}"
        else:
            text_rep = f"{os.path.basename(path)} | Lost Found Item"

        print(f"Processing text embedding for: '{text_rep[:60]}...'")
        vec = get_text_embedding(text_rep)
        embeddings.append(vec)

    embeddings_matrix = np.array(embeddings, dtype=np.float32)
    dimension = embeddings_matrix.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_matrix)

    faiss.write_index(index, TEXT_INDEX_FILE)

    print()
    print("FAISS text index created successfully!")
    print("Total text vectors in index:", index.ntotal)
    print("Saved to:", TEXT_INDEX_FILE)


if __name__ == "__main__":
    build_text_index()
