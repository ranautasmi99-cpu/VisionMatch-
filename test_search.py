from search import search_similar_images


query_image = "query_images/new_earbuds.jpeg"

results = search_similar_images(
    query_image,
    top_k=3
)

print("\nSimilar images:\n")

for result in results:
    print(
        result["image_path"],
        "Distance:",
        result["distance"]
    )