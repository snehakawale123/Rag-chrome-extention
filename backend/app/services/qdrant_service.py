from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.models import (
    Filter,
    FilterSelector,
    FieldCondition,
    MatchValue,
)


QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "rag_documents"
VECTOR_SIZE = 3072


client = QdrantClient(url=QDRANT_URL)


def create_collection():

    if not client.collection_exists(COLLECTION_NAME):

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )

        print(f"Collection '{COLLECTION_NAME}' created.")

    else:
        print(f"Collection '{COLLECTION_NAME}' already exists.")


def insert_chunks(chunks):

    points = []

    for chunk in chunks:

        point = PointStruct(
            id=str(uuid4()),
            vector=chunk["vector"],
            payload={
                "text": chunk["text"],
                "page": chunk.get("page"),
                "filename": chunk.get("filename"),
                "source_type": chunk.get("source_type", "pdf"),
                "url": chunk.get("url"),
                "title": chunk.get("title"),
            },
        )

        points.append(point)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    print(f"{len(points)} chunks inserted into Qdrant.")


def search_documents(query_vector, limit=3):

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        with_payload=True,
    )

    return results.points



def delete_chunks_by_filename(filename: str):
    """Delete existing chunks for this filename before re-indexing it."""

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="filename",
                        match=MatchValue(value=filename),
                    )
                ]
            )
        ),
        wait=True,
    )

    print(f"Deleted existing chunks for: {filename}")


def list_documents():
    response = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=1000,
        with_payload=True,
        with_vectors=False,
    )

    documents = {}

    for point in response[0]:
        payload = point.payload or {}
        filename = payload.get("filename")

        if not filename:
            continue

        if filename not in documents:
            documents[filename] = {
                "filename": filename,
                "chunks": 0,
                "pages": set(),
            }

        documents[filename]["chunks"] += 1

        page = payload.get("page")
        if page is not None:
            documents[filename]["pages"].add(page)

    return [
        {
            "filename": doc["filename"],
            "chunks": doc["chunks"],
            "pages": sorted(doc["pages"]),
        }
        for doc in documents.values()
    ]    

def delete_chunks_by_url(url: str):
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="url",
                        match=MatchValue(value=url),
                    )
                ]
            )
        ),
        wait=True,
    )
    print(f"Deleted existing chunks for URL: {url}")