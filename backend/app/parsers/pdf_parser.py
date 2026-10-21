import os
import re
from typing import Tuple, List, Optional
import pymupdf as fitz

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

def extract_pdf_layout_aware(pdf_path: str) -> Tuple[str, List[str]]:
    """
    Hybrid PDF Parsing Engine (PyMuPDF + pdfplumber):
    - PyMuPDF (Tier 1): High-speed (15x-30x faster) layout-aware block sorting,
      two-column reading order, and hidden text/prompt-injection inspection.
    - pdfplumber (Tier 2): Surgical table extraction when visual line drawings
      or structured tables are detected, preventing table cell mangling.
    """
    review_flags: List[str] = []
    text_blocks_ordered: List[str] = []

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return "", [f"pdf_open_failed: {str(e)}"]

    has_tables_to_extract = False
    pages_with_tables: List[int] = []

    for page_idx in range(len(doc)):
        try:
            page = doc[page_idx]
            page_width = page.rect.width
            page_height = page.rect.height

            # Anti-Injection / White-Text Check (Catch 3):
            # Inspect raw dict spans for invisible or near-zero font sizes or #FFFFFF color
            try:
                page_dict = page.get_text("dict")
                for block in page_dict.get("blocks", []):
                    if block.get("type") == 0:  # text
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                font_size = span.get("size", 10)
                                color = span.get("color", 0)
                                text_val = span.get("text", "").strip()
                                # Flag micro-fonts (< 3.0 pt) or white text (#FFFFFF or 16777215)
                                if text_val and (font_size < 3.0 or color == 16777215):
                                    review_flags.append(f"page_{page_idx+1}_invisible_text_detected: {text_val[:40]}")
            except Exception:
                pass

            # Detect if page contains vector line drawings (often indicates tables/grid borders)
            drawings = page.get_drawings()
            if len(drawings) >= 8:
                pages_with_tables.append(page_idx)
                has_tables_to_extract = True

            # Get blocks: (x0, y0, x1, y1, text, block_no, block_type)
            blocks = page.get_text("blocks")
            # Filter text blocks only (block_type 0)
            text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]

            if not text_blocks:
                continue

            # Detect whether page is multi-column:
            left_blocks = []
            right_blocks = []
            full_width_blocks = []

            # 45% threshold for left column, 55% for right
            column_split = page_width * 0.45

            is_two_column = False
            left_count = sum(1 for b in text_blocks if b[2] <= column_split + 20)
            right_count = sum(1 for b in text_blocks if b[0] >= column_split - 20)

            if left_count >= 2 and right_count >= 2:
                is_two_column = True
                review_flags.append(f"page_{page_idx+1}_two_column_layout_detected")

            if is_two_column:
                for b in text_blocks:
                    x0, y0, x1, y1, content = b[0], b[1], b[2], b[3], b[4].strip()
                    # If span is across both columns, treat as header/full-width
                    if x0 < column_split and x1 > (page_width * 0.65):
                        full_width_blocks.append((y0, content))
                    elif x1 <= column_split + 30:
                        left_blocks.append((y0, content))
                    else:
                        right_blocks.append((y0, content))

                # Sort top-to-bottom within each group
                left_blocks.sort(key=lambda item: item[0])
                right_blocks.sort(key=lambda item: item[0])
                full_width_blocks.sort(key=lambda item: item[0])

                # Combine: headers/full-width, then left sidebar, then right main content
                if full_width_blocks:
                    text_blocks_ordered.extend([t[1] for t in full_width_blocks])
                text_blocks_ordered.extend([t[1] for t in left_blocks])
                text_blocks_ordered.extend([t[1] for t in right_blocks])
            else:
                # Single column: sort by vertical position (y0), then horizontal (x0)
                text_blocks.sort(key=lambda b: (round(b[1] / 10) * 10, b[0]))
                text_blocks_ordered.extend([b[4].strip() for b in text_blocks])

        except Exception as pe:
            review_flags.append(f"page_{page_idx+1}_extract_error: {str(pe)}")

    # Tier 2: Surgical pdfplumber Table Extraction for pages with detected tables
    if HAS_PDFPLUMBER and pages_with_tables:
        try:
            with pdfplumber.open(pdf_path) as p_pdf:
                for p_num in pages_with_tables:
                    if p_num < len(p_pdf.pages):
                        tables = p_pdf.pages[p_num].extract_tables()
                        for t_idx, table in enumerate(tables):
                            if table and len(table) > 1:
                                review_flags.append(f"page_{p_num+1}_table_extracted_via_pdfplumber")
                                table_rows = []
                                for row in table:
                                    clean_row = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
                                    if clean_row:
                                        table_rows.append(" | ".join(clean_row))
                                if table_rows:
                                    text_blocks_ordered.append("\n[Structured Table Data]\n" + "\n".join(table_rows))
        except Exception as table_err:
            review_flags.append(f"pdfplumber_table_note: {str(table_err)[:60]}")

    full_text = "\n\n".join(text_blocks_ordered)
    # Basic cleanup: remove null bytes and excessive repeated spaces
    full_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', full_text)
    full_text = re.sub(r'[ \t]+', ' ', full_text)
    full_text = re.sub(r'\n{3,}', '\n\n', full_text)

    return full_text.strip(), review_flags
