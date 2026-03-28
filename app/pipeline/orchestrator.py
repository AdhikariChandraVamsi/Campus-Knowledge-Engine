"""
Pipeline orchestrator with logging.
Ties together: extractor → preprocessor → chunker → vector store.
"""
import logging
from datetime import datetime

from app.models.document import Document, DocumentType
from app.pipeline.extractor import extract_pdf
from app.pipeline.preprocessor import clean_table, clean_text_block
from app.pipeline.chunker import chunk_timetable, chunk_text_document
from app.services.vector_service import store_chunks

logging.basicConfig(level=logging.INFO, format="%(asctime)s [PIPELINE] %(message)s")
log = logging.getLogger(__name__)


def process_document(doc: Document) -> int:
    """
    Full pipeline for one document.
    Returns number of chunks created and stored.
    """
    log.info(f"Starting pipeline for document: {doc.id}")
    log.info(f"Type: {doc.document_type.value} | Dept: {doc.department} | Sem: {doc.semester} | Section: {doc.section}")

    # Step 1: Extract
    log.info(f"Extracting PDF: {doc.file_path}")
    pages = extract_pdf(doc.file_path)
    log.info(f"Extracted {len(pages)} pages")

    metadata = {
        "document_id": doc.id,
        "university_id": doc.university_id,
        "document_type": doc.document_type.value,
        "department": doc.department,
        "semester": doc.semester or "",
        "section": doc.section or "",
        "subject_code": doc.subject_code or "",
        "subject_name": doc.subject_name or "",
        "regulation": doc.regulation or "",
        "academic_year": doc.academic_year or "",
    }

    chunks = []

    if doc.document_type == DocumentType.TIMETABLE:
        all_tables = []
        for page in pages:
            log.info(f"  Page {page['page_num']}: type={page['page_type']} | tables={len(page.get('tables', []))}")
            for table in page.get("tables", []):
                cleaned = clean_table(table)
                if cleaned:
                    all_tables.append(cleaned)
                    log.info(f"    Table: {len(cleaned)} rows x {len(cleaned[0]) if cleaned else 0} cols")

        log.info(f"Total tables collected: {len(all_tables)}")
        chunks = chunk_timetable(all_tables, metadata)

    else:
        full_text = ""
        for page in pages:
            if page.get("text"):
                full_text += clean_text_block(page["text"]) + "\n\n"
            for table in page.get("tables", []):
                cleaned = clean_table(table)
                for row in cleaned:
                    row_text = " | ".join(cell for cell in row if cell)
                    if row_text:
                        full_text += row_text + "\n"

        log.info(f"Total text extracted: {len(full_text)} chars")
        chunks = chunk_text_document(full_text.strip(), metadata)

    log.info(f"Chunks created: {len(chunks)}")

    if not chunks:
        log.warning("No chunks generated — check PDF format")
        return 0

    # Preview first chunk
    if chunks:
        log.info(f"Sample chunk[0]: {chunks[0]['text'][:200]}...")

    # Step 2: Store in ChromaDB
    log.info("Storing chunks in ChromaDB...")
    count = store_chunks(chunks, doc.id, doc.university_id)
    log.info(f"✅ Pipeline complete — {count} chunks indexed")

    return count
