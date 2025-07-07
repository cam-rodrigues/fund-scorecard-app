import streamlit as st

def run():
    st.markdown("## Changelog & Feature Plans")

    st.markdown("### Recent Updates")

    st.markdown("#### Version 1.2.0 – July 2025")
    st.write("""
    - Updated UI with professional color scheme and sidebar layout
    - Integrated user manual and documentation cleanup
    - Added dropdown navigation using query parameters
    - Improved fund scorecard preview and error handling
    """)

    st.markdown("#### Version 1.1.0 – June 2025")
    st.write("""
    - Introduced User Request form with optional email
    - Enhanced fuzzy matching engine
    - Added Excel formatting (green/red) and formula detection
    """)

    st.markdown("#### Version 1.0.0 – May 2025")
    st.write("""
    - Initial release
    - Upload fund scorecard (PDF) and Excel workbook
    - Match statuses and export updated Excel
    """)

    st.markdown("---")

    st.markdown("### Planned Features")

    st.write("""
    These items are under consideration or in development:
    - Optional match confidence scoring and review step
    - Advanced Excel features (multi-sheet targeting, dynamic cell ranges)
    - Theme customization (light/dark mode toggle)
    - Export preview data as CSV
    - Admin dashboard for user feedback review
    """)
