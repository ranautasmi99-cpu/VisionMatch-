from flask import Flask, render_template, request, send_from_directory
import os
import uuid

from search import search_similar_images, add_image_to_index, search_multimodal
from database import get_item_by_image_path, insert_item


app = Flask(__name__)

# Folders for uploads & temporary query images
QUERY_FOLDER = "query_images"
TEST_FOLDER = "test_images"
UPLOAD_FOLDER = os.path.join("static", "uploads")

os.makedirs(QUERY_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/query_images/<path:filename>")
def serve_query_image(filename):
    return send_from_directory(QUERY_FOLDER, filename)


@app.route("/test_images/<path:filename>")
def serve_test_image(filename):
    return send_from_directory(TEST_FOLDER, filename)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "GET":
        return render_template("report.html")

    # Handle POST request for item report
    name = request.form.get("name")
    description = request.form.get("description")
    category = request.form.get("category")
    status = request.form.get("status")
    location = request.form.get("location")
    item_date = request.form.get("item_date")

    if not all([name, description, category, status, location, item_date]):
        return render_template("report.html", error="All fields are required.")

    if "image" not in request.files:
        return render_template("report.html", error="Please upload an item image.")

    file = request.files["image"]

    if file.filename == "":
        return render_template("report.html", error="No image selected.")

    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in [".jpg", ".jpeg", ".png"]:
        return render_template("report.html", error="Only JPG, JPEG and PNG images are allowed.")

    filename = str(uuid.uuid4()) + extension
    image_path = os.path.join(UPLOAD_FOLDER, filename).replace("\\", "/")

    # Save uploaded item image
    file.save(image_path)

    try:
        # 1. Save item info into MySQL
        item_id = insert_item(
            name=name,
            description=description,
            category=category,
            status=status,
            image_path=image_path,
            location=location,
            item_date=item_date
        )

        # 2. Generate text representation & update FAISS image + text indices
        text_rep = f"{name} | {description} | {category}"
        add_image_to_index(image_path, text_representation=text_rep)

        return render_template("report.html", success=True, item_id=item_id)
    except Exception as e:
        return render_template("report.html", error=f"Error saving item: {str(e)}")


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return render_template("search.html")

    query_text = request.form.get("query_text", "")
    query_category = request.form.get("category", "")
    query_location = request.form.get("location", "")
    query_status = request.form.get("status", "")

    query_path = None

    if "image" in request.files and request.files["image"].filename != "":
        file = request.files["image"]
        extension = os.path.splitext(file.filename)[1].lower()

        if extension not in [".jpg", ".jpeg", ".png"]:
            return render_template("search.html", error="Only JPG, JPEG and PNG images are allowed.")

        filename = str(uuid.uuid4()) + extension
        query_path = os.path.join(QUERY_FOLDER, filename).replace("\\", "/")
        file.save(query_path)

    # Require at least image or query text
    if not query_path and not query_text.strip():
        return render_template("search.html", error="Please upload a photo or enter item description to search.")

    try:
        # Execute Multimodal Search
        matches = search_multimodal(
            query_image_path=query_path,
            query_text=query_text,
            query_category=query_category,
            query_location=query_location,
            query_status=query_status,
            top_k=5
        )

        return render_template(
            "results.html",
            query_image=query_path,
            query_text=query_text,
            matches=matches
        )
    except Exception as e:
        return render_template("search.html", error=f"Search error: {str(e)}")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", error_title="404 - Page Not Found", error_message="The requested page does not exist on VisionMatch."), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("error.html", error_title="500 - Internal Server Error", error_message="An internal server error occurred. Please try again later."), 500


if __name__ == "__main__":
    app.run(debug=True)