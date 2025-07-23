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
    st.title("Write Up Output")

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


def generate_watchlist_slide(df, selected_fund):
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import PP_ALIGN
    from pptx.dml.color import RGBColor

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])

    # === Title ===
    title_shape = slide.shapes.title
    title_shape.text = "Investment Watchlist"
    title_run = title_shape.text_frame.paragraphs[0].runs[0]
    title_run.font.size = Pt(20)
    title_run.font.name = "HelveticaNeueLT Std Lt Ext"
    title_run.font.color.rgb = RGBColor(0, 51, 102)

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
    table_left = Inches(0.3)
    table_height = Inches(0.25 * (rows + 1))
    table_width = Inches(9)

    table = slide.shapes.add_table(rows + 1, cols, table_left, table_top, table_width, table_height).table
    headers = ["Category", "Time Period", "Plan Assets"] + [str(i) for i in range(1, 12)] + ["IPS Status"]

    # Set column widths
    for i, width in enumerate(col_widths):
        table.columns[i].width = Inches(width)

    # Header row
    for col_idx, header in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = header
        cell.fill.background()
        p = cell.text_frame.paragraphs[0]
        p.font.name = "Cambria"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = RGBColor(0, 0, 0)
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
            cell.fill.background()
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(10)
            p.font.name = "Cambria"
            p.font.color.rgb = RGBColor(0, 0, 0)
            p.alignment = PP_ALIGN.CENTER

            if val == "Pass" and col_idx != 14:
                p.text = "✔"
                p.font.color.rgb = RGBColor(0, 176, 80)
            elif val == "Review" and col_idx != 14:
                p.text = "✖"
                p.font.color.rgb = RGBColor(255, 0, 0)
            elif col_idx == 14:
                p.text = ""  # Clear cell text
                val_str = str(val).strip().upper()

                # === Badge Logic ===
                if val_str.startswith("FW"):
                    badge_text = "FW"
                    badge_color = RGBColor(192, 0, 0)      # Red
                    font_color = RGBColor(255, 255, 255)
                elif val_str.startswith("IW"):
                    badge_text = "IW"
                    badge_color = RGBColor(255, 165, 0)    # Orange
                    font_color = RGBColor(255, 255, 255)
                elif val_str == "PASS":
                    badge_text = "✔"
                    badge_color = RGBColor(0, 176, 80)     # Green
                    font_color = RGBColor(255, 255, 255)
                else:
                    continue  # No badge for unknown status

                # === Calculate badge position manually ===
                badge_left = table_left + sum(Inches(w) for w in col_widths[:col_idx]) + Inches(0.15)
                badge_top = table_top + Inches(0.25 * row_idx)

                shape = slide.shapes.add_shape(
                    MSO_SHAPE.OVAL,
                    left=badge_left,
                    top=badge_top,
                    width=Inches(0.6),
                    height=Inches(0.3),
                )
                shape.fill.solid()
                shape.fill.fore_color.rgb = badge_color
                shape.line.color.rgb = RGBColor(255, 255, 255)

                tf = shape.text_frame
                tf.clear()
                para = tf.paragraphs[0]
                para.alignment = PP_ALIGN.CENTER
                run = para.add_run()
                run.text = badge_text
                run.font.bold = True
                run.font.size = Pt(12 if badge_text == "✔" else 10)
                run.font.color.rgb = font_color
            else:
                p.text = str(val)

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
