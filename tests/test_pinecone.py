import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from healthlens.pinecone_db import PineconeConnectionError, check_connection
from healthlens.pinecone_db import document_chunks, index_document
from healthlens.models import Document
from healthlens.models import Observation, Patient
from healthlens.pinecone_db import restore_documents, load_patient_records


def test_connection_checks_index_and_data_plane(monkeypatch):
    monkeypatch.setenv("PINECONE_API_KEY", "test-key")
    monkeypatch.setenv("PINECONE_INDEX_NAME", "healthlens")
    responses = []
    for payload in [{"status": {"ready": True}, "host": "healthlens.svc.pinecone.io", "dimension": 1024, "metric": "cosine"}, {"totalVectorCount": 12}]:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        responses.append(response)
    with patch("healthlens.pinecone_db.urlopen", side_effect=responses) as call:
        info = check_connection()
    assert info["vector_count"] == 12
    assert call.call_args.args[0].full_url == "https://healthlens.svc.pinecone.io/describe_index_stats"
    assert call.call_args.args[0].method == "POST"


@pytest.mark.parametrize("status,message", [(401, "rejected access"), (404, "not found")])
def test_connection_errors_hide_provider_details(status, message, monkeypatch):
    monkeypatch.setenv("PINECONE_API_KEY", "test-key")
    monkeypatch.setenv("PINECONE_INDEX_NAME", "healthlens")
    with patch("healthlens.pinecone_db.urlopen", side_effect=HTTPError("https://example", status, "secret provider details", {}, None)):
        with pytest.raises(PineconeConnectionError, match=message):
            check_connection()


def test_chunks_cover_source_and_have_stable_patient_scoped_ids():
    doc = Document(id="doc", patient_id="P-1", name="test.txt", hash="abc",
                   pages=[{"text": "a" * 2500, "locator": "Page 1"}])
    chunks = document_chunks(doc)
    assert [c["chunk_start"] for c in chunks] == [0, 1000, 2000]
    assert len(chunks[-1]["chunk_text"]) == 500
    assert [c["_id"] for c in chunks] == [c["_id"] for c in document_chunks(doc.model_copy(update={"id": "retry"}))]
    assert chunks[0]["_id"] != document_chunks(doc.model_copy(update={"patient_id": "P-2"}))[0]["_id"]


def test_index_document_uses_mapped_text_and_patient_namespace(monkeypatch):
    monkeypatch.setenv("PINECONE_API_KEY", "test-key")
    doc = Document(patient_id="P-1", name="test.txt", hash="abc", pages=[{"text": "Source text", "locator": "Page 1"}])
    info = {"host": "test.svc.pinecone.io", "model": "llama-text-embed-v2", "field_map": {"text": "content"}}
    response = MagicMock()
    response.__enter__.return_value.status = 201
    with patch("healthlens.pinecone_db.check_connection", return_value=info), patch("healthlens.pinecone_db.urlopen", return_value=response) as post:
        result = index_document(doc)
    assert result == {"chunk_count": 1, "namespace": "patient-P-1"}
    request = post.call_args.args[0]
    assert request.full_url.endswith("/records/namespaces/patient-P-1/upsert")
    record = json.loads(request.data)
    assert record["content"] == "Source text"
    assert record["patient_id"] == "P-1"
    assert "chunk_text" not in record


def test_quarantined_document_is_not_sent_to_cloud():
    doc = Document(patient_id="P-1", name="test.txt", hash="abc", pages=[], status="Quarantined")
    with patch("healthlens.pinecone_db.urlopen") as request:
        with pytest.raises(PineconeConnectionError, match="Quarantined"):
            index_document(doc)
    request.assert_not_called()


def cloud_fixture():
    doc = Document(id="cloud-doc", patient_id="C-1", name="cloud.pdf", hash="cloud-hash",
                   pages=[{"text": "Patient: Cloud Patient\nHemoglobin evidence", "locator": "Page 1"}])
    observation = Observation(id="cloud-obs", patient_id="C-1", document_id=doc.id,
                              name="Hemoglobin", value=13.9, original_value="13.9", unit="g/dL",
                              low=12, high=15.5, date="2026-01-01", locator="Page 1, line 2",
                              source_text="Hemoglobin evidence", status="accepted")
    records = document_chunks(doc)
    for record in records:
        record["source_chunk_count"] = len(records)
        record["observation_count"] = 1
    records.append({"record_type": "observation", "patient_id": "C-1", "source_hash": doc.hash,
                    "observation_json": observation.model_dump_json()})
    return records


def test_restore_preserves_values_and_patient_scope():
    records = cloud_fixture()
    restored = restore_documents("C-1", records, "chunk_text")
    document, observations, _ = restored[0]
    assert document.source == "Pinecone"
    assert observations[0].value == 13.9
    assert str(observations[0].date) == "2026-01-01"
    with pytest.raises(PineconeConnectionError, match="scope mismatch"):
        restore_documents("C-2", records, "chunk_text")
    with pytest.raises(PineconeConnectionError, match="incomplete"):
        restore_documents("C-1", records[:-1], "chunk_text")


def test_patient_selection_restores_all_sections_without_cross_patient_data(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("PINECONE_API_KEY", "test")
    monkeypatch.setenv("PINECONE_INDEX_NAME", "healthlens")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test")
    records = restore_documents("C-1", cloud_fixture(), "chunk_text")
    def load(pid, secrets):
        return records if pid == "C-1" else []
    with patch("healthlens.supabase.list_patients", return_value=[Patient(id="C-1", name="Cloud Patient", initials="CP")]), patch("healthlens.pinecone_db.load_patient_records", side_effect=load):
        app = AppTest.from_file("app.py", default_timeout=30).run()
        app.selectbox(key="patient_id").select("C-1").run()
        assert not app.exception
        assert len(app.session_state.workspace.obs("C-1")) == 1
        for page in ["trends", "analysis", "evidence", "timeline", "reports", "documents"]:
            app.switch_page(f"app_pages/{page}.py").run()
            assert not app.exception, page
        app.selectbox(key="patient_id").select("DUMMY-0001").run()
        assert all(o.patient_id == "DUMMY-0001" for o in app.session_state.workspace.obs("DUMMY-0001"))


def test_loader_fetches_only_selected_namespace(monkeypatch):
    monkeypatch.setenv("PINECONE_API_KEY", "test")
    records = cloud_fixture()
    listing = {"vectors": [{"id": str(i)} for i in range(len(records))]}
    fetched = {"vectors": {str(i): {"metadata": record} for i, record in enumerate(records)}}
    responses = []
    for payload in [listing, fetched]:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        responses.append(response)
    with patch("healthlens.pinecone_db.check_connection", return_value={"host": "test.svc.pinecone.io", "field_map": {"text": "chunk_text"}}), patch("healthlens.pinecone_db.urlopen", side_effect=responses) as get:
        restored = load_patient_records("C-1")
    assert restored[0][0].patient_id == "C-1"
    assert all("namespace=patient-C-1" in call.args[0].full_url for call in get.call_args_list)
