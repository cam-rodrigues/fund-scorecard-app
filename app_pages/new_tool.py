import streamlit as st

st.set_page_config(page_title="SEC EDGAR Lookup", layout="centered")
st.title("🏦 SEC EDGAR Lookup")

st.markdown("""
Use this tool to quickly access SEC filings for any public company.

Enter a **ticker** or **CIK** to generate direct EDGAR links:
- Full Filings Page
- Latest 10-K / 10-Q / 8-K (manual links, not API-powered)
""")

query = st.text_input("Enter Ticker or CIK:", max_chars=10)

if query:
    query = query.strip().upper()
    cik_or_ticker = query.replace(" ", "")
    base_url = f"https://www.sec.gov/edgar/browse/?CIK={cik_or_ticker}&owner=exclude"
    filings_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_or_ticker}&type=&dateb=&owner=exclude&count=40"

    st.markdown("---")
    st.subheader(f"🔗 Quick EDGAR Links for {cik_or_ticker}")
    st.markdown(f"- [Company Filings Page]({filings_url})")
    st.markdown(f"- [Latest 10-K]({filings_url}&type=10-K)")
    st.markdown(f"- [Latest 10-Q]({filings_url}&type=10-Q)")
    st.markdown(f"- [Latest 8-K]({filings_url}&type=8-K)")
    st.markdown(f"- [SEC Summary Page]({base_url})")

    st.info("Filings open in a new tab. EDGAR search supports both tickers and full CIK numbers.")


def run():
    import streamlit as st

    st.set_page_config(page_title="SEC EDGAR Lookup", layout="centered")
    st.title("🏦 SEC EDGAR Lookup")

    st.markdown("""
    Use this tool to quickly access SEC filings for any public company.

    Enter a **ticker** or **CIK** to generate direct EDGAR links:
    - Full Filings Page
    - Latest 10-K / 10-Q / 8-K (manual links, not API-powered)
    """)

    query = st.text_input("Enter Ticker or CIK:", max_chars=10)

    if query:
        query = query.strip().upper()
        cik_or_ticker = query.replace(" ", "")
        base_url = f"https://www.sec.gov/edgar/browse/?CIK={cik_or_ticker}&owner=exclude"
        filings_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_or_ticker}&type=&dateb=&owner=exclude&count=40"

        st.markdown("---")
        st.subheader(f"🔗 Quick EDGAR Links for {cik_or_ticker}")
        st.markdown(f"- [Company Filings Page]({filings_url})")
        st.markdown(f"- [Latest 10-K]({filings_url}&type=10-K)")
        st.markdown(f"- [Latest 10-Q]({filings_url}&type=10-Q)")
        st.markdown(f"- [Latest 8-K]({filings_url}&type=8-K)")
        st.markdown(f"- [SEC Summary Page]({base_url})")

        st.info("Filings open in a new tab. EDGAR search supports both tickers and full CIK numbers.")

