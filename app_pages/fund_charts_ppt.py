import streamlit as st
import fitz  # PyMuPDF
import base64
import openai
import requests
import json
import re

# ========== CONFIG ==========
TOGETHER_MODEL = "togethercomputer/llava-1.5-7b-hf"
TOGETHER_API_KEY = st.secrets["together"]["api_key"]
OPENAI_API_KEY = st.secrets["openai"]["api_key"]
openai.api_key = OPENAI_API_KEY
OPENAI_MODEL = "gpt-4o"
FINANCIAL_TERMS = [
    "alpha", "beta", "sharpe ratio", "sortino ratio", "r-squared", "standard deviation",
    "information ratio", "expense ratio", "turnover", "fund exposure", "top 10 holdings",
    "downside risk", "trailing returns", "calendar year returns", "fund facts", "benchmark"
]

# ========== AI ANALYSIS FUNCTIONS ==========

def analyze_with_together(image_bytes):
    try:
        headers = {
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        }
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "model": TOGETHER_MODEL,
            "prompt": (
                "Extract key financial terms (like alpha, sharpe ratio, expense ratio) "
                "and fund name if available from this page. Return JSON like: "
                '{"terms": [...], "fund_name": "..."}'
            ),
            "image": b64,
        }
        res = requests.post("https://api.together.xyz/inference", headers=headers, data=json.dumps(payload))
        j = res.json()
        content = j.get("output") or j.get("choices", [{}])[0].get("text", "")
        return eval(content) if "{" in content else {"terms": [], "fund_name": None}
    except Exception as e:
        st.warning(f"[Together AI error] {e}")
        return {"terms": [], "fund_name": None}

def analyze_with_openai(image_bytes):
    try:
        result = openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You're a financial analyst reviewing a fund scorecard."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": (
                            "This is a page from an MPI report. Extract the fund name (if any), "
                            "and list any key financial metrics like alpha, expense ratio, sharpe ratio, benchmark. "
                            "Return only a JSON object like: {\"terms\": [...], \"fund_name\": \"...\"}"
                        )},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"}}
                    ]
                }
            ],
            temperature=0.2,
            max_tokens=300
        )
        content = result.choices[0].message.content
        return eval(content.strip()) if content.startswith("{") else {"terms": [], "fund_name": None}
    except Exception as e:
        st.warning(f"[OpenAI fallback failed] {e}")
        return {"terms": [], "fund_name": None}

# ========== MAIN TOOL ==========
def run():
    st.title("🔍 PDF Financial Term & Fund Navigator")
    st.markdown("Upload an MPI-style PDF. This tool extracts financial terms and fund sections, then lets you navigate to them.")

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
    if not pdf_file:
        return

    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    hits = {}  # { "alpha": [12, 13], "Vanguard Windsor II": [46] }

    with st.spinner("Scanning PDF..."):
        for i, page in enumerate(doc):
            text = page.get_text()
            image = page.get_pixmap(dpi=150).tobytes("png")
            found = []

            # Fast: detect keywords in text
            for term in FINANCIAL_TERMS:
                if re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE):
                    hits.setdefault(term.lower(), []).append(i)

            # Detect fund header (basic)
            match = re.search(r"([A-Z][a-z]+ ){1,5}(Fund|Index|Institutional|Admiral|Retirement)", text)
            if match:
                fund_name = match.group().strip()
                hits.setdefault(fund_name, []).append(i)
            else:
                # Use AI if no match
                result = analyze_with_together(image)
                if not result["terms"] and not result["fund_name"]:
                    result = analyze_with_openai(image)
                for term in result["terms"]:
                    hits.setdefault(term.lower(), []).append(i)
                if result["fund_name"]:
                    hits.setdefault(result["fund_name"], []).append(i)

    if not hits:
        st.error("No financial terms or fund sections found.")
        return

    options = sorted(hits.keys())
    selected = st.selectbox("Select a financial term or fund section:", options)
    page_nums = sorted(set(hits[selected]))

    st.markdown(f"### Showing {len(page_nums)} page(s) for: `{selected}`")

    for page_num in page_nums:
        st.markdown(f"#### Page {page_num + 1}")
        st.image(doc[page_num].get_pixmap(dpi=150).tobytes("png"), use_container_width=True)
        st.code(doc[page_num].get_text())

