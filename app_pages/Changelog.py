import streamlit as st

def run():
    st.markdown("## Changelog")

    st.markdown("### v1.2.0 – July 2025")
    st.markdown("""
    - Modern UI and color scheme
    - Dropdown-based sidebar navigation
    - User Manual and FAQ added
    - Streamlit API upgraded to support `st.query_params`
    """)

    st.markdown("### v1.1.0 – June 2025")
    st.markdown("""
    - User Request form launched
    - PDF and Excel preview upgraded
    - Internal fuzzy matching engine improved
    """)

    st.markdown("### v1.0.0 – May 2025")
    st.markdown("""
    - Initial release
    - Fund Scorecard processing with Excel export
    - Manual investment option input
    """)
