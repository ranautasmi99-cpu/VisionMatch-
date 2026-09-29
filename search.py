import os
import json
import faiss
import numpy as np

from gimini_embedings import get_image_embedding, get_text_embedding


FAISS_FOLDER = "faiss_data"

INDEX_FILE = os.path.join(
    FAISS_FOLDER,
    "index.faiss"
)

TEXT_INDEX_FILE = os.path.join(
    FAISS_FOLDER,
    "text_index.faiss"
)

IMAGE_PATHS_FILE = os.path.join(
    FAISS_FOLDER,
    "image_paths.json"
)


def search_similar_images(query_image, top_k=3):
    """
    Original working image similarity search function.
    Preserved without changes for backward compatibility.
    """
    # Load FAISS index
    index = faiss.read_index(INDEX_FILE)

    # Load image paths
    with open(IMAGE_PATHS_FILE, "r") as f:
        image_paths = json.load(f)

    # Create embedding for query image
    query_vector = get_image_embedding(query_image)

    # Convert to NumPy array
    query_vector = np.array(
        [query_vector],
        dtype=np.float32
    )

    # Search FAISS
    distances, indices = index.search(
        query_vector,
        top_k
    )

    results = []

    for distance, index_position in zip(
        distances[0],
        indices[0]
    ):
        if index_position < len(image_paths):
            image_path = image_paths[index_position]

            results.append({
                "image_path": image_path,
                "distance": float(distance)
            })

    return results


def add_image_to_index(image_path, text_representation=None):
    """
    Generates image & text embeddings for a new item and appends them dynamically
    to the FAISS image index, FAISS text index, and image_paths.json file.
    """
    normalized_path = image_path.replace("\\", "/")
    os.makedirs(FAISS_FOLDER, exist_ok=True)

    # 1. Generate & Add Image Embedding
    img_vector = get_image_embedding(image_path)
    img_vector_2d = np.array([img_vector], dtype=np.float32)

    if os.path.exists(INDEX_FILE):
        img_index = faiss.read_index(INDEX_FILE)
    else:
        img_index = faiss.IndexFlatL2(img_vector_2d.shape[1])

    img_index.add(img_vector_2d)
    faiss.write_index(img_index, INDEX_FILE)

    # 2. Generate & Add Text Embedding
    if not text_representation:
        text_representation = f"{os.path.basename(normalized_path)} | Lost Found Item"

    txt_vector = get_text_embedding(text_representation)
    txt_vector_2d = np.array([txt_vector], dtype=np.float32)

    if os.path.exists(TEXT_INDEX_FILE):
        txt_index = faiss.read_index(TEXT_INDEX_FILE)
    else:
        txt_index = faiss.IndexFlatL2(txt_vector_2d.shape[1])

    txt_index.add(txt_vector_2d)
    faiss.write_index(txt_index, TEXT_INDEX_FILE)

    # 3. Update image_paths.json
    if os.path.exists(IMAGE_PATHS_FILE):
        with open(IMAGE_PATHS_FILE, "r") as f:
            image_paths = json.load(f)
    else:
        image_paths = []

    image_paths.append(normalized_path)

    with open(IMAGE_PATHS_FILE, "w") as f:
        json.dump(image_paths, f, indent=4)

    return True


def search_multimodal(
    query_image_path=None,
    query_text=None,
    query_category=None,
    query_location=None,
    query_status=None,
    top_k=5,
    query_img_vec_2d=None,
    query_txt_vec_2d=None
):
    """
    Performs Multimodal Similarity Search combining:
    - Image Similarity (60% weight) via FAISS L2 image index
    - Text Similarity (25% weight) via FAISS L2 text index
    - Metadata Matching Score (15% weight) based on Category, Location & Status
    """
    if not os.path.exists(IMAGE_PATHS_FILE):
        return []

    with open(IMAGE_PATHS_FILE, "r") as f:
        image_paths = json.load(f)

    num_items = len(image_paths)
    if num_items == 0:
        return []

    # 1. Compute Image Distances
    image_sim_scores = [0.5] * num_items
    image_distances = [999.0] * num_items

    if (query_image_path and os.path.exists(query_image_path) and os.path.exists(INDEX_FILE)) or query_img_vec_2d is not None:
        img_index = faiss.read_index(INDEX_FILE)
        if query_img_vec_2d is None:
            img_vec = get_image_embedding(query_image_path)
            img_vec_2d = np.array([img_vec], dtype=np.float32)
        else:
            img_vec_2d = query_img_vec_2d

        distances, indices = img_index.search(img_vec_2d, num_items)

        for dist, idx in zip(distances[0], indices[0]):
            if 0 <= idx < num_items:
                image_distances[idx] = float(dist)
                # Normalize L2 distance to [0, 1] similarity score
                image_sim_scores[idx] = 1.0 / (1.0 + float(dist))

    # 2. Compute Text Distances
    text_sim_scores = [0.5] * num_items

    if ((query_text and query_text.strip()) or query_txt_vec_2d is not None) and os.path.exists(TEXT_INDEX_FILE):
        txt_index = faiss.read_index(TEXT_INDEX_FILE)
        if query_txt_vec_2d is None:
            txt_vec = get_text_embedding(query_text.strip())
            txt_vec_2d = np.array([txt_vec], dtype=np.float32)
        else:
            txt_vec_2d = query_txt_vec_2d

        txt_distances, txt_indices = txt_index.search(txt_vec_2d, num_items)

        for dist, idx in zip(txt_distances[0], txt_indices[0]):
            if 0 <= idx < num_items:
                # Normalize L2 distance to [0, 1] similarity score
                text_sim_scores[idx] = 1.0 / (1.0 + float(dist))
    elif query_image_path:
        # Fall back text similarity to image similarity if no explicit search text given
        text_sim_scores = list(image_sim_scores)

    # 3. Compute Metadata Scores & Combine Final Weighted Score
    from database import get_item_by_image_path

    multimodal_results = []

    for idx, path in enumerate(image_paths):
        item = get_item_by_image_path(path)

        # Metadata Match Calculation (max 1.0)
        category_score = 0.50
        location_score = 0.30
        status_score = 0.20

        if item:
            if query_category and query_category.strip():
                if query_category.strip().lower() == item.get("category", "").strip().lower():
                    category_score = 0.50
                else:
                    category_score = 0.0

            if query_location and query_location.strip():
                item_loc = item.get("location", "").strip().lower()
                q_loc = query_location.strip().lower()
                if q_loc in item_loc or item_loc in q_loc:
                    location_score = 0.30
                else:
                    location_score = 0.05

            if query_status and query_status.strip():
                q_stat = query_status.strip().lower()
                item_stat = item.get("status", "").strip().lower()
                # A "Lost" search query matches "Found" items best
                if (q_stat == "lost" and item_stat == "found") or (q_stat == "found" and item_stat == "lost"):
                    status_score = 0.20
                elif q_stat == item_stat:
                    status_score = 0.15
                else:
                    status_score = 0.05

        meta_score = category_score + location_score + status_score
        meta_score = min(1.0, max(0.0, meta_score))

        img_sim = image_sim_scores[idx]
        txt_sim = text_sim_scores[idx]

        # Final Weighted Score Calculation:
        # 0.60 * Image Similarity + 0.25 * Text Similarity + 0.15 * Metadata Score
        final_score = (0.60 * img_sim) + (0.25 * txt_sim) + (0.15 * meta_score)

        multimodal_results.append({
            "image_path": path,
            "distance": image_distances[idx],
            "image_similarity": img_sim,
            "text_similarity": txt_sim,
            "metadata_score": meta_score,
            "final_score": final_score,
            "item": item
        })

    # Sort results by Final Score descending
    multimodal_results.sort(key=lambda x: x["final_score"], reverse=True)

    return multimodal_results[:top_k]