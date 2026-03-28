"""
Data cleaning after extraction.
Handles: None propagation for merged cells, newline splitting,
unicode normalization, break slot removal.
"""
import re
import unicodedata
from typing import List, Optional


BREAK_KEYWORDS = {"interval break", "lunch break", "break", "", "none"}

ABBREVIATION_MAP = {
    "thur": "Thursday",
    "wed": "Wednesday",
    "mon": "Monday",
    "tue": "Tuesday",
    "fri": "Friday",
    "ab iii": "Academic Block 3",
    "ab3": "Academic Block 3",
    "ab-3": "Academic Block 3",
    "tf": "Top Floor",
    "sf": "Second Floor",
    "cp lab": "Computer Lab",
    "(t)": "Tutorial",
    "b.tech": "B.Tech",
}


def normalize_text(text: str) -> str:
    """Standard text normalization pipeline."""
    if not text:
        return ""
    # Unicode normalization
    text = unicodedata.normalize("NFKC", text)
    # Strip control characters
    text = re.sub(r"[\x00-\x08\x0b\x0e-\x1f]", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    # Non-breaking spaces
    text = text.replace("\xa0", " ")
    return text.strip()


def expand_abbreviations(text: str) -> str:
    """Expand known academic abbreviations."""
    lower = text.lower()
    for abbr, full in ABBREVIATION_MAP.items():
        lower = lower.replace(abbr, full)
    return lower


def propagate_merged_cells(row: List) -> List[str]:
    """
    Fill None values (merged cells from pdfplumber) with previous non-None value.
    Keeps break/null slots as empty strings.
    """
    result = []
    last_value = ""
    for cell in row:
        if cell is None:
            result.append(last_value)
        else:
            cleaned = normalize_text(str(cell))
            last_value = cleaned
            result.append(cleaned)
    return result


def is_break_slot(cell_value: str) -> bool:
    """Return True if the slot is a break/free period (should not be embedded)."""
    return cell_value.lower().strip() in BREAK_KEYWORDS


def clean_table(raw_table: List[List]) -> List[List[str]]:
    """Clean a full table: propagate merged cells, normalize each cell."""
    cleaned = []
    for row in raw_table:
        cleaned_row = propagate_merged_cells(row)
        cleaned.append(cleaned_row)
    return cleaned


def clean_text_block(text: str) -> str:
    """Clean a raw text block from PyMuPDF."""
    text = normalize_text(text)
    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text
