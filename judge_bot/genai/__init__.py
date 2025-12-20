import os

from google.genai import Client as GoogleClient


def get_google_client() -> GoogleClient:
    google_client = GoogleClient(api_key=os.getenv("GOOGLE_API_KEY"))
    return google_client

def get_client(provider: str = "google") -> GoogleClient:
    if provider == "google":
        return get_google_client()
    raise ValueError(f"Unsupported provider: {provider}")