import time
import streamlit as st
from rapidfuzz import process
import logging
import pdfplumber

# ===== Logger Setup =====
logger = logging.getLogger("FidSync")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# ===== API Key Handling =====
def get_api_key():
    if "together_api_key" not in st.session_state:
        st.session_state["together_api_key"] = st.secrets.get("together_api_key")
    return st.session_state["together_api_key"]

# ===== Fund Matching with Caching =====
@st.cache_data
def get_fuzzy_matches(fund_list, options_list):
    return {f: process.extractOne(f, options_list) for f in fund_list}

# ===== PDF Safety Extraction =====
def extract_text_safe(pdf_file):
    texts = []
    with pdfplumber.open(pdf_file) as pdf:
        for i, page in enumerate(pdf.pages):
            try:
                text = page.extract_text()
                if text:
                    texts.append(text)
                else:
                    logger.warning(f"Page {i+1} had no readable text.")
            except Exception as e:
                logger.warning(f"Skipping unreadable page {i+1}: {e}")
    return texts

# ===== Retry Logic for API Calls =====
def retry_api_call(func, max_attempts=3, delay_base=2):
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            logger.warning(f"API call failed (attempt {attempt+1}): {e}")
            time.sleep(delay_base * (attempt + 1))
    raise Exception("API call failed after multiple retries.")

# ===== Normalize Fund Names =====
def normalize_fund_names(name_list):
    return [n.lower().strip() for n in name_list]

# ===== Reject Bad PDFs =====
def is_valid_pdf(text_pages):
    return len(text_pages) >= 5 and any(text_pages)

# ===== Watchlist Fallback =====
def extract_watchlist_status(text_block):
    line = text_block.lower()
    if "meets watchlist criteria" in line:
        return "Pass"
    elif "placed on watchlist" in line:
        return "Fail"
    else:
        return "Unknown"

# ===== Clipboard Preview Helper =====
def parse_clipboard_options(raw_text):
    options = [line.strip() for line in raw_text.splitlines() if line.strip()]
    return options

# ===== UI Helper: Help Tooltips =====
def checkbox_with_help(label, help_text):
    return st.checkbox(label, help=help_text)

# ===== Logging Tool =====
def log_processing_summary(fund_count, failed_pages, time_taken):
    logger.info(f"Processed {fund_count} funds in {time_taken:.2f}s with {failed_pages} page failures.")




## To Paste Into .Pys
  #from utils.stability_enhancer import (
      get_api_key,
      get_fuzzy_matches,
      extract_text_safe,
      retry_api_call,
      normalize_fund_names,
      is_valid_pdf,
      extract_watchlist_status,
      parse_clipboard_options,
      checkbox_with_help,
      log_processing_summary
  )

