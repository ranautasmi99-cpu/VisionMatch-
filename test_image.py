import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 1. Read the image as bytes
with open("test_images/earbuds.jpg", "rb") as f:
    image_bytes = f.read()

# 2. Convert bytes to Part object with appropriate mime type
image_part = types.Part.from_bytes(
    data=image_bytes,
    mime_type="image/jpeg",  # Change to image/png if using PNG
)

prompt = """
Identify this object.
Give only:
Category:
Color:
Short description:
"""

# 3. Call generate_content with a valid model name
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=[prompt, image_part],
)

print(response.text)