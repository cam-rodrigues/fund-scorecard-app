import fitz  # PyMuPDF
from pptx import Presentation
from pptx.util import Inches, Pt
from io import BytesIO
import re
import streamlit as st

# ======================
# FUND NAME EXTRACTOR — Advanced Logic
# ======================
def extract_fund_name(text):
    lines = text.strip().split("\n")
    for line in lines:
        line_clean = line.strip()
        # Match if line contains the word "Fund" and is reasonably long
        if re.search(r"\bFund\b", line_clean, re.IGNORECASE) and len(line_clean.split()) >= 3:
            return line_clean
        # Fallback: ALL CAPS short line, likely a title
        if line_clean.isupper() and len(line_clean.split()) >= 2 and len(line_clean) < 80:
            return line_clean
    return "Unnamed Fund"

# ======================
# PDF IMAGE EXTRACTOR
# ======================
def extract_fund_charts(pdf_file, start_page=36):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    fund_to_images = {}

    for page_num in range(start_page - 1, len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if not text.strip():
            continue

        fund_name = extract_fund_name(text)
        if not fund_name:
            continue

        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            image_info = doc.extract_image(xref)
            image_bytes = image_info["image"]
            fund_to_images.setdefault(fund_name, []).append(image_bytes)

    return fund_to_images

# ======================
# POWERPOINT GENERATOR
# ======================
def build_powerpoint(fund_to_images):
    prs = Presentation()
    blank_layout = prs.slide_layouts[6]  # Titleless layout

    for fund, images in fund_to_images.items():
        for i, image_bytes in enumerate(images):
            slide = prs.slides.add_slide(blank_layout)
            left = Inches(0.5)
            top = Inches(0.75)
            width = Inches(8.5)

            # Add image
            slide.shapes.add_picture(BytesIO(image_bytes), left, top, width=width)

            # Add fund title
            txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.5))
            tf = txBox.text_frame
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = f"{fund} (Image {i+1}/{len(images)})"
            run.font.size = Pt(16)
            run.font.bold = True

    return prs

# ======================
# STREAMLIT APP
# ======================
def run():
    st.set_page_config(layout="wide")
    st.title("📈 Fund Chart Converter")
    st.markdown("This tool extracts all fund charts from an MPI-style PDF (starting at page 36) and compiles them into a PowerPoint presentation.")

    uploaded_pdf = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if uploaded_pdf:
        with st.spinner("Extracting fund images..."):
            fund_charts = extract_fund_charts(uploaded_pdf)

            if not fund_charts:
                st.error("❌ No charts found after page 36.")
                return

            prs = build_powerpoint(fund_charts)
            output = BytesIO()
            prs.save(output)
            output.seek(0)

            total_images = sum(len(v) for v in fund_charts.values())
            st.success(f"✅ Created presentation with {total_images} charts across {len(fund_charts)} funds.")

            st.download_button("📥 Download PowerPoint", output, "fund_charts.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

# ======================
# RUN APP
# ======================
if __name__ == "__main__":
    try:
        import streamlit.runtime
        run()
    except ImportError:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("pdf", type=str, help="Path to MPI PDF")
        parser.add_argument("output", type=str, help="Path to save PowerPoint")
        args = parser.parse_args()

        with open(args.pdf, "rb") as f:
            fund_charts = extract_fund_charts(f)

        if not fund_charts:
            print("❌ No charts found.")
        else:
            prs = build_powerpoint(fund_charts)
            prs.save(args.output)
            print(f"✅ Saved presentation with {sum(len(v) for v in fund_charts.values())} charts.")

