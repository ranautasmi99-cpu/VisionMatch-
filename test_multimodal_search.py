import os
import sys

print("=" * 60)
print(" MULTIMODAL SIMILARITY SYSTEM VERIFICATION SUITE ")
print("=" * 60)

# 1. Test Image Similarity Search (Original & Multimodal)
print("\n[TEST 1] Testing Image Similarity Search Independently...")
from search import search_similar_images, search_multimodal

test_image = "test_images/earbuds.jpg"

if os.path.exists(test_image):
    img_results = search_similar_images(test_image, top_k=3)
    print("  [SUCCESS] Baseline image search working! Top match:")
    print(f"    Path: {img_results[0]['image_path']}, Raw L2 Distance: {img_results[0]['distance']:.4f}")
else:
    print("  [FAILED] Test image 'test_images/earbuds.jpg' missing.")
    sys.exit(1)

# 2. Test Text Embedding & Text Similarity Search
print("\n[TEST 2] Testing Text Similarity Search Independently...")
from gimini_embedings import get_text_embedding

query_text = "Black boAt earbuds true wireless in charging case"
try:
    txt_vec = get_text_embedding(query_text)
    print(f"  [SUCCESS] Gemini text embedding generated! Dimension: {len(txt_vec)}")
    
    text_matches = search_multimodal(query_text=query_text, top_k=3)
    print("  [SUCCESS] Text similarity search completed! Top match:")
    print(f"    Path: {text_matches[0]['image_path']}, Text Sim: {text_matches[0]['text_similarity']*100:.2f}%")
except Exception as e:
    print(f"  [FAILED] Text similarity search error: {e}")
    sys.exit(1)

# 3. Test Metadata Score & Final Weighted Combination
print("\n[TEST 3] Testing Multimodal Score Combination & Ranking...")
try:
    multimodal_matches = search_multimodal(
        query_image_path=test_image,
        query_text="Black boAt earbuds wireless",
        query_category="Electronics",
        query_location="Library",
        query_status="Lost",
        top_k=3
    )

    print("  [SUCCESS] Multimodal combination completed! Results ranking:")
    for idx, match in enumerate(multimodal_matches, 1):
        print(f"    Match #{idx}: {match['image_path']}")
        print(f"      Image Sim  (60%): {match['image_similarity']*100:.2f}%")
        print(f"      Text Sim   (25%): {match['text_similarity']*100:.2f}%")
        print(f"      Meta Score (15%): {match['metadata_score']*100:.2f}%")
        print(f"      FINAL SCORE     : {match['final_score']*100:.2f}%")
        print("-" * 50)

except Exception as e:
    print(f"  [FAILED] Multimodal combination test error: {e}")
    sys.exit(1)

# 4. Verify Image-Only Search Backward Compatibility
print("\n[TEST 4] Verifying Image-Only Search Backward Compatibility...")
try:
    compat_results = search_similar_images(test_image, top_k=3)
    assert len(compat_results) > 0
    print("  [SUCCESS] Original search_similar_images() function intact & fully operational!")
except Exception as e:
    print(f"  [FAILED] Backward compatibility test error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print(" ALL MULTIMODAL SIMILARITY TESTS PASSED SUCCESSFULLY! ")
print("=" * 60)
