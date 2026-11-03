from fastapi import FastAPI

from app.routes.chat import router as chat_router
from app.routes.documents import router as documents_router
from app.routes.webpages import router as webpages_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RAG Chrome Extension API",
    description="FastAPI backend for our RAG Chrome Extension",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
   allow_origins=[
        "null",
        "chrome-extension://onknpgggcdbkpilhiccffaikpaelkapd"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/")
async def root():
    return {"message": "RAG API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


app.include_router(
    chat_router,
    prefix="/api",
    tags=["Chat"]
)


app.include_router(
    documents_router,
    prefix="/api",
    tags=["Documents"]
)

app.include_router(
    webpages_router,
    prefix="/api",
    tags=["Webpages"]
)