import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

try:
    print("Sending request to gemini-2.0-flash...")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Return a JSON object: {'hello': 'world'}"
    )
    print("Response received.")
    print(f"Generated text: {response.text}")
except Exception as e:
    print(f"Error occurred: {e}")
