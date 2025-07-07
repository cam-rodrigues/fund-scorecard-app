import streamlit as st

def run():
    st.markdown("## Frequently Asked Questions")

    st.markdown("### Why can’t I paste investment options directly from Excel?")
    st.write("""
    Excel often includes hidden formatting like formulas, merged cells, or non-standard characters that don't paste cleanly.
    That's why FidSync asks for plain-text input — one investment option per line.
    """)

    st.markdown("### Is it safe to use FidSync with sensitive data?")
    st.write("""
    Yes. All processing happens locally and in-memory. No data is stored, transmitted, or saved. FidSync is safe for internal or client use.
    """)

    st.markdown("### What do 'Pass' and 'Review' mean in the Excel output?")
    st.write("""
    FidSync reads your PDF and writes 'Pass' or 'Review' based on the fund’s status. Green = Pass. Red = Review.
    You’ll see a live preview before downloading the Excel file.
    """)

    st.markdown("### Can I match funds if the names aren't exact?")
    st.write("""
    Yes — FidSync uses smart fuzzy matching. It's highly accurate, but always review the preview to confirm matches before downloading.
    """)
