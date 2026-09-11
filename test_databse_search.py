from search import search_similar_images
from database import get_item_by_image_path


query_image = "query_images/new_earbuds.jpeg"


results = search_similar_images(
    query_image,
    top_k=3
)


print("\nPossible matches:\n")


for result in results:

    image_path = result["image_path"]
    distance = result["distance"]

    item = get_item_by_image_path(image_path)

    print("Image:", image_path)
    print("Distance:", distance)

    if item:
        print("Item ID:", item["id"])
        print("Name:", item["name"])
        print("Description:", item["description"])
        print("Category:", item["category"])
        print("Status:", item["status"])
        print("Location:", item["location"])
        print("Date:", item["item_date"])
    else:
        print("No database record found.")

    print("-" * 40)