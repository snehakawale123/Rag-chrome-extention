
from app.services.embedding_service import create_embedding
from app.services.qdrant_service import search_documents
from app.services.llm_service import llm


def answer_question(question: str):
    # 1. Convert the question into an embedding
    query_vector = create_embedding(question)

    # 2. Retrieve more relevant chunks from Qdrant
    results = search_documents(query_vector, limit=8)

    print("\n===== ALL RETRIEVED CHUNKS =====")
    for result in results:
        payload = result.payload or {}
        print("Score:", result.score)
        print("Filename:", payload.get("filename"))
        print("Page:", payload.get("page"))
        print("Text:", payload.get("text"))
        print("--------------------")

    # 3. Filter by similarity score
    MIN_SCORE = 0.40

    results = [
        result
        for result in results
        if result.score is not None and result.score >= MIN_SCORE
    ]

    # 4. Build context and sources
  

    context_parts = []
    sources = []
    seen_chunks = set()
    seen_sources = set()

    for result in results:
        payload = result.payload or {}

        text = payload.get("text", "")
        filename = payload.get("filename", "Unknown document")
        page = payload.get("page")

        if not text:
            continue

        # Deduplicate context chunks
        chunk_key = (filename, page, text)
        if chunk_key in seen_chunks:
            continue

        seen_chunks.add(chunk_key)
        context_parts.append(text)

        source_type = payload.get("source_type", "pdf")

        if source_type == "webpage":
            source_key = (
                "webpage",
                payload.get("url")
                or payload.get("title")
                or "Unknown webpage",
            )
        else:
            source_key = ("pdf", filename)

        # Add each source document only once
        if source_key in seen_sources:
            continue

        seen_sources.add(source_key)

        source = {
            "source_type": source_type,
            "score": round(float(result.score), 4),
            "text": text,
        }

        if source_type == "webpage":
            source["title"] = payload.get("title")
            source["url"] = payload.get("url")
        else:
            source["filename"] = filename
            source["page"] = page

        sources.append(source)
        payload = result.payload or {}

        text = payload.get("text", "")
        filename = payload.get("filename", "Unknown document")
        page = payload.get("page")

        if not text:
            continue

        # Avoid including identical chunks more than once
        chunk_key = (filename, page, text)

        if chunk_key in seen_chunks:
            continue

        seen_chunks.add(chunk_key)
        context_parts.append(text)

        source_type = payload.get("source_type", "pdf")

        source = {
            "source_type": source_type,
            "score": round(float(result.score), 4),
            "text": text,
        }

        if source_type == "webpage":
            source["title"] = payload.get("title")
            source["url"] = payload.get("url")
        else:
            source["filename"] = filename
            source["page"] = page

        sources.append(source)

    context = "\n\n".join(context_parts)

    print("\n===== CONTEXT SENT TO GEMINI =====")
    print(context)

    # 5. Handle empty context
    if not context.strip():
        return {
            "answer": "I don't know based on the provided documents.",
            "sources": [],
        }

    # 6. Ask Gemini to answer from the retrieved context
    prompt = f"""
You answer questions using the supplied document context.

Instructions:
- Answer the user's question directly.
- Use only facts stated in the context.
- For questions about previous employment, identify the
  employers and job titles explicitly present in the context.
- Do not say information is missing if it is present in the context.
- If the answer truly is not present, say:
  "I don't know based on the provided documents."

Context:
{context}

Question:
{question}

Answer:
"""

    response = llm.invoke(prompt)

    # 7. Extract Gemini's answer
    if isinstance(response.content, list):
        answer = "".join(
            item.get("text", "")
            for item in response.content
            if isinstance(item, dict)
            and item.get("type") == "text"
        )
    else:
        answer = str(response.content)

    return {
        "answer": answer,
        "sources": sources,
    }
