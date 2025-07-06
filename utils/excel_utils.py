import openpyxl
from openpyxl.styles import PatternFill
import pandas as pd
from typing import Union


def update_excel_with_template(file_path: str, match_df: pd.DataFrame) -> None:
    """
    Updates an Excel workbook in-place with Pass/Fail results based on name matching.

    Args:
        file_path (str): Path to the Excel file.
        match_df (pd.DataFrame): DataFrame with "Extracted Fund Name" and "Investment Option".
    """
    try:
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active

        green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        red_fill = PatternFill(start_color="F2DCDB", end_color="F2DCDB", fill_type="solid")

        # Clear previous formatting in case of re-run
        for row in sheet.iter_rows():
            for cell in row:
                cell.fill = PatternFill()  # Reset to default

        # Map: Investment Option → Result
        results = []
        for _, row in match_df.iterrows():
            extracted = str(row["Extracted Fund Name"]).strip().lower()
            expected = str(row["Investment Option"]).strip().lower()
            passed = extracted == expected
            results.append("Pass" if passed else "Fail")

        # Write results into Excel (append to the right)
        start_row = 2  # Skip header
        result_col = sheet.max_column + 1
        sheet.cell(row=1, column=result_col, value="Status")

        for i, result in enumerate(results):
            cell = sheet.cell(row=start_row + i, column=result_col, value=result)
            cell.fill = green_fill if result == "Pass" else red_fill

        wb.save(file_path)

    except Exception as e:
        raise RuntimeError(f"Excel update failed: {e}")
