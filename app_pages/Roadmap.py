import streamlit as st

def run():
    st.markdown("## Product Roadmap")

    st.markdown("### ✅ Recently Completed")
    st.write("""
    - Professional sidebar with custom styling
    - Secure file handling (fully in-memory)
    - Smart fuzzy matching with match preview
    - User Manual, FAQ, and Changelog documentation tabs
    """)

    st.markdown("### 🚧 In Progress")
    st.write("""
    - Enhanced Excel support (multi-sheet detection, dynamic cell targeting)
    - Optional CSV export of match preview
    - Match confidence scoring (e.g., 92% match accuracy)
    - Admin dashboard to review submitted user requests
    """)

    st.markdown("### 🔮 Planned Features")
    st.write("""
    - Smart AI match review (flag low-confidence matches)
    - Integration with cloud storage (optional enterprise toggle)
    - Slack/email notifications for batch results
    - Theme switcher (light/dark mode)
    """)
