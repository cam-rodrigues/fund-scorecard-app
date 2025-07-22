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


    def generate_watchlist_slide_template_style(df, selected_fund):
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[5])
    
        # === Title (Centered) ===
        title = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(0.5))
        tf = title.text_frame
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = "Investment Watchlist"
        run.font.size = Pt(20)
        run.font.name = "HelveticaNeueLT Std Lt Ext"
        run.font.color.rgb = RGBColor(0, 51, 102)
    
        # === Subheading (Fund Name, bold + underline) ===
        subtitle = slide.shapes.add_textbox(Inches(0.5), Inches(0.7), Inches(9), Inches(0.3))
        tf = subtitle.text_frame
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = selected_fund
        run.font.name = "Cambria"
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.underline = True
        run.font.color.rgb = RGBColor(0, 0, 0)
    
        # === Filter data ===
        matching_rows = df[df["Fund Name"] == selected_fund]
        rows = len(matching_rows)
        cols = 15
        table = slide.shapes.add_table(
            rows + 1, cols, Inches(0.3), Inches(1.1), Inches(9), Inches(0.8 + 0.3 * rows)
        ).table
    
        headers = ["Category", "Time Period", "Plan Assets"] + [str(i) for i in range(1, 12)] + ["IPS Status"]
    
        # === Header Row Styling ===
        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = header
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(47, 84, 150)  # Dark blue
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(10)
            p.font.bold = True
            p.font.color.rgb = RGBColor(255, 255, 255)
            p.alignment = PP_ALIGN.CENTER
            cell.text_frame.vertical_anchor = PP_ALIGN.CENTER
    
        # === Data Rows Styling ===
        for row_idx, (_, r) in enumerate(matching_rows.iterrows(), start=1):
            values = [
                r.get("Category", ""),
                r.get("Time Period", ""),
                r.get("Plan Assets", "$")
            ] + [r.get(str(i), "") for i in range(1, 12)] + [r.get("IPS Status", "")]
    
            for col_idx, val in enumerate(values):
                cell = table.cell(row_idx, col_idx)
                cell.fill.background()  # Clear fill (transparent like template)
                p = cell.text_frame.paragraphs[0]
                p.font.size = Pt(10)
                p.alignment = PP_ALIGN.CENTER
                cell.text_frame.vertical_anchor = PP_ALIGN.CENTER
    
                if val == "Pass":
                    p.text = "✔"
                    p.font.color.rgb = RGBColor(0, 176, 80)  # Green
                elif val == "Review":
                    p.text = "✖"
                    p.font.color.rgb = RGBColor(255, 0, 0)  # Red
                else:
                    p.text = str(val)
    
        return prs
    
    ppt = generate_watchlist_slide_template_style(st.session_state["summary_df"], selected_fund)
    output = BytesIO()
    ppt.save(output)
    
    st.download_button(
        label="Download PowerPoint File",
        data=output.getvalue(),
        file_name=f"{selected_fund}_Watchlist.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
