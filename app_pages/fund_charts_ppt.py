import streamlit as st
import fitz  # PyMuPDF
import base64
import requests
from io import BytesIO
from collections import defaultdict

# === Setup Together API ===
TOGETHER_API_KEY = st.secrets["together"]["api_key"]
TOGETHER_MODEL = "togethercomputer/llava-1.5-7b-hf"
API_URL = "https://api.together.xyz/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

FINANCIAL_TERMS = [
    "performance", "returns", "expense ratio", "risk", "benchmark", "alpha",
    "beta", "standard deviation", "sharpe ratio", "style box",
    "drawdown", "volatility", "asset allocation", "top holdings"
]

def analyze_page_with_ai(image_bytes):
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = (
        "You're looking at a page from an investment report.\n"
        "Return a list of financial terms (e.g., performance, expense ratio, risk) that appear or are discussed on this page.\n"
        "Also, if this page is the beginning of a fund section (like XYZ GROWTH FUND), extract that fund name.\n"
        "Respond in this format:\n"
        '{"terms": [...], "fund_name": "..."}'
    )

    payload = {
        "model": TOGETHER_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful financial analyst."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 200
    }

    try:
        res = requests.post(API_URL, headers=HEADERS, json=payload)
        raw = res.json()["choices"][0]["message"]["content"]
        return eval(raw.strip())
    except Exception as e:
        st.error(f"AI error: {e}")
        return {"terms": [], "fund_name": None}

def extract_keywords_and_funds(pdf):
    doc = fitz.open(stream=pdf.read(), filetype="pdf")
    term_pages = defaultdict(list)
    fund_pages = {}

    for i, page in enumerate(doc):
        page_num = i + 1
        text = page.get_text().lower()

        # Quick scan for financial terms
        for term in FINANCIAL_TERMS:
            if term in text:
                term_pages[term].append(page_num)

        # Quick scan for fund header
        for line in text.splitlines():
            if line.strip().isupper() and "fund" in line.lower() and 5 < len(line) < 80:
                fund_pages[line.strip()] = page_num
                break  # only grab first match per page

        # If weak or no data, fallback to vision
        if page_num >= 30 and (page_num not in sum(term_pages.values(), []) or page_num not in fund_pages.values()):
            img = page.get_pixmap(dpi=150).tobytes("png")
            ai_result = analyze_page_with_ai(img)
            for term in ai_result["terms"]:
                term_pages[term.lower()].append(page_num)
            if ai_result.get("fund_name"):
                fund_pages[ai_result["fund_name"].strip()] = page_num

    return term_pages, fund_pages, doc

def run():
    st.set_page_config(layout="wide")
    st.title("🔍 PDF Financial Term & Fund Navigator")
    st.markdown("Upload an MPI-style PDF. This tool will extract financial terms and fund sections, then let you navigate to them.")

    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded_pdf:
        with st.spinner("Analyzing PDF with Together AI..."):
            term_pages, fund_pages, doc = extract_keywords_and_funds(uploaded_pdf)

        all_options = list(term_pages.keys()) + list(fund_pages.keys())
        selected = st.selectbox("Select a financial term or fund section:", sorted(set(all_options)))

        if selected:
            pages = term_pages.get(selected, [])
            if not pages and selected in fund_pages:
                pages = [fund_pages[selected]]

            st.info(f"Showing {len(pages)} page(s) for: **{selected}**")

            for p in pages:
                st.subheader(f"Page {p}")
                text = doc[p-1].get_text()
                st.text_area(f"Text from Page {p}", text, height=200)

                img = doc[p-1].get_pixmap(dpi=150).tobytes("png")
                st.image(img, caption=f"Preview of Page {p}", use_column_width=True)

