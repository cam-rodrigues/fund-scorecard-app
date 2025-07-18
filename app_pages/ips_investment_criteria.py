import streamlit as st
import pdfplumber
import re

def run():
    st.set_page_config(page_title="Step 13: Extract Fund Info", layout="wide")
    st.title("Step 13: Ticker, Category, Benchmark (Ends with 'Index')")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step13_final_indexcheck")
    if not uploaded_file:
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # === Get TOC Page Numbers ===
            toc_text = pdf.pages[1].extract_text()
            def get_page(title):
                for line in toc_text.split("\n"):
                    if title in line:
                        match = re.search(r"(\d+)$", line)
                        return int(match.group(1)) if match else None
                return None

            perf_page = get_page("Fund Performance: Current vs. Proposed Comparison")
            if not perf_page:
                st.error("❌ Could not locate Fund Performance section.")
                return

            # === Extract Performance Lines ===
            perf_lines = []
            for page in pdf.pages[perf_page - 1:]:
                text = page.extract_text()
                if not text or "Fund Factsheets" in text:
                    break
                perf_lines.extend(text.split("\n"))

            results = []
            for idx in range(1, len(perf_lines) - 1):
                raw_fund_line = perf_lines[idx]
                fund_line = raw_fund_line.strip()
                raw_cat_line = perf_lines[idx - 1]
                cat_line = raw_cat_line.strip()

                # Fund Name + Ticker pattern
                m = re.match(r"^(.*?)([A-Z]{5})\s*$", fund_line)
                if not m:
                    continue

                fund_name = m.group(1).strip()
                ticker = m.group(2).strip()

                # Category check (1 line above, no digits, more left aligned)
                fund_indent = len(raw_fund_line) - len(raw_fund_line.lstrip())
                cat_indent = len(raw_cat_line) - len(raw_cat_line.lstrip())
                category = (
                    cat_line if cat_indent < fund_indent and not any(char.isdigit() for char in cat_line)
                    else "Unknown"
                )

                # Benchmark: next line, only if ends in "Index"
                raw_benchmark = perf_lines[idx + 1].strip() if idx + 1 < len(perf_lines) else ""
                benchmark = raw_benchmark if raw_benchmark.lower().endswith("index") else "Unknown"

                results.append({
                    "Fund Name": fund_name,
                    "Ticker": ticker,
                    "Category": category,
                    "Benchmark": benchmark
                })

            # === Display Results ===
            st.subheader("Fund Performance Info (Final Pass)")
            if not results:
                st.warning("No matching funds found.")
            else:
                for r in results:
                    st.markdown(f"### ✅ {r['Fund Name']}")
                    st.markdown(f"- **Ticker:** {r['Ticker']}")
                    st.markdown(f"- **Category:** {r['Category']}")
                    st.markdown(f"- **Benchmark:** {r['Benchmark']}")
                    st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error processing PDF: {e}")
