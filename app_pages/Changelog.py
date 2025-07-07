import streamlit as st

def run():
    st.title("Changelog & Feature Plans")

    st.markdown("Below are the latest updates to FidSync, along with upcoming planned improvements.")

    with st.container():
        st.subheader("Version 1.2.0 – July 2025")
        st.markdown("""
        - Professional sidebar with styled navigation  
        - Unified documentation layout and styling  
        - Live fund match preview and improved error handling  
        """)

    with st.container():
        st.subheader("Version 1.1.0 – June 2025")
        st.markdown("""
        - User request form with email validation  
        - Fuzzy matching logic upgraded  
        - Color-coded Excel output with formula skip detection  
        """)

    with st.container():
        st.subheader("Version 1.0.0 – May 2025")
        st.markdown("""
        - Initial launch with PDF + Excel processing  
        - Manual investment option input  
        - Basic match results written to Excel  
        """)

    with st.container():
        st.subheader("Planned Features")
        st.markdown("""
        - Match confidence scores and review step  
        - Multi-sheet Excel support with custom targeting  
        - CSV export of preview table  
        - Theme toggle (light/dark mode)  
        - Admin dashboard for user feedback  
        """)
