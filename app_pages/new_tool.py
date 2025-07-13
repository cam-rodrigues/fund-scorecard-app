import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Flash Idea Board", layout="centered")
st.title("🧠 Flash Idea Board")

st.markdown("Write fast. Organize later.")
st.markdown("---")

if 'ideas' not in st.session_state:
    st.session_state.ideas = []

with st.form("idea_form"):
    new_idea = st.text_area("Add a new idea:", height=100)
    tag = st.selectbox("Tag (optional):", ["💡 Idea", "🔥 Urgent", "📊 Research", "🎨 Design", "🧪 Experiment", "None"])
    submitted = st.form_submit_button("Add")
    if submitted and new_idea.strip():
        timestamp = datetime.now().strftime("%b %d, %Y %I:%M %p")
        st.session_state.ideas.append({
            "text": new_idea.strip(),
            "tag": tag if tag != "None" else "",
            "time": timestamp
        })

st.markdown("### Your Ideas")

if not st.session_state.ideas:
    st.info("No ideas yet. Start typing above.")
else:
    for i, idea in enumerate(reversed(st.session_state.ideas)):
        idx = len(st.session_state.ideas) - 1 - i
        st.markdown(f"**{idea['tag']}** {idea['text']}")
        st.caption(f"Added {idea['time']}")
        cols = st.columns([1, 1])
        if cols[0].button("⬆️ Move Up", key=f"up_{idx}") and idx > 0:
            st.session_state.ideas[idx - 1], st.session_state.ideas[idx] = st.session_state.ideas[idx], st.session_state.ideas[idx - 1]
            st.experimental_rerun()
        if cols[1].button("❌ Delete", key=f"del_{idx}"):
            st.session_state.ideas.pop(idx)
            st.experimental_rerun()
        st.markdown("---")

if st.session_state.ideas:
    if st.download_button("Download All Ideas as .txt", 
                          data="\n\n".join(f"{i['tag']} {i['text']}".strip() for i in st.session_state.ideas),
                          file_name="ideas.txt"):
        st.success("File ready!")
