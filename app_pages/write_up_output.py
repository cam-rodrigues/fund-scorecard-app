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

        


    def generate_watchlist_slide(df, selected_fund):
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[5])
    
        # === Title ===
        title_shape = slide.shapes.title
        title_shape.text = "Investment Watchlist"
        title_run = title_shape.text_frame.paragraphs[0].runs[0]
        title_run.font.size = Pt(20)
        title_run.font.name = "HelveticaNeueLT Std Lt Ext"
        title_run.font.color.rgb = RGBColor(0, 51, 102)  # Dark blue
    
        # === Subheading ===
        top = Inches(1.1)
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
    
        # === Table Data ===
        matching_rows = df[df["Fund Name"] == selected_fund]
        rows = len(matching_rows)
        cols = 15
        col_widths = [1.8, 1.2, 1.0] + [0.4]*11 + [0.9]
    
        table_top = Inches(1.5)
        table = slide.shapes.add_table(rows + 1, cols, Inches(0.3), table_top, Inches(9), Inches(0.8 + 0.25 * rows)).table
    
        headers = ["Category", "Time Period", "Plan Assets"] + [str(i) for i in range(1, 12)] + ["IPS Status"]
    
        # Set widths
        for i, width in enumerate(col_widths):
            table.columns[i].width = Inches(width)
    
        # Header
        for col_idx, header in enumerate(headers):
            cell = table.cell(0, col_idx)
            cell.text = header
            p = cell.text_frame.paragraphs[0]
            p.font.bold = True
            p.font.size = Pt(10)
            p.alignment = PP_ALIGN.CENTER
    
        # Data rows
        for row_idx, (_, r) in enumerate(matching_rows.iterrows(), start=1):
            row_vals = [
                r.get("Category", ""),
                r.get("Time Period", ""),
                r.get("Plan Assets", ""),
            ] + [r.get(str(i), "") for i in range(1, 12)] + [r.get("IPS Status", "")]
    
            for col_idx, val in enumerate(row_vals):
                cell = table.cell(row_idx, col_idx)
                p = cell.text_frame.paragraphs[0]
                p.font.size = Pt(10)
                p.alignment = PP_ALIGN.CENTER
    
                if val == "Pass":
                    p.text = "✔"
                    p.font.color.rgb = RGBColor(0, 176, 80)
                elif val == "Review":
                    p.text = "✖"
                    p.font.color.rgb = RGBColor(255, 0, 0)
                elif col_idx == 14 and val.startswith("FW"):
                    # IPS Status Badge
                    shape = slide.shapes.add_shape(
                        autoshape_type_id=1,  # MSO_SHAPE.OVAL
                        left=table.columns[col_idx].left + Inches(0.35),
                        top=table_top + Inches(0.25 * row_idx),
                        width=Inches(0.6),
                        height=Inches(0.3),
                    )
                    shape.fill.solid()
                    shape.fill.fore_color.rgb = RGBColor(192, 0, 0)
                    shape.text = val
                    tf = shape.text_frame
                    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
                    run = tf.paragraphs[0].runs[0]
                    run.font.size = Pt(10)
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
                else:
                    p.text = str(val)
    
        # === Optional: Footnotes / Commentary (placeholder) ===
        note_top = table_top + Inches(0.25 * (rows + 1)) + Inches(0.2)
        note_box = slide.shapes.add_textbox(Inches(0.5), note_top, Inches(8.5), Inches(1))
        note_frame = note_box.text_frame
        bullet1 = note_frame.add_paragraph()
        bullet1.text = f"{selected_fund} underperformed its benchmark due to stock selection."
        bullet1.level = 0
        bullet1.font.size = Pt(10)
    
        bullet2 = note_frame.add_paragraph()
        bullet2.text = "The fund’s results were impacted by market volatility and sector exposure."
        bullet2.level = 0
        bullet2.font.size = Pt(10)
    
        return prs
        
    # === Store the processed table so we can export it ===
    if "summary_df" not in st.session_state:
        st.session_state["summary_df"] = df  # df is the final table showing all funds
    
    # === Export PowerPoint for Selected Fund ===
    st.markdown("---")
    st.subheader("📤 Export Selected Fund to PowerPoint")
    
    if st.button("Export to PowerPoint"):
        selected_fund = st.session_state.get("selected_fund") or fund_dropdown
        
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
