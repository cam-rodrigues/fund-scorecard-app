import re
import streamlit as st
import pdfplumber
import pandas as pd

# === Utility: Extract Quarter from Date String ===
def extract_quarter_label(text):
    m = re.search(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text)
    if not m:
        return None
    month, day, year = int(m.group(1)), int(m.group(2)), m.group(3)
    if month == 3 and day == 31:
        return f"1st QTR, {year}"
    if month == 6:
        return f"2nd QTR, {year}"
    if month == 9 and day == 30:
        return f"3rd QTR, {year}"
    if month == 12 and day == 31:
        return f"4th QTR, {year}"
    return f"Unknown ({m.group(0)})"

# === Step 1 & 1.5: Page 1 Extraction ===
def process_page1(text):
    # Quarter
    q = extract_quarter_label(text or "")
    if q:
        st.session_state.quarter = q
        st.success(f"Quarter detected: {q}")
    else:
        st.error("Quarter not found on page 1.")

    # Total Options, Prepared For, Prepared By
    opts = re.search(r"Total Options:\s*(\d+)", text or "")
    st.session_state.total_options = int(opts.group(1)) if opts else None

    pf = re.search(r"Prepared For:\s*\n(.*)", text or "")
    st.session_state.prepared_for = pf.group(1).strip() if pf else None

    pb = re.search(r"Prepared By:\s*\n(.*)", text or "")
    st.session_state.prepared_by = pb.group(1).strip() if pb else None

    st.subheader("Page 1 Metadata")
    st.write(f"- Total Options: {st.session_state.total_options}")
    st.write(f"- Prepared For: {st.session_state.prepared_for}")
    st.write(f"- Prepared By: {st.session_state.prepared_by}")

# === Step 2: TOC Extraction ===
def process_toc(text):
    patterns = {
        "performance_page": r"Fund Performance: Current vs\. Proposed Comparison\s+(\d+)",
        "scorecard_page":   r"Fund Scorecard\s+(\d+)",
        "factsheets_page":  r"Fund Factsheets\s+(\d+)"
    }
    st.subheader("Table of Contents Pages")
    for key, pat in patterns.items():
        m = re.search(pat, text or "")
        num = int(m.group(1)) if m else None
        st.session_state[key] = num
        st.write(f"- {key.replace('_',' ').title()}: {num}")

# === Step 3 & 3.5–3.7: Scorecard Metrics & Numbers ===
def process_scorecard(pdf, start_page, declared_total):
    # collect pages
    pages = []
    for p in pdf.pages[start_page-1:]:
        txt = p.extract_text() or ""
        if "Fund Scorecard" in txt:
            pages.append(txt)
        else:
            break
    text = "\n".join(pages)
    lines = text.splitlines()

    # skip criteria box
    idx = next((i for i,l in enumerate(lines) if "Criteria Threshold" in l), None)
    if idx is not None:
        lines = lines[idx+1:]

    # parse blocks
    blocks = []
    current, metrics, capturing = None, [], False
    for i,l in enumerate(lines):
        if "Manager Tenure" in l:
            title = lines[i-1].strip()
            name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", title).strip()
            if current and metrics:
                blocks.append({"Fund Name": current, "Metrics": metrics})
            current, metrics, capturing = name, [], True
        elif capturing:
            if not l.strip() or "Fund Scorecard" in l:
                continue
            if len(metrics)>=14:
                capturing = False
                continue
            m = re.match(r"^(.*?)\s+(Pass|Review)\s+(.+)$", l.strip())
            if m:
                met, stat, info = m.groups()
                metrics.append({"Metric": met, "Status": stat, "Info": info})
    if current and metrics:
        blocks.append({"Fund Name": current, "Metrics": metrics})

    st.session_state.fund_blocks = blocks

    # show only Info lines
    st.subheader("Step 3.5: Metric Info")
    for b in blocks:
        st.markdown(f"**{b['Fund Name']}**")
        for m in b["Metrics"]:
            st.write(f"- {m['Info']}")

    # Step 3.6: count
    st.subheader("Step 3.6: Count Validation")
    cnt = len(blocks)
    st.write(f"- Declared: {declared_total}, Extracted: {cnt}")
    if cnt==declared_total:
        st.success("Counts match.")
    else:
        st.error("Count mismatch.")

    # Step 3.7: numbers
    st.subheader("Step 3.7: Numbers Extracted")
    for b in blocks:
        nums=[]
        for m in b["Metrics"]:
            nums+=re.findall(r"[-+]?\d*\.\d+|\d+", m["Info"])
        st.markdown(f"**{b['Fund Name']}**: " + (", ".join(nums) if nums else "No numbers"))

# === Main ===
def run():
    st.title("MPI Tool (Steps 1–3.7)")
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        return

    with pdfplumber.open(uploaded) as pdf:
        # Step 1 & 1.5
        page1 = pdf.pages[0].extract_text() or ""
        with st.expander("Page 1 Text"):
            st.text(page1)
        process_page1(page1)

        # Step 2
        if len(pdf.pages)>1:
            toc = pdf.pages[1].extract_text() or ""
            with st.expander("Page 2 (TOC)"):
                st.text(toc)
            process_toc(toc)
        else:
            st.warning("No TOC page.")

        # Step 3
        sp = st.session_state.get("scorecard_page")
        to = st.session_state.get("total_options")
        if sp and to is not None:
            process_scorecard(pdf, sp, to)
        else:
            st.warning("Run Steps 1–2 first.")

# To run in Streamlit:
# if __name__=="__main__":
#     run()
