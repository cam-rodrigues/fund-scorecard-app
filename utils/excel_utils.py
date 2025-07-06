import pandas as pd
import io
import openpyxl
from difflib import get_close_matches
import pdfplumber

def update_excel_with_template(
    pdf_bytes,
    excel_bytes,
    sheet_name,
    status_col,
    start_row,
    fund_names,
    start_page,
    end_page,
    dry_run=False
):
    # Extract PDF text
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = ""
        for page in pdf.pages[start_page - 1:end_page]:
            text += page.extract_text() + "\n"

    # Match fund names and assign Pass/Fail
    matches = {}
    for name in fund_names:
        match = get_close_matches(name, text.splitlines(), n=1, cutoff=0.5)
        matches[name] = "Pass" if match else "Fail"

    # Load Excel
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    ws = wb[sheet_name]

    # Build a DataFrame from Excel to find column indexes
    df = pd.DataFrame(ws.values)
    headers = df.iloc[start_row - 2].tolist()

    if status_col not in headers:
        raise ValueError(f"Column '{status_col}' not found in Excel.")

    status_col_idx = headers.index(status_col) + 1

    updated_rows = []

    for i, row in enumerate(ws.iter_rows(min_row=start_row), start=start_row):
        fund_cell = row[0]  # assuming fund name is in column A
        fund = str(fund_cell.value).strip()
        if not fund:
            continue

        result = matches.get(fund, "Fail")
        if not dry_run:
            cell = ws.cell(row=i, column=status_col_idx)
            cell.value = result
            fill_color = "C6EFCE" if result == "Pass" else "FFC7CE"
            font_color = "006100" if result == "Pass" else "9C0006"
            cell.fill = openpyxl.styles.PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            cell.font = openpyxl.styles.Font(color=font_color)

        updated_rows.append({"Fund": fund, "Status": result})

    if dry_run:
        return pd.DataFrame(updated_rows)

    # Save to memory
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return output
