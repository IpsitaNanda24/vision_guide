import os

from dotenv import load_dotenv
from google import genai

# Load environment variables from config/.env
env_path = os.path.join(os.getcwd(), "config", ".env")
load_dotenv(dotenv_path=env_path, override=True)

api_key = os.getenv("GEMINI_API_KEY")
model_id = os.getenv("GEMINI_MODEL_ID")

print(f"Testing API Key: {api_key[:10]}...")
print(f"Testing Model: {model_id}")


def test_gemini():
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment.")
        return

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_id,
            contents="Say 'API still working' if you can read this.",
        )
        print("Response from Gemini:")
        print(response.text)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    test_gemini()
