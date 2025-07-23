import streamlit as st
import pandas as pd
import app_pages.write_up_processor as write_up_processor  # Make sure this module has process_mpi(uploaded_file)
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from io import BytesIO  # ✅ Add this
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
    


def run():
    st.set_page_config(page_title="IPS Summary Table", layout="wide")
    st.title("Upload MPI & View IPS Summary Table")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="writeup_upload")

    if not uploaded_file:
        st.warning("Please upload an MPI PDF to continue.")
        return

    if "fund_blocks" not in st.session_state:
        st.session_state["suppress_criteria_display"] = True
        st.session_state["suppress_scorecard_table"] = True
        st.session_state["suppress_matching_confirmation"] = True  # 👈 NEW FLAG
        write_up_processor.process_mpi(uploaded_file)
        st.success("File processed.")
    

    # Load data
    ips_results = st.session_state.get("step8_results", [])
    factsheet_data = st.session_state.get("fund_factsheets_data", [])
    quarter = st.session_state.get("report_quarter", "Unknown")

    if not ips_results or not factsheet_data:
        st.error("Missing processed data.")
        return

    # === Section 1: Full Table with All Funds ===
    rows = []
    for result in ips_results:
        fund_name = result["Fund Name"]
        ips_status = result["Overall IPS Status"]
        metric_results = [m["Status"] if m["Status"] in ("Pass", "Review") else "N/A" for m in result["IPS Metrics"]]
        metric_results = metric_results[:11] + ["N/A"] * (11 - len(metric_results))

        fund_fact = next((f for f in factsheet_data if f["Matched Fund Name"] == fund_name), {})
        category = fund_fact.get("Category", "N/A")
        ticker = fund_fact.get("Matched Ticker", "N/A")

        row = {
            "Fund Name": fund_name,
            "Ticker": ticker,
            "Category": category,
            "Time Period": quarter,
            "Plan Assets": "$"
        }
        for i in range(11):
            row[str(i + 1)] = metric_results[i]
        row["IPS Status"] = ips_status

        rows.append(row)

    df_summary = pd.DataFrame(rows)
    st.subheader("IPS Summary Table (All Funds)")
    st.dataframe(df_summary, use_container_width=True)

    # === Section 2: View One Fund in Detail ===
    st.subheader("View Individual Fund Summary")
    fund_names = [res["Fund Name"] for res in ips_results]
    selected_fund = st.selectbox("Select a Fund", fund_names)

    selected_result = next((r for r in ips_results if r["Fund Name"] == selected_fund), None)
    selected_facts = next((f for f in factsheet_data if f["Matched Fund Name"] == selected_fund), {})

    if not selected_result:
        st.error("Selected fund not found.")
        return

    category = selected_facts.get("Category", "N/A")
    ticker = selected_facts.get("Matched Ticker", "N/A")
    ips_status = selected_result["Overall IPS Status"]
    metric_results = [m["Status"] if m["Status"] in ("Pass", "Review") else "N/A" for m in selected_result["IPS Metrics"]]
    metric_results = metric_results[:11] + ["N/A"] * (11 - len(metric_results))

    row = {
        "Fund Name": selected_fund,
        "Ticker": ticker,
        "Category": category,
        "Time Period": quarter,
        "Plan Assets": "$"
    }
    for i in range(11):
        row[str(i + 1)] = metric_results[i]
    row["IPS Status"] = ips_status

    df_one = pd.DataFrame([row])
    st.dataframe(df_one, use_container_width=True)

    # === Section 3: Additional Factsheet Info ===
    st.subheader("Fund Factsheet Information")
    if selected_facts:
        st.markdown(f"""
        - **Ticker:** {selected_facts.get('Matched Ticker', 'N/A')}
        - **Benchmark:** {selected_facts.get('Benchmark', 'N/A')}
        - **Category:** {selected_facts.get('Category', 'N/A')}
        - **Net Assets:** {selected_facts.get('Net Assets', 'N/A')}
        - **Manager Name:** {selected_facts.get('Manager Name', 'N/A')}
        - **Avg. Market Cap:** {selected_facts.get('Avg. Market Cap', 'N/A')}
        - **Expense Ratio:** {selected_facts.get('Expense Ratio', 'N/A')}
        """)
    else:
        st.warning("No factsheet data found for the selected fund.")

        # === Section 4: Powerpoint ===

def run():
    st.set_page_config(page_title="IPS Summary Table", layout="wide")
    st.title("Upload MPI & View IPS Summary Table")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="writeup_upload")

    if not uploaded_file:
        st.warning("Please upload an MPI PDF to continue.")
        return

    if "fund_blocks" not in st.session_state:
        st.session_state["suppress_criteria_display"] = True
        st.session_state["suppress_scorecard_table"] = True
        st.session_state["suppress_matching_confirmation"] = True  # 👈 NEW FLAG
        write_up_processor.process_mpi(uploaded_file)
        st.success("File processed.")

    # Load data
    ips_results = st.session_state.get("step8_results", [])
    factsheet_data = st.session_state.get("fund_factsheets_data", [])
    quarter = st.session_state.get("report_quarter", "Unknown")

    if not ips_results or not factsheet_data:
        st.error("Missing processed data.")
        return

    # === Section 1: Full Table with All Funds ===
    rows = []
    for result in ips_results:
        fund_name = result["Fund Name"]
        ips_status = result["Overall IPS Status"]
        metric_results = [m["Status"] if m["Status"] in ("Pass", "Review") else "N/A" for m in result["IPS Metrics"]]
        metric_results = metric_results[:11] + ["N/A"] * (11 - len(metric_results))

        fund_fact = next((f for f in factsheet_data if f["Matched Fund Name"] == fund_name), {})
        category = fund_fact.get("Category", "N/A")
        ticker = fund_fact.get("Matched Ticker", "N/A")

        row = {
            "Fund Name": fund_name,
            "Ticker": ticker,
            "Category": category,
            "Time Period": quarter,
            "Plan Assets": "$"
        }
        for i in range(11):
            row[str(i + 1)] = metric_results[i]
        row["IPS Status"] = ips_status

        rows.append(row)

    df_summary = pd.DataFrame(rows)
    st.subheader("IPS Summary Table (All Funds)")
    st.dataframe(df_summary, use_container_width=True)

    # === Section 2: View One Fund in Detail ===
    st.subheader("View Individual Fund Summary")
    fund_names = [res["Fund Name"] for res in ips_results]
    selected_fund = st.selectbox("Select a Fund", fund_names)

    selected_result = next((r for r in ips_results if r["Fund Name"] == selected_fund), None)
    selected_facts = next((f for f in factsheet_data if f["Matched Fund Name"] == selected_fund), {})

    if not selected_result:
        st.error("Selected fund not found.")
        return

    category = selected_facts.get("Category", "N/A")
    ticker = selected_facts.get("Matched Ticker", "N/A")
    ips_status = selected_result["Overall IPS Status"]
    metric_results = [m["Status"] if m["Status"] in ("Pass", "Review") else "N/A" for m in selected_result["IPS Metrics"]]
    metric_results = metric_results[:11] + ["N/A"] * (11 - len(metric_results))

    row = {
        "Fund Name": selected_fund,
        "Ticker": ticker,
        "Category": category,
        "Time Period": quarter,
        "Plan Assets": "$"
    }
    for i in range(11):
        row[str(i + 1)] = metric_results[i]
    row["IPS Status"] = ips_status

    df_one = pd.DataFrame([row])
    st.dataframe(df_one, use_container_width=True)

    # === Section 3: Additional Factsheet Info ===
    st.subheader("Fund Factsheet Information")
    if selected_facts:
        st.markdown(f"""
        - **Ticker:** {selected_facts.get('Matched Ticker', 'N/A')}
        - **Benchmark:** {selected_facts.get('Benchmark', 'N/A')}
        - **Category:** {selected_facts.get('Category', 'N/A')}
        - **Net Assets:** {selected_facts.get('Net Assets', 'N/A')}
        - **Manager Name:** {selected_facts.get('Manager Name', 'N/A')}
        - **Avg. Market Cap:** {selected_facts.get('Avg. Market Cap', 'N/A')}
        - **Expense Ratio:** {selected_facts.get('Expense Ratio', 'N/A')}
        """)
    else:
        st.warning("No factsheet data found for the selected fund.")


# === PowerPoint Generator: Dataset-style ===
def generate_watchlist_slide(df, selected_fund):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])

    # Title
    title_shape = slide.shapes.title
    title_shape.text = "Investment Watchlist"
    title_run = title_shape.text_frame.paragraphs[0].runs[0]
    title_run.font.size = Pt(20)
    title_run.font.name = "HelveticaNeueLT Std Lt Ext"
    title_run.font.color.rgb = RGBColor(0, 51, 102)

    # Subheading
    top = Inches(1.0)
    subheading = slide.shapes.add_textbox(Inches(0.5), top, Inches(9), Inches(0.3))
    tf = subheading.text_frame
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = selected_fund
    run.font.name = "Cambria"
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.underline = True
    run.font.color.rgb = RGBColor(0, 0, 0)

    # Data
    matching_rows = df[df["Fund Name"] == selected_fund]
    if matching_rows.empty:
        return prs

    r = matching_rows.iloc[0]
    category = r["Category"]
    time_period = r["Time Period"]
    plan_assets = r["Plan Assets"]
    ips_status = r["IPS Status"]
    metrics = [r[str(i)] for i in range(1, 12)]

    # Format as monospace text
    header = ["Category", "Time Period", "Plan Assets"] + [str(i) for i in range(1, 12)] + ["IPS Status"]
    header_str = "{:<12} {:<12} {:<12}".format(*header[:3]) + "  " + "  ".join([f"{h:>2}" for h in header[3:-1]]) + "   " + header[-1]
    metric_str = "{:<12} {:<12} {:<12}".format(category, time_period, plan_assets)

    for m in metrics:
        if m == "Pass":
            metric_str += "   ✔"
        elif m == "Review":
            metric_str += "   ✖"
        else:
            metric_str += "   -"
    metric_str += "   "  # space for IPS badge

    textbox = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(9), Inches(2))
    tf = textbox.text_frame
    tf.word_wrap = True
    tf.clear()

    for line in [header_str, metric_str]:
        para = tf.add_paragraph()
        para.text = line
        para.font.name = "Courier New"
        para.font.size = Pt(11)
        para.space_after = Pt(5)

    # Badge for IPS Status
    badge = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        left=Inches(8.1),
        top=Inches(1.75),
        width=Inches(0.6),
        height=Inches(0.3),
    )
    badge.fill.solid()
    badge.fill.fore_color.rgb = RGBColor(192, 0, 0)
    badge.line.color.rgb = RGBColor(255, 255, 255)
    badge_tf = badge.text_frame
    badge_tf.clear()
    badge_para = badge_tf.paragraphs[0]
    badge_para.alignment = PP_ALIGN.CENTER
    badge_run = badge_para.add_run()
    badge_run.text = ips_status
    badge_run.font.size = Pt(10)
    badge_run.font.bold = True
    badge_run.font.color.rgb = RGBColor(255, 255, 255)

    return prs

# === Streamlit App ===
def run():
    st.set_page_config(page_title="IPS Summary Table", layout="wide")
    st.title("Upload MPI & View IPS Summary Table")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="writeup_upload")
    if not uploaded_file:
        st.warning("Please upload an MPI PDF to continue.")
        return

    if "fund_blocks" not in st.session_state:
        st.session_state["suppress_criteria_display"] = True
        st.session_state["suppress_scorecard_table"] = True
        st.session_state["suppress_matching_confirmation"] = True
        write_up_processor.process_mpi(uploaded_file)
        st.success("File processed.")

    ips_results = st.session_state.get("step8_results", [])
    factsheet_data = st.session_state.get("fund_factsheets_data", [])
    quarter = st.session_state.get("report_quarter", "Unknown")

    if not ips_results or not factsheet_data:
        st.error("Missing processed data.")
        return

    rows = []
    for result in ips_results:
        fund_name = result["Fund Name"]
        ips_status = result["Overall IPS Status"]
        metric_results = [m["Status"] if m["Status"] in ("Pass", "Review") else "N/A" for m in result["IPS Metrics"]]
        metric_results = metric_results[:11] + ["N/A"] * (11 - len(metric_results))

        fund_fact = next((f for f in factsheet_data if f["Matched Fund Name"] == fund_name), {})
        category = fund_fact.get("Category", "N/A")
        ticker = fund_fact.get("Matched Ticker", "N/A")

        row = {
            "Fund Name": fund_name,
            "Ticker": ticker,
            "Category": category,
            "Time Period": quarter,
            "Plan Assets": "$"
        }
        for i in range(11):
            row[str(i + 1)] = metric_results[i]
        row["IPS Status"] = ips_status
        rows.append(row)

    df_summary = pd.DataFrame(rows)
    st.subheader("IPS Summary Table (All Funds)")
    st.dataframe(df_summary, use_container_width=True)

    st.subheader("View Individual Fund Summary")
    fund_names = [res["Fund Name"] for res in ips_results]
    selected_fund = st.selectbox("Select a Fund", fund_names)

    selected_result = next((r for r in ips_results if r["Fund Name"] == selected_fund), None)
    selected_facts = next((f for f in factsheet_data if f["Matched Fund Name"] == selected_fund), {})

    if not selected_result:
        st.error("Selected fund not found.")
        return

    category = selected_facts.get("Category", "N/A")
    ticker = selected_facts.get("Matched Ticker", "N/A")
    ips_status = selected_result["Overall IPS Status"]
    metric_results = [m["Status"] if m["Status"] in ("Pass", "Review") else "N/A" for m in selected_result["IPS Metrics"]]
    metric_results = metric_results[:11] + ["N/A"] * (11 - len(metric_results))

    row = {
        "Fund Name": selected_fund,
        "Ticker": ticker,
        "Category": category,
        "Time Period": quarter,
        "Plan Assets": "$"
    }
    for i in range(11):
        row[str(i + 1)] = metric_results[i]
    row["IPS Status"] = ips_status

    df_one = pd.DataFrame([row])
    st.dataframe(df_one, use_container_width=True)

    st.subheader("Fund Factsheet Information")
    if selected_facts:
        st.markdown(f"""
        - **Ticker:** {selected_facts.get('Matched Ticker', 'N/A')}
        - **Benchmark:** {selected_facts.get('Benchmark', 'N/A')}
        - **Category:** {selected_facts.get('Category', 'N/A')}
        - **Net Assets:** {selected_facts.get('Net Assets', 'N/A')}
        - **Manager Name:** {selected_facts.get('Manager Name', 'N/A')}
        - **Avg. Market Cap:** {selected_facts.get('Avg. Market Cap', 'N/A')}
        - **Expense Ratio:** {selected_facts.get('Expense Ratio', 'N/A')}
        """)
    else:
        st.warning("No factsheet data found for the selected fund.")

    # === Export PowerPoint ===
    if "summary_df" not in st.session_state:
        st.session_state["summary_df"] = df_summary

    st.markdown("---")
    st.subheader("Export Selected Fund to PowerPoint")

    if st.button("Export to PowerPoint"):
        if selected_fund and not st.session_state["summary_df"].empty:
            ppt = generate_watchlist_slide(st.session_state["summary_df"], selected_fund)
            output = BytesIO()
            ppt.save(output)

            st.download_button(
                label="Download PowerPoint File",
                data=output.getvalue(),
                file_name=f"{selected_fund}_Watchlist.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        else:
            st.warning("Please select a fund and ensure data is loaded.")
