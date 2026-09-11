import os
import json
import faiss
import numpy as np
import sys

# Add project root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gimini_embedings import get_image_embedding


IMAGE_FOLDER = "test_images"
FAISS_FOLDER = "faiss_data"

INDEX_FILE = os.path.join(FAISS_FOLDER, "index.faiss")
IMAGE_PATHS_FILE = os.path.join(FAISS_FOLDER, "image_paths.json")


def build_index():

    # Create faiss_data folder if it doesn't exist
    os.makedirs(FAISS_FOLDER, exist_ok=True)

    image_paths = []
    embeddings = []

    # Find images
    for filename in os.listdir(IMAGE_FOLDER):

        if filename.lower().endswith((".jpg", ".jpeg", ".png")):

            image_path = os.path.join(
                IMAGE_FOLDER,
                filename
            )

            print(f"Processing: {filename}")

            # Generate Gemini embedding
            vector = get_image_embedding(image_path)

            image_paths.append(image_path)
            embeddings.append(vector)

    # Make sure we found images
    if not embeddings:
        print("No images found!")
        return

    # Convert list to NumPy array
    embeddings = np.array(
        embeddings,
        dtype=np.float32
    )

    print("Embedding matrix shape:", embeddings.shape)

    # Create FAISS index
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    # Add vectors to FAISS
    index.add(embeddings)

    # Save FAISS index
    faiss.write_index(
        index,
        INDEX_FILE
    )

    # Save image paths
    with open(IMAGE_PATHS_FILE, "w") as f:

        json.dump(
            image_paths,
            f,
            indent=4
        )

    print()
    print("FAISS index created successfully!")
    print("Number of images:", index.ntotal)
    print("Index saved to:", INDEX_FILE)
    print("Image paths saved to:", IMAGE_PATHS_FILE)


if __name__ == "__main__":
    build_index()