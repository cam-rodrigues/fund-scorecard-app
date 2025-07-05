# 📊 Fund Scorecard Status Tool

A secure, company-branded web app that updates Excel files with fund status results from a PDF fund scorecard.

---

## 🔐 Security Features

- **Password-protected login**
  - Configured via `.streamlit/secrets.toml`
- **Confidential-safe**: Files are processed 100% in-memory — nothing is stored or uploaded
- **Local-only** unless deployed
- Built using Python + Streamlit

---

## 🎨 Company Branding

- Custom color scheme using `.streamlit/config.toml`
- Polished, professional UI with modern typography
- Wider layout and large hero heading
- Ready for enterprise deployment

---

## 🧰 What It Does

- Upload a **PDF fund scorecard**
- Upload an **Excel workbook**
- Paste in a list of investment option names
- App will:
  - Scan the PDF for fund status phrases
  - Match fund names with high-accuracy fuzzy matching
  - Write “Pass” or “Fail” into the Excel sheet
  - Color-code the cells (green/red)
  - Skip formula cells automatically
  - Collect feature requests via a dedicated tab

---

## 📦 Files & Folders

```
fund-scorecard-app/
├── app.py                  ← Main app script
├── requirements.txt        ← List of needed Python packages
├── README.md               ← You're reading this!
├── app_pages/
│   ├── fund_scorecard.py   ← Fund scorecard workflow
│   └── user_requests.py    ← Request submission tab
├── .streamlit/
│   ├── config.toml         ← Custom color theme
│   └── secrets.toml        ← Access password
```

---

## 🛠 How to Run the App (Locally)

1. **Activate your conda environment**:

```bash
conda activate fund_status_env
```

2. **Navigate to the project folder**:

```bash
cd path/to/fund-scorecard-app
```

3. **Run the app**:

```bash
streamlit run app.py
```

4. **Enter your password** when prompted  
   *(Password is stored in `.streamlit/secrets.toml`)*

---

## 📥 Output

- ✅ **Updated Excel file** (with statuses + formatting)
- ✅ **Match Log CSV** showing:
  - Input name
  - Matched name
  - Confidence score
  - Final status

---

## 💡 Tips

- Page numbers are **0-based** (Page 1 = 0)
- Use clean fund names, one per line
- Recommended match score threshold is 70+
- Make sure the sheet name in Excel is spelled exactly

---

## 📌 Author

Built by [Your Name Here] for secure internal use  
Built with Python, Streamlit, pdfplumber, openpyxl, pandas, and rapidfuzz

---

## 🛡️ License

Internal use only – contains proprietary logic and confidential data.
