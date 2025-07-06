from openpyxl import load_workbook
from openpyxl.styles import PatternFill
import io

def update_excel_with_template(excel_bytes, sheet_name, match_df):
    try:
        wb = load_workbook(excel_bytes)
        if sheet_name not in wb.sheetnames:
            raise ValueError(f"Sheet '{sheet_name}' not found in the workbook.")

        ws = wb[sheet_name]

        # Create fill styles
        green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        red_fill = PatternFill(start_color="F2DCDB", end_color="F2DCDB", fill_type="solid")

        # Write matched values to sheet starting at row 2
        for i, row in enumerate(match_df.itertuples(index=False), start=2):
            fund_name = row._1
            matched_name = row._2
            score = row._3
            status = row._4

            # Columns: A = raw, B = matched, C = score, D = status
            ws.cell(row=i, column=1, value=fund_name)
            ws.cell(row=i, column=2, value=matched_name)
            ws.cell(row=i, column=3, value=score)

            status_cell = ws.cell(row=i, column=4)
            status_cell.value = status
            status_cell.fill = green_fill if status == "Pass" else red_fill

        # Save to memory
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    except Exception as e:
        raise RuntimeError(f"Excel update failed: {e}")
