import streamlit as st
import pdfplumber
import re

def run():
    st.set_page_config(page_title="Step 13: Extract Fund Performance Info", layout="wide")
    st.title("Step 13: Ticker, Category, Benchmark from Layout Pattern")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step13_blockscan")
    if not uploaded_file:
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # === Get TOC and Page Numbers ===
            toc_text = pdf.pages[1].extract_text()

            def get_page(section_title):
                for line in toc_text.split("\n"):
                    if section_title in line:
                        m = re.search(r"(\d+)$", line)
                        return int(m.group(1)) if m else None
                return None

            perf_page = get_page("Fund Performance: Current vs. Proposed Comparison")
            if not perf_page:
                st.error("❌ Could not find Fund Performance section.")
                return

            # === Read all lines from Fund Performance section ===
            perf_lines = []
            for page in pdf.pages[perf_page - 1:]:
                text = page.extract_text()
                if not text or "Fund Factsheets" in text:
                    break
                perf_lines.extend(text.split("\n"))

            results = []
            for i in range(len(perf_lines) - 2):
                cat_line = perf_lines[i].strip()
                fund_line = perf_lines[i + 1].strip()
                bench_line = perf_lines[i + 2].strip()

                # Detect ticker at end of fund line
                fund_match = re.match(r"^(.*?)([A-Z]{5})\s*$", fund_line)
                if fund_match and not any(char.isdigit() for char in cat_line):
                    fund_name = fund_match.group(1).strip()
                    ticker = fund_match.group(2).strip()
                    category = cat_line
                    benchmark = bench_line

                    results.append({
                        "Fund Name": fund_name,
                        "Ticker": ticker,
                        "Category": category,
                        "Benchmark": benchmark
                    })

            # === Display Results ===
            st.subheader("Extracted Fund Performance Info")
            if not results:
                st.warning("No matching fund blocks found.")
            else:
                for r in results:
                    st.markdown(f"### ✅ {r['Fund Name']}")
                    st.markdown(f"- **Ticker:** {r['Ticker']}")
                    st.markdown(f"- **Category:** {r['Category']}")
                    st.markdown(f"- **Benchmark:** {r['Benchmark']}")
                    st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error processing PDF: {e}")
