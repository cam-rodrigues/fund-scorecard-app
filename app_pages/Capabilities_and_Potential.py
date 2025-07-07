import streamlit as st

def run():
    st.markdown("## Capabilities & Potential")

    st.markdown("""
FidSync is a reliable internal tool designed to automate and simplify fund scorecard processing. In its current form, it already saves hours of manual effort, and its foundation is built for future expansion.

---

### What FidSync Can Do Now

- Extract fund names from complex PDF scorecards
- Match those names to investment options using fuzzy logic
- Update Excel templates accurately and automatically
- Log activity to Google Sheets for review and compliance
- Allow secure admin access to user feedback and requests
- Run as a web-based interface with a clear, easy-to-use design

---

### What FidSync Could Do Next

#### Integration Opportunities
- Email notifications for completed uploads
- CRM integration (e.g., Salesforce, HubSpot)
- Slack or Microsoft Teams connectivity
- Document signing integrations (e.g., DocuSign)

#### Smart Features
- Auto-suggest corrections for unmatched fund names
- Explain and summarize key PDF sections
- Highlight potential fund risks based on key indicators

#### Reporting and Analysis
- Add visual dashboards and charts
- Generate PDF or presentation-style reports
- Enable batch processing for high-volume use

#### Platform Scalability
- User authentication and account access control
- Audit logs and historical data tracking
- Secure file encryption and cleanup

---

### Summary

This project demonstrates what’s possible with Python in a real business environment:
- Automating repetitive financial tasks
- Working across multiple data types (PDF, Excel, Google Sheets)
- Building secure and scalable internal tools
- Creating a foundation for advanced features like AI, integrations, and reporting
    """)
