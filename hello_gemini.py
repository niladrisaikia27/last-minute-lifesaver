from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model=os.environ["GEMINI_MODEL"],
    contents="Say hello and tell me what you can help with!"
)

print(response.text)