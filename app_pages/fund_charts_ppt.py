import fitz  # PyMuPDF
from pptx import Presentation
from pptx.util import Inches, Pt
from io import BytesIO
import re
import streamlit as st

# === Robust Fund Name Detection ===
def extract_fund_name(text):
    lines = text.strip().split("\n")
    for line in lines:
        if re.search(r"(FUND\s+|FUND$|FUND\()", line.upper()) and len(line.strip().split()) >= 3:
            return line.strip()
        if line.isupper() and len(line.split()) >= 2 and len(line) <= 80:
            return line.strip()
    return None

# === Extract Charts Grouped by Fund ===
def extract_fund_charts(pdf_file, start_page=36):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    fund_to_images = {}
    current_fund = "Unnamed Fund"

    for page_num in range(start_page - 1, len(doc)):
        page = doc[page_num]
        text = page.get_text()
        new_fund = extract_fund_name(text)
        if new_fund:
            current_fund = new_fund

        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            image_info = doc.extract_image(xref)
            image_bytes = image_info["image"]
            fund_to_images.setdefault(current_fund, []).append(image_bytes)

    return fund_to_images

# === Build PowerPoint with Slide per Image ===
def build_powerpoint(fund_to_images):
    prs = Presentation()
    blank_layout = prs.slide_layouts[6]

    for fund, images in fund_to_images.items():
        for i, image_bytes in enumerate(images):
            slide = prs.slides.add_slide(blank_layout)
            left = Inches(0.5)
            top = Inches(0.75)
            width = Inches(8.5)
            slide.shapes.add_picture(BytesIO(image_bytes), left, top, width=width)

            txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.5))
            tf = txBox.text_frame
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = f"{fund} (Image {i+1}/{len(images)})"
            run.font.size = Pt(16)
            run.font.bold = True

    return prs

# === Streamlit UI ===
def run():
    st.set_page_config(layout="wide")
    st.title("📈 MPI Fund Chart Converter")
    st.markdown("Upload an MPI PDF. This tool extracts all charts and associates them with the correct fund name, then compiles everything into a PowerPoint.")

    uploaded_pdf = st.file_uploader("Upload MPI PDF", type=["pdf"])
    if uploaded_pdf:
        with st.spinner("Analyzing fund pages..."):
            fund_charts = extract_fund_charts(uploaded_pdf)

            if not fund_charts:
                st.error("No charts found.")
                return

            pptx_buffer = BytesIO()
            prs = build_powerpoint(fund_charts)
            prs.save(pptx_buffer)
            pptx_buffer.seek(0)

            total_images = sum(len(v) for v in fund_charts.values())
            st.success(f"✅ Compiled {total_images} charts from {len(fund_charts)} funds.")

            st.download_button(
                label="📥 Download PowerPoint",
                data=pptx_buffer,
                file_name="fund_charts.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )

# === For direct run ===
if __name__ == "__main__":
    try:
        import streamlit.runtime
        run()
    except ImportError:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("pdf", type=str)
        parser.add_argument("output", type=str)
        args = parser.parse_args()
        with open(args.pdf, "rb") as f:
            fund_charts = extract_fund_charts(f)
        if not fund_charts:
            print("No charts found.")
        else:
            prs = build_powerpoint(fund_charts)
            prs.save(args.output)
            print("PowerPoint saved.")
