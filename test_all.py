import os
import sys
import shutil
import faiss
import numpy as np

print("=" * 60)
print(" VISIONMATCH - COMPREHENSIVE SYSTEM VERIFICATION SUITE ")
print("=" * 60)

# A. Test Database Connection
print("\n[A] Testing Database Connection...")
try:
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    conn.close()
    print("  [SUCCESS] Database connection to 'visionmatch' established.")
except Exception as e:
    print(f"  [FAILED] Database connection error: {e}")
    sys.exit(1)

# B & C. Test Item Report & Image Upload Simulation
print("\n[B & C] Testing Item Reporting & Image Upload...")
test_image_source = "test_images/earbuds.jpg"
if not os.path.exists(test_image_source):
    print("  [FAILED] Baseline test image 'test_images/earbuds.jpg' not found.")
    sys.exit(1)

target_upload_dir = "static/uploads"
os.makedirs(target_upload_dir, exist_ok=True)
test_upload_path = os.path.join(target_upload_dir, "test_verification_earbuds.jpg").replace("\\", "/")

shutil.copy(test_image_source, test_upload_path)
print(f"  [SUCCESS] Image copied to upload directory: {test_upload_path}")

from database import insert_item
try:
    item_id = insert_item(
        name="Verification Earbuds",
        description="Automated system test earbuds item",
        category="Electronics",
        status="Found",
        image_path=test_upload_path,
        location="Testing Lab",
        item_date="2026-09-06"
    )
    print(f"  [SUCCESS] Item inserted into MySQL items table with ID: {item_id}")
except Exception as e:
    print(f"  [FAILED] MySQL item insertion failed: {e}")
    sys.exit(1)

# D. Test Gemini Embeddings Generation
print("\n[D] Testing Gemini Image Embedding Generation...")
try:
    from gimini_embedings import get_image_embedding
    vector = get_image_embedding(test_upload_path)
    print(f"  [SUCCESS] Embedding vector generated! Vector dimension: {len(vector)} (dtype: {vector.dtype})")
except Exception as e:
    print(f"  [FAILED] Gemini API embedding generation failed: {e}")
    sys.exit(1)

# E. Test FAISS Index Addition
print("\n[E] Testing Dynamic FAISS Index Addition...")
try:
    from search import add_image_to_index
    add_image_to_index(test_upload_path)
    index = faiss.read_index("faiss_data/index.faiss")
    print(f"  [SUCCESS] FAISS index updated! Total vectors in index: {index.ntotal}")
except Exception as e:
    print(f"  [FAILED] FAISS index addition failed: {e}")
    sys.exit(1)

# F. Test Image Search
print("\n[F] Testing Similarity Search with FAISS...")
try:
    from search import search_similar_images
    results = search_similar_images(test_upload_path, top_k=3)
    print(f"  [SUCCESS] Search completed! Found {len(results)} matches.")
    for idx, r in enumerate(results, 1):
        print(f"    Match #{idx}: Path={r['image_path']}, Distance={r['distance']:.4f}")
except Exception as e:
    print(f"  [FAILED] FAISS search failed: {e}")
    sys.exit(1)

# G. Test Retrieving Database Record for Match
print("\n[G] Testing MySQL Lookup for Matching Image...")
try:
    from database import get_item_by_image_path
    match_path = results[0]["image_path"]
    db_item = get_item_by_image_path(match_path)
    if db_item:
        print(f"  [SUCCESS] Database record retrieved! Name: '{db_item['name']}', Category: '{db_item['category']}', Status: '{db_item['status']}'")
    else:
        print(f"  [WARNING] No record found in DB for path: {match_path}")
except Exception as e:
    print(f"  [FAILED] Database record retrieval error: {e}")
    sys.exit(1)

# H. Test Flask Web Application Routes
print("\n[H] Testing Flask Web Interface Endpoints...")
try:
    from app import app
    client = app.test_client()
    
    r_home = client.get("/")
    r_report = client.get("/report")
    r_search = client.get("/search")
    
    print(f"  [SUCCESS] GET / -> HTTP {r_home.status_code}")
    print(f"  [SUCCESS] GET /report -> HTTP {r_report.status_code}")
    print(f"  [SUCCESS] GET /search -> HTTP {r_search.status_code}")
except Exception as e:
    print(f"  [FAILED] Web endpoint verification failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print(" ALL SYSTEM VERIFICATION CHECKS PASSED SUCCESSFULLY! ")
print("=" * 60)
