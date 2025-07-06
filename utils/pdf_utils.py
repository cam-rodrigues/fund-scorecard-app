import pdfplumber
import io

def extract_data_from_pdf(pdf_bytes, start_page=1, end_page=1):
    """
    Extracts all text from a given page range of the PDF.
    Returns a single string with the combined content.
    """
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = pdf.pages[start_page - 1:end_page]
            content = "\n".join(page.extract_text() for page in pages if page.extract_text())
        return content
    except Exception as e:
        raise RuntimeError(f"Failed to extract PDF text: {e}")
