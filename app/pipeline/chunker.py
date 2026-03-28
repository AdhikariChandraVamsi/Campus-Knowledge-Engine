"""
Chunking strategy — converts cleaned data into retrievable text chunks.
Design philosophy from architecture doc:
- Each chunk must be self-contained (readable without surrounding context)
- Every chunk carries all metadata needed to understand it
- Timetable: one chunk per day + one per course + one meta chunk
- Text documents: paragraph/section-based with overlap
"""
import uuid
from typing import List, Dict


def make_chunk_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def chunk_timetable(
    structured_data: dict,
    metadata: dict,
) -> List[dict]:
    """
    Timetable-specific chunking.
    structured_data comes directly from extract_timetable_data.
    Returns list of chunk dicts: {id, text, metadata}
    """
    chunks = []
    doc_id = metadata.get("document_id", "unknown")
    university_id = metadata.get("university_id", "unknown")
    dept = metadata.get("department", "")
    semester = metadata.get("semester", "")
    section = metadata.get("section", "")

    base_meta = {
        "university_id": university_id,
        "document_id": doc_id,
        "document_type": "timetable",
        "dept": dept,
        "semester": semester,
        "section": section,
        "regulation": metadata.get("regulation", ""),
        "academic_year": metadata.get("academic_year", ""),
    }

    schedule = structured_data.get("schedule", {})
    meta = structured_data.get("meta", [])

    # Day Chunks: 5 chunks usually
    for day, day_slots in schedule.items():
        if not day_slots: continue
        # Target format: "Day Schedule for [Dept] [Sem] [Section] on Monday: 08:50 AM - 09:40 AM is Machine Learning (23CSE301)..."
        slot_texts = []
        for slot in day_slots:
            slot_texts.append(f"{slot['time']} is {slot['subject']}")
        
        full_day_text = f"Day Schedule for {dept} {semester} {section} on {day}: " + ", ".join(slot_texts)
        
        chunk_meta = {**base_meta, "day": day}
        chunks.append({
            "id": make_chunk_id(f"tt_{dept}_{section}_{semester}_{day[:3].lower()}"),
            "text": full_day_text,
            "metadata": chunk_meta,
        })

    # Meta Chunks
    if meta:
        meta_texts = []
        for row in meta:
            details = ", ".join([f"{k}: {v}" for k, v in row.items() if v])
            meta_texts.append(details)
            
        meta_full_text = f"Course Details for {dept} {semester} {section}: " + " | ".join(meta_texts)
        chunks.append({
            "id": make_chunk_id(f"tt_meta_{dept}_{section}_{semester}"),
            "text": meta_full_text,
            "metadata": base_meta,
        })

    return chunks


def _is_break(cell: str) -> bool:
    """Check if cell content is a break/free slot."""
    from app.pipeline.preprocessor import is_break_slot
    return is_break_slot(cell)


def chunk_text_document(
    text: str,
    metadata: dict,
    chunk_size: int = 500,
    overlap: int = 100,
) -> List[dict]:
    """
    Generic text chunking with overlap.
    Used for syllabus, PYQ, evaluation documents.
    Splits on paragraphs first, then by character count.
    Overlap ensures context isn't lost at chunk boundaries.
    """
    chunks = []
    doc_id = metadata.get("document_id", "unknown")

    # Split into paragraphs first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            if current_chunk:
                chunks.append(_make_text_chunk(current_chunk, metadata))
            # Start new chunk with overlap from previous
            if len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:] + "\n\n" + para
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(_make_text_chunk(current_chunk, metadata))

    return chunks


def _make_text_chunk(text: str, metadata: dict) -> dict:
    base_meta = {
        "university_id": metadata.get("university_id", ""),
        "document_id": metadata.get("document_id", ""),
        "document_type": metadata.get("document_type", "other"),
        "dept": metadata.get("department", ""),
        "semester": metadata.get("semester", ""),
        "section": metadata.get("section", ""),
    }
    return {
        "id": make_chunk_id("chunk"),
        "text": text,
        "metadata": base_meta,
    }
