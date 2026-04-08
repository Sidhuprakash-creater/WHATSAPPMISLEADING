import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load from the correct absolute path
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", ".env")
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not found in .env")
else:
    genai.configure(api_key=api_key)
    try:
        print("--- Available Models ---")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")
