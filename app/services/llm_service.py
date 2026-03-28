"""
LLM response generation using Gemini 1.5 Flash via google-genai SDK.
Strict grounding — model is instructed to ONLY use provided context.
"""
from typing import List
from app.core.config import settings

SYSTEM_PROMPT = """You are a Campus Knowledge Assistant. Answer the student's question using ONLY the retrieved timetable chunks below. If the schedule does not contain data for a specific day (like Saturday), explicitly state that no academic data is available."""


def generate_answer(query: str, context_chunks: List[dict]) -> str:
    """
    Generate a grounded answer using retrieved chunks as context.
    Falls back to dev mode if GEMINI_API_KEY is not set.
    """
    if not context_chunks:
        return "I don't have information about this in the uploaded documents."

    if not settings.GEMINI_API_KEY:
        return _development_fallback(query, context_chunks)

    try:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            context_parts.append(f"[Source {i}]\n{chunk['text']}")
        context_text = "\n\n".join(context_parts)

        full_prompt = f"""{SYSTEM_PROMPT}

--- CONTEXT START ---
{context_text}
--- CONTEXT END ---

Student Question: {query}

Answer:"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )
        return response.text.strip()

    except Exception as e:
        return f"Error generating response: {str(e)}"


def _development_fallback(query: str, context_chunks: List[dict]) -> str:
    """Used when GEMINI_API_KEY is not set — shows raw retrieved context."""
    lines = [f"[DEV MODE — Gemini key not set]\n\nQuery: {query}\n\nRetrieved Context:"]
    for i, chunk in enumerate(context_chunks, 1):
        lines.append(f"\n--- Chunk {i} (score: {chunk['similarity_score']}) ---")
        lines.append(chunk["text"])
    return "\n".join(lines)
