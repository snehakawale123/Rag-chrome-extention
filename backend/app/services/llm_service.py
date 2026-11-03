from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import GEMINI_API_KEY

llm = ChatGoogleGenerativeAI(
    model="gemini-3.7-flash",
    google_api_key=GEMINI_API_KEY,
)