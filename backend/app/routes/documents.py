
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.pdf_service import extract_text_from_pdf
from app.services.chunk_service import split_text
from app.services.embedding_service import create_embedding
from app.services.qdrant_service import create_collection, insert_chunks
from app.services.qdrant_service import (
    create_collection,
    insert_chunks,
    delete_chunks_by_filename,
)
from app.services.qdrant_service import list_documents

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    # 1. Validate the uploaded file
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please provide a filename."
        )

    filename = Path(file.filename).name

    if Path(filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported currently."
        )

    # 2. Save the uploaded PDF
    file_path = UPLOAD_DIR / filename

    try:
        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="The uploaded PDF is empty."
            )

        file_path.write_bytes(content)

        # 3. Extract text from the PDF
        pages = extract_text_from_pdf(str(file_path))

        if not pages:
            raise HTTPException(
                status_code=400,
                detail="No readable text found in the PDF."
            )

        # 4. Split extracted text into chunks
        all_chunks = []

        for page in pages:
            chunks = split_text(page["text"])

            for chunk in chunks:
                all_chunks.append({
                    "text": chunk,
                    "page": page["page"],
                    "filename": filename,
                })

        if not all_chunks:
            raise HTTPException(
                status_code=400,
                detail="No text chunks could be created."
            )

        # 5. Generate an embedding for each chunk
        for index, chunk in enumerate(all_chunks, start=1):
            print(
                f"Embedding chunk {index}/{len(all_chunks)}..."
            )
            chunk["vector"] = create_embedding(chunk["text"])

        # 6. Create the collection if needed and store the chunks
        create_collection()
        # Remove old chunks for this filename first
        delete_chunks_by_filename(filename)
        # Store the newly processed chunks
        insert_chunks(all_chunks)

        # 7. Return the result
        return {
            "message": "Document uploaded and indexed successfully.",
            "filename": filename,
            "pages": len(pages),
            "chunks": len(all_chunks),
            "status": "indexed",
        }

    except HTTPException:
        raise

    except Exception as exc:
        print(f"Document ingestion failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Document upload or indexing failed. Check the backend terminal."
        ) from exc

    finally:
        await file.close()

@router.get("/documents")
async def get_documents():
    documents = list_documents()

    return {
        "count": len(documents),
        "documents": documents,
    }

@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    safe_filename = Path(filename).name

    if safe_filename != filename or not safe_filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    file_path = UPLOAD_DIR / safe_filename

    delete_chunks_by_filename(safe_filename)

    if file_path.exists():
        file_path.unlink()

    return {
        "message": "Document deleted successfully.",
        "filename": safe_filename,
    }