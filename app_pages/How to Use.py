import streamlit as st

st.title("How to Use FidSync")

st.markdown("""
This guide walks you through using the **Fund Scorecard** tool.

---

### 📂 Step 1: Upload Files
Upload:
- A **fund report PDF** (usually 2–5 pages)
- An **Excel template** (your firm's scorecard file)

Make sure you're using the correct template — ask your manager if you're not sure.

---

### ⚙️ Step 2: Fill In the Form
Enter:
- The **sheet name** in the Excel file (usually "Scorecard")
- The column name where statuses go (like `"Status"`)
- The **first row** where fund data starts (like row `2`)
- The **page range** in the PDF (where fund info appears)
- The list of **fund names**, one per line (copy from Excel if needed)

> Not sure what to put in? Ask a teammate or submit a question in the **User Requests** tab.

---

### 🖱 Step 3: Generate Scorecard
Click **"Generate Scorecard"**. The app will:
- Extract the right data from the PDF
- Match it to the fund names in the Excel
- Fill in Pass/Fail with color-coding

If everything looks good, download your updated Excel file.

---

### 📝 Need Something Else?
Use the **User Requests** tab to submit feedback or request a new feature.
""")
