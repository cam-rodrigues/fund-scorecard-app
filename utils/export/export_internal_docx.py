from utils.export.export_internal_docx_fancy import export_internal_docx_fancy
from io import BytesIO

buffer = BytesIO()
export_internal_docx_fancy(enhanced_df, proposal_text, buffer)
buffer.seek(0)

st.download_button(
    label="Download Internal DOCX",
    data=buffer,
    file_name="Internal_Proposal.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
