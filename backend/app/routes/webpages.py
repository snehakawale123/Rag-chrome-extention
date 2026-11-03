
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from app.services.webpage_service import extract_text_from_webpage
from app.services.chunk_service import split_text
from app.services.embedding_service import create_embedding
from app.services.qdrant_service import (
    create_collection,
    delete_chunks_by_url,
    insert_chunks,
)

router = APIRouter()


class WebpageRequest(BaseModel):
    url: HttpUrl


@router.post("/webpages/ingest")
def ingest_webpage(request: WebpageRequest):
    url = str(request.url)

    # Basic URL checks. Additional SSRF protection is needed
    # before allowing arbitrary URLs in a public deployment.
    parsed_url = urlparse(url)

    if parsed_url.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400,
            detail="Only HTTP and HTTPS URLs are supported.",
        )

    try:
        webpage = extract_text_from_webpage(url)

        text_chunks = split_text(webpage["text"])

        if not text_chunks:
            raise HTTPException(
                status_code=400,
                detail="No text chunks were generated.",
            )

        chunks_to_insert = []

        for text_chunk in text_chunks:
            chunks_to_insert.append({
                "text": text_chunk,
                "page": None,
                "filename": None,
                "source_type": "webpage",
                "url": url,
                "title": webpage["title"],
                "vector": create_embedding(text_chunk),
            })

        create_collection()

        # Replace previous content for this URL.
        delete_chunks_by_url(url)
        insert_chunks(chunks_to_insert)

        return {
            "message": "Webpage ingested successfully.",
            "url": url,
            "title": webpage["title"],
            "chunks": len(chunks_to_insert),
            "status": "indexed",
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Webpage ingestion failed: {str(exc)}",
        )