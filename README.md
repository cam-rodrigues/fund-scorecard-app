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


---

## 📄 Submission Log

All user request submissions are viewable here (admin only):  
👉 [FidSync Submissions Sheet](https://docs.google.com/spreadsheets/d/1NByeYVPB0oX8i2ct9cEt3cQat7Dyp-uZxBbw17QiQeY)

> _Only shared with the developer or authorized team members._
---

## 🔒 Data & Privacy

- No submission data is stored or shared outside the app unless authorized.
- All uploads go to a local `/requests/` folder by default.
- The public GitHub repo only tracks `.gitkeep` (no user submissions).
- You control whether to connect Google Sheets or email for backups.

---

## 📬 Support

For issues or questions, submit a request in-app or reach out directly.  
Want to contribute or build your own version? Fork this repo and start customizing.

---

## 📌 Coming Soon

- Google Sheets live integration
- Admin filtering & search
- Export to CSV
- Submission email alerts

---

_© 2025 Cam Rodrigues — Built with ❤️ using Streamlit_
