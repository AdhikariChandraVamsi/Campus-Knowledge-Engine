"""
PDF text extraction.
Peek-and-switch strategy: pdfplumber for table-heavy pages, PyMuPDF for text pages.
Returns a list of page-level results: {page_num, tables, text_blocks}
"""
from typing import List, Optional
import pdfplumber
import fitz  # PyMuPDF


def peek_page_type(page: pdfplumber.page.Page) -> str:
    """
    Determine if a page is primarily table-based or text-based.
    Table-heavy → 'table', text-heavy → 'text', mixed → 'mixed'
    """
    tables = page.find_tables()
    table_count = len(tables) if tables else 0

    if table_count >= 2:
        return "table"
    elif table_count == 1:
        return "mixed"
    return "text"


def extract_tables_from_page(page: pdfplumber.page.Page) -> List[List]:
    """Extract all tables from a page using pdfplumber spatial analysis."""
    tables = page.extract_tables()
    return tables if tables else []


def extract_text_from_page_pymupdf(pdf_path: str, page_num: int) -> str:
    """Extract plain text from a page using PyMuPDF (fast, for text-heavy pages)."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    text = page.get_text("text")
    doc.close()
    return text.strip()


def extract_pdf(file_path: str) -> List[dict]:
    """
    Main extraction function.
    Returns list of dicts, one per page:
    {page_num, page_type, tables: [...], text: "..."}
    """
    results = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_type = peek_page_type(page)

            page_result = {
                "page_num": page_num,
                "page_type": page_type,
                "tables": [],
                "text": "",
            }

            if page_type in ("table", "mixed"):
                page_result["tables"] = extract_tables_from_page(page)

            if page_type in ("text", "mixed"):
                # Use PyMuPDF for text blocks
                page_result["text"] = extract_text_from_page_pymupdf(
                    file_path, page_num
                )

            results.append(page_result)

    return results


def extract_timetable_data(pdf_path: str) -> dict:
    """
    Extracts unstructured timetable grids into structured JSON dictionary forms.
    Uses pdfplumber to safely read table contents directly matching requirements.
    Rules:
    - Tables[0] contains the Schedule Row/Cols.
    - Tables[1] contains the Meta details mapped (subject -> faculty & venues).
    Returns {"schedule": {...}, "meta": [...]}.
    """
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            return {"schedule": {}, "meta": []}
            
        page = pdf.pages[0]
        tables = page.extract_tables()
        
        schedule_table = tables[0] if len(tables) > 0 else []
        meta_table = tables[1] if len(tables) > 1 else []
        
        schedule_dict = {}
        if schedule_table and len(schedule_table) > 1:
            # Find the actual header row dynamically
            header_idx = 0
            for i, r in enumerate(schedule_table):
                if r and r[0] and "day" in str(r[0]).lower():
                    header_idx = i
                    break
                    
            raw_header = schedule_table[header_idx]
            header = [str(x).replace('\n', ' ').strip() if x else "" for x in raw_header]
            
            for row in schedule_table[header_idx + 1:]:
                if not row or not row[0]: continue
                day = str(row[0]).replace('\n', ' ').strip()
                if not day or day.lower() in ("day", "time/day", ""): continue
                
                day_schedule = []
                col_idx = 1
                while col_idx < len(row):
                    cell = row[col_idx]
                    h_val = header[col_idx] if col_idx < len(header) else ""
                    
                    # Valid if header has actual text and isn't a break/lunch column
                    is_valid_col = bool(h_val) and h_val.lower() not in ("-", "break", "lunch")
                    
                    if not cell or not is_valid_col:
                        col_idx += 1
                        continue
                        
                    cell_text = str(cell).replace('\n', ' ').strip()
                    check_text = cell_text.lower()
                    if not check_text or check_text in ("-", "free", "break", "lunch", "library", "none"):
                        col_idx += 1
                        continue
                        
                    # We found a legitimate subject! Let's check spans cleanly.
                    spanned_slots = [h_val]
                    
                    # Lookahead: aggregate subsequent None cells under valid slot headers
                    lookahead_idx = col_idx + 1
                    while lookahead_idx < len(row) and row[lookahead_idx] is None:
                        lh_val = header[lookahead_idx] if lookahead_idx < len(header) else ""
                        is_lh_valid = bool(lh_val) and lh_val.lower() not in ("-", "break", "lunch")
                        if is_lh_valid:
                            spanned_slots.append(lh_val)
                        lookahead_idx += 1
                        
                    time_slot_str = ", ".join(spanned_slots)
                    prefix = "Slots " if len(spanned_slots) > 1 else "Slot "
                    day_schedule.append({
                        "time": f"{prefix}{time_slot_str}" if time_slot_str.replace(', ','').isdigit() else time_slot_str,
                        "subject": cell_text
                    })
                    
                    # Fast forward cursor past the span
                    col_idx = lookahead_idx
                    
                # Assign non-empty arrays to schedule dictionary directly
                schedule_dict[day] = day_schedule
                
        meta_dict = []
        if meta_table and len(meta_table) > 1:
            meta_header = [str(x).replace('\n', ' ').strip() if x else "" for x in meta_table[0]]
            for row in meta_table[1:]:
                if not row or not row[0]: continue
                code_text = str(row[0]).replace('\n', ' ').strip()
                if not code_text: continue
                
                row_data = {}
                for col_idx, cell in enumerate(row):
                    h_val = meta_header[col_idx] if col_idx < len(meta_header) else f"Col{col_idx}"
                    c_val = str(cell).replace('\n', ' ').strip() if cell else ""
                    if h_val: row_data[h_val] = c_val
                meta_dict.append(row_data)

    return {"schedule": schedule_dict, "meta": meta_dict}
