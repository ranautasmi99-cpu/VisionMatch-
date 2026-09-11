import os
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def get_image_embedding(image_path: str) -> np.ndarray:
    """
    Reads an image file and retrieves its vector embedding
    using the Gemini API.

    Returns a float32 NumPy array ready for FAISS.
    """

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Determine image type
    if image_path.lower().endswith(".png"):
        mime_type = "image/png"
    else:
        mime_type = "image/jpeg"

    result = client.models.embed_content(
        model="gemini-embedding-2",
        contents=[
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
        ]
    )

    # Convert to NumPy float32 for FAISS
    embedding_vector = np.array(
        result.embeddings[0].values,
        dtype=np.float32
    )

    return embedding_vector


def get_text_embedding(text: str) -> np.ndarray:
    """
    Retrieves vector embedding for a text string using the Gemini API.
    Returns a float32 NumPy array ready for FAISS.
    """
    if not text or not text.strip():
        text = "Unspecified Lost Found Item"

    result = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text.strip()
    )

    embedding_vector = np.array(
        result.embeddings[0].values,
        dtype=np.float32
    )

    return embedding_vector


if __name__ == "__main__":

    test_image = "test_images/earbuds.jpg"

    if os.path.exists(test_image):

        vector = get_image_embedding(test_image)

        print("Embedding generated successfully!")
        print("Vector Dimension:", len(vector))
        print("Sample values:", vector[:5])

    else:
        print("Test image not found!")