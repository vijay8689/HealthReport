import streamlit as st

from healthlens.discharge import ingest_discharge
from healthlens.ingestion import IntakeError
from ui.components import heading, panel_title, patient_id, workspace

ws, pid = workspace(), patient_id()
heading("Discharge summary", "Upload a discharge document and organize its contents into separate sections.", "DISCHARGE RECORDS")
st.caption("PDF, PNG, JPG or JPEG · up to 20 MB. Records are stored in this browser session only, and are lost when the session ends. Download the structured data to keep a copy.")

with st.container(border=True):
    panel_title("Upload a discharge summary", f"Selected patient: {ws.patient(pid).name}")
    with st.form(f"discharge_upload_{pid}"):
        upload = st.file_uploader("Choose discharge document", type=["pdf", "png", "jpg", "jpeg"], key=f"discharge_file_{pid}")
        st.caption("Text is extracted locally and organized by document headings. A patient name must be present; it does not need to match the selected profile. The document is saved under the selected patient. Scanned PDFs and images require English Tesseract OCR. Unrecognized content is kept under Other information.")
        submitted = st.form_submit_button("Analyze and save", type="primary", icon=":material/upload_file:")
    if submitted:
        if upload is None:
            st.warning("Choose a PDF or image first.")
        else:
            try:
                with st.spinner("Reading and organizing the discharge summary…"):
                    content = upload.getvalue()
                    document, summary = ingest_discharge(content, upload.name, pid, ws.patient(pid).name)
                    saved = ws.add_discharge(document, summary, content)
                if not saved:
                    st.info("This discharge document has already been uploaded for this patient.")
                elif summary.status == "quarantined":
                    st.warning("Saved in quarantine. No readable patient name was found in the document.")
                else:
                    st.success("Discharge summary saved in separate sections. Check the extracted details against the source.")
            except IntakeError as error:
                st.error(str(error))

summaries = ws.discharges(pid)
if not summaries:
    st.info("No discharge summaries uploaded for this patient yet.")
else:
    documents = {d.id: d for d in ws.docs(pid)}
    selected = st.selectbox("Saved discharge summaries", [s.id for s in summaries],
                            format_func=lambda sid: documents[next(s.document_id for s in summaries if s.id == sid)].name,
                            key=f"discharge_selected_{pid}")
    summary = next(s for s in summaries if s.id == selected)
    document = documents[summary.document_id]
    st.caption(f"Status: {summary.status.replace('_', ' ')}")
    for warning in document.warnings:
        if warning.startswith("Text was read using OCR."):
            st.info(warning)
        else:
            st.warning(warning)
    for title, entries in summary.sections.items():
        with st.expander(f"{title} · {len(entries)} source lines", expanded=bool(entries)):
            if not entries:
                st.caption("Not found in the document.")
            else:
                st.text("\n".join(entry.text for entry in entries))
                st.caption("Sources: " + "; ".join(dict.fromkeys(entry.locator for entry in entries)))
    with st.expander("Full extracted source"):
        for page in document.pages:
            st.caption(page["locator"])
            st.code(page["text"], language=None, wrap_lines=True)
    if summary.status == "needs_review" and st.button("Mark as checked against source", key=f"discharge_review_{summary.id}"):
        summary.status = "reviewed"
        document.status = "Reviewed"
        st.rerun()
    st.download_button("Download structured discharge data", summary.model_dump_json(indent=2),
                       f"discharge-{summary.id}.json", mime="application/json", key=f"discharge_json_{summary.id}")
    st.download_button("Download original document", ws.originals[document.id], document.name,
                       key=f"discharge_original_{summary.id}")
