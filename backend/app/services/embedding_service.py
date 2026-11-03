from google import genai

from app.core.config import GEMINI_API_KEY


client = genai.Client(api_key=GEMINI_API_KEY)


def create_embedding(text: str):
    result = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text,
    )

    return result.embeddings[0].values