# FidSync

FidSync is a professional-grade tool that helps financial teams extract fund names from PDF scorecards, align them with investment options, and update Excel templates — cleanly and accurately, with no manual Excel hacks.

---

## 🚀 What It Does

- Extracts fund names from messy PDF scorecards
- Lets you align those with your actual investment options
- Updates your Excel templates for compliance or reporting
- Provides a "Fund Scorecard" matching interface
- Collects feedback through a secure form
- Admin view to review all submissions

---

## 🛠 How to Use

1. Launch the app (`streamlit run app.py`)
2. Use the sidebar to:
   - View **Getting Started** and **Security Policy**
   - Run the **Fund Scorecard** tool
   - Submit a **User Request** or **Feature Idea**
3. If you're an admin, you can access a hidden tab to view all submissions

---

## 📁 Folder Structure

```bash
fydsync/
├── app.py                       # Main Streamlit app
├── app_pages/                  # Modular Streamlit page files
│   ├── fund_scorecard.py
│   ├── user_requests.py
│   ├── admin_view_requests.py
│   └── ...
├── requests/                   # Saved user submissions (.txt, attachments)
│   └── .gitkeep
├── .streamlit/
│   └── config.toml             # Theme & credentials (optional)
├── README.md
└── requirements.txt
