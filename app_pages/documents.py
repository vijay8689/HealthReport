import streamlit as st
from healthlens.ingestion import IntakeError, ingest
from healthlens.models import Patient
from ui.components import doc_rows, heading, panel_title, patient_id, workspace

ws, pid = workspace(), patient_id()
heading("Good insights start with good records.", "Import a report, inspect its source, and review extracted observations.", "DOCUMENT LIBRARY")
st.session_state.setdefault("document_view", "Library")
tab = st.segmented_control("Document view", ["Library", "Upload reports"], key="document_view")
if tab == "Upload reports":
    left, right = st.columns([1.8, 1])
    with left:
        with st.container(border=True):
            panel_title("Bring your records together", "PDF, DOCX, TXT, PNG or JPG · up to 20 MB per file")
            st.caption("Files stay in this local browser session and are not sent to an AI provider. Use only reports you are authorized to process.")
            with st.form(f"upload_{pid}"):
                uploads = st.file_uploader("Choose reports", type=["pdf", "docx", "txt", "png", "jpg", "jpeg"], accept_multiple_files=True)
                st.write(f"Import into **{ws.patient(pid).name} · {pid}**")
                association = st.selectbox(
                    "Patient association",
                    ["Use Patient ID from each report", "Use selected patient"],
                    help="A detected report ID creates a local patient profile when needed.",
                )
                consent = st.checkbox("I am authorized to process these reports in this local workspace.")
                submit = st.form_submit_button("Import and extract", icon=":material/upload_file:", type="primary", width="stretch")
            if submit:
                if not uploads:
                    st.warning("Choose at least one report first.")
                elif not consent:
                    st.warning("Confirm the synthetic data and patient association before import.")
                elif len(uploads) > 20:
                    st.warning("Import up to 20 documents at a time.")
                else:
                    progress = st.progress(0, text="Reading reports…")
                    imported_patient_ids = []
                    for index, upload in enumerate(uploads):
                        try:
                            doc, extracted = ingest(
                                upload.getvalue(), upload.name, pid,
                                use_source_patient=association == "Use Patient ID from each report",
                            )
                            if doc.patient_id not in {patient.id for patient in ws.patients}:
                                initials = "".join(part[0] for part in doc.patient_id.split("-") if part)[:2].upper() or "PT"
                                ws.patients.append(Patient(
                                    id=doc.patient_id,
                                    name=f"Patient {doc.patient_id}",
                                    initials=initials,
                                    description="Profile created from an imported report Patient ID",
                                ))
                            if ws.add(doc, extracted, upload.getvalue()):
                                imported_patient_ids.append(doc.patient_id)
                                st.session_state.last_import_patient_id = doc.patient_id
                                if doc.status == "Quarantined":
                                    st.warning(f"{doc.name}: quarantined. " + " ".join(doc.warnings))
                                else:
                                    st.success(f"{doc.name}: {len(extracted)} observations ready for review.")
                                    for warning in doc.warnings:
                                        st.info(warning)
                            else:
                                st.info(f"{upload.name}: duplicate content skipped.")
                        except IntakeError as error:
                            st.error(f"{upload.name}: {error}")
                        progress.progress((index + 1) / len(uploads), text=f"Processed {index + 1} of {len(uploads)} reports")
            review_patient = st.session_state.get("last_import_patient_id", pid)
            if any(o.status == "needs_review" for o in ws.obs(review_patient)):
                if st.button("Review extracted observations", icon=":material/fact_check:"):
                    st.session_state.pending_patient_id = review_patient
                    st.session_state[f"review_filter_{review_patient}"] = "Needs review"
                    st.switch_page("app_pages/evidence.py")
    with right:
        with st.container(border=True):
            panel_title("Import a report", "Associate the document with its source Patient ID or the selected profile")
            st.markdown("**How import works**\n\n1. File format and size checks\n2. Text extraction or available OCR\n3. Patient ID validation\n4. Laboratory row extraction\n5. Human review before analysis")
            st.caption("The extractor supports pipe-separated rows and common multi-line lab panels. Unsupported content remains viewable as source text; no values are guessed. OCR requires local English Tesseract.")
else:
    a, b = st.columns([2, 1])
    with a:
        search = st.text_input("Find a document", placeholder="Search by filename…", icon=":material/search:")
    with b:
        status = st.selectbox("Document status", ["All statuses", "Reviewed", "Needs review", "Quarantined", "Text only"])
    docs = [d for d in ws.docs(pid) if search.lower() in d.name.lower() and (status == "All statuses" or d.status == status)]
    with st.container(border=True):
        panel_title(f"{len(docs)} documents", "Each record retains its original text and source location")
        doc_rows(docs)
    with st.expander("Add a report", expanded=not docs):
        st.caption("Use the Upload reports tab above to import a synthetic document.")
    if docs:
        selected = st.selectbox("Preview source document", [d.id for d in docs], format_func=lambda x:next(d.name for d in docs if d.id == x))
        doc = next(d for d in docs if d.id == selected)
        for warning in doc.warnings:
            st.warning(warning)
        for page in doc.pages:
            with st.expander(page["locator"], expanded=len(doc.pages) == 1):
                st.code(page["text"], language=None, wrap_lines=True)
        st.caption(f"SHA-256: {doc.hash} · Version {doc.version}")
        data = ws.originals.get(doc.id, "\n".join(p["text"] for p in doc.pages).encode())
        st.download_button("Download source", data, doc.name, icon=":material/download:")
