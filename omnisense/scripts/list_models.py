import os

import google.generativeai as genai
from dotenv import load_dotenv

# Point to central config
config_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "config", ".env")
)
load_dotenv(config_path)
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)
