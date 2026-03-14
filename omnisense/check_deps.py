# Dependency check script


modules = [
    "google.genai",
    "google.adk",
    "google.adk.sessions",
    "dotenv",
    "PIL",
    "fastapi",
    "uvicorn",
    "requests",
]

for mod in modules:
    try:
        __import__(mod)
        print(f"SUCCESS: {mod}")
    except ImportError as e:
        print(f"FAILED: {mod} - {e}")
