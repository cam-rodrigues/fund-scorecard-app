import pdfplumber
from typing import List
import re
from difflib import SequenceMatcher

try:
    from rapidfuzz.fuzz import ratio as fuzzy_ratio
except ImportError:
    def fuzzy_ratio(a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100


def extract_data_from_pdf(pdf_path: str, start_page: int, end_page: int) -> List[str]:
    """
    Extracts fund names from a PDF between the given page range.

    Args:
        pdf_path (str): Path to the PDF file.
        start_page (int): First page to extract from (1-based).
        end_page (int): Last page to extract from (1-based).

    Returns:
        List[str]: A list of extracted fund names.
    """
    fund_names = []
    seen = set()

    with pdfplumber.open(pdf_path) as pdf:
        for i in range(start_page - 1, end_page):
            page = pdf.pages[i]
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            for idx, line in enumerate(lines):
                line = line.strip()
                if "Manager Tenure" in line and idx > 0:
                    possible_fund = lines[idx - 1].strip()
                    if possible_fund and possible_fund not in seen:
                        fund_names.append(possible_fund)
                        seen.add(possible_fund)

    return fund_names


def similarity_score(a: str, b: str) -> float:
    """
    Computes a fuzzy similarity score between two strings.

    Args:
        a (str): First string.
        b (str): Second string.

    Returns:
        float: Similarity score between 0 and 100.
    """
    return fuzzy_ratio(a, b)
