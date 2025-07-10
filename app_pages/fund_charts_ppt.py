import os
import fitz  # PyMuPDF
import requests
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches, Pt
from PIL import Image
import streamlit as st
import base64

API_KEY = st.secrets["api_key"]  # or use os.environ["TOGETHER_API_KEY"]
TOGETHER_MODEL = "togethercomputer/llava-1.5-7b-hf"
API_URL = "https://api.together.xyz/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

def extract_image_from_page(page):
    pix = page.get_pixmap(dpi=200)
    img_bytes = pix.tobytes("png")
    return img_bytes

def analyze_page(image_bytes):
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = (
        "You are analyzing a page from a fund performance report.\n"
        "1. What is the **fund name** shown on the page?\n"
        "2. Does this page contain any charts or tables?\n"
        "Return your response in this JSON format:\n"
        '{"fund_name": "...", "contains_chart_or_table": true/false}'
    )

    data = {
        "model": TOGETHER_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful financial assistant."},
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

    res = requests.post(API_URL, headers=HEADERS, json=data)
    try:
        response_text = res.json()["choices"][0]["message"]["content"]
        parsed = eval(response_text.strip())
        return parsed
    except Exception as e:
        return {"fund_name": "Unknown Fund", "contains_chart_or_table": False}

def extract_and_classify_fund_pages(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    fund_to_images = {}
    for i in range(35, len(doc)):  # Page 36 onward
        page = doc[i]
        img_bytes = extract_image_from_page(page)
        result = analyze_page(img_bytes)

        if result["contains_chart_or_table"]:
            fund = result["fund_name"] or "Unknown Fund"
            fund_to_images.setdefault(fund, []).append(img_bytes)
    return fund_to_images

def build_powerpoint(fund_to_images):
    prs = Presentation()
    blank = prs.slide_layouts[6]

    for fund, images in fund_to_images.items():
        for i, image in enumerate(images):
            slide = prs.slides.add_slide(blank)
            slide.shapes.add_picture(BytesIO(image), Inches(0.5), Inches(0.75), width=Inches(8.5))
            txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.5))
            p = txBox.text_frame.paragraphs[0].add_run()
            p.text = f"{fund} (Image {i+1}/{len(images)})"
            p.font.size = Pt(16)
            p.font.bold = True
    return prs

def run():
    st.set_page_config(layout="wide")
    st.title("🧠 AI-Powered Fund Chart Extractor")
    uploaded_pdf = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if uploaded_pdf:
        with st.spinner("Analyzing pages with Together AI..."):
            results = extract_and_classify_fund_pages(uploaded_pdf)
            if not results:
                st.error("No charts or tables found.")
                return

            prs = build_powerpoint(results)
            buffer = BytesIO()
            prs.save(buffer)
            buffer.seek(0)

            total = sum(len(v) for v in results.values())
            st.success(f"✅ Extracted {total} charts from {len(results)} funds.")
            st.download_button("📥 Download PowerPoint", buffer, "fund_charts_ai.pptx")

if __name__ == "__main__":
    try:
        import streamlit.runtime
        run()
    except ImportError:
        print("Streamlit runtime not detected.")
