"""Read-only Pinecone cloud connection checks."""
import json
import os
import re
import hashlib
from urllib.parse import quote, urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class PineconeConnectionError(Exception):
    """Connection failure safe to display without credentials."""


def check_connection(secrets=None):
    secrets = secrets or {}
    key = str(os.getenv("PINECONE_API_KEY") or secrets.get("PINECONE_API_KEY", "")).strip()
    name = str(os.getenv("PINECONE_INDEX_NAME") or secrets.get("PINECONE_INDEX_NAME", "")).strip()
    if not key or not name or key.lower().startswith(("your-", "your_", "replace", "<")):
        raise PineconeConnectionError("Set PINECONE_API_KEY and PINECONE_INDEX_NAME in Streamlit secrets or server environment variables.")
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,43}[a-z0-9])?", name):
        raise PineconeConnectionError("PINECONE_INDEX_NAME must be the index name from the Pinecone console, not its URL.")
    headers = {"Api-Key": key, "X-Pinecone-Api-Version": "2025-10", "Content-Type": "application/json"}
    try:
        with urlopen(Request("https://api.pinecone.io/indexes/" + name, headers=headers), timeout=15) as response:
            index = json.loads(response.read())
        if not index.get("status", {}).get("ready"):
            raise PineconeConnectionError("The Pinecone index is still initializing. Retry when it is ready.")
        host = index.get("host", "")
        if not re.fullmatch(r"[a-zA-Z0-9.-]+\.pinecone\.io", host):
            raise PineconeConnectionError("Pinecone returned an invalid index host.")
        with urlopen(Request("https://" + host + "/describe_index_stats", data=b"{}", headers=headers, method="POST"), timeout=15) as response:
            stats = json.loads(response.read())
        return {"dimension": index.get("dimension"), "metric": index.get("metric"),
                "model": (index.get("embed") or {}).get("model"), "vector_count": stats.get("totalVectorCount", 0),
                "host": host, "field_map": (index.get("embed") or {}).get("field_map", {})}
    except HTTPError as exc:
        if exc.code in (401, 403):
            message = "Pinecone rejected access. Check the API key and its index permissions."
        elif exc.code == 404:
            message = "Pinecone index was not found. Check PINECONE_INDEX_NAME and that the key belongs to the same project."
        else:
            message = f"Pinecone connection check failed (HTTP {exc.code}). Retry later."
        raise PineconeConnectionError(message) from None
    except (URLError, TimeoutError, OSError):
        raise PineconeConnectionError("Could not reach Pinecone. Check the app's network access and internet connection.") from None
    except (ValueError, TypeError, AttributeError):
        raise PineconeConnectionError("Pinecone returned an invalid connection response.") from None


def document_chunks(document):
    """Bounded overlapping text chunks with stable IDs and source metadata."""
    records = []
    for page_index, page in enumerate(document.pages):
        text = str(page.get("text", ""))
        for start in range(0, len(text), 1000):
            chunk = text[start:start + 1200]
            if not chunk.strip():
                continue
            identity = f"{document.patient_id}|{document.kind}|{document.hash}|{page_index}|{start}"
            records.append({"_id": hashlib.sha256(identity.encode()).hexdigest(), "chunk_text": chunk,
                            "patient_id": document.patient_id, "document_id": document.id,
                            "source_name": document.name, "source_hash": document.hash,
                            "locator": str(page.get("locator", f"Page {page_index + 1}")),
                            "chunk_start": start, "page_index": page_index, "kind": document.kind,
                            "record_type": "source",
                            "document_json": document.model_dump_json(exclude={"pages"})})
            if start + 1200 >= len(text):
                break
    return records


def index_document(document, secrets=None, observations=None):
    """Embed and upsert source text into the selected patient's namespace."""
    if document.status == "Quarantined":
        raise PineconeConnectionError("Quarantined documents cannot be indexed in Pinecone.")
    records = document_chunks(document)
    if not records:
        raise PineconeConnectionError("No readable text is available to index.")
    chunk_count = len(records)
    observations = observations or []
    for observation in observations:
        if observation.patient_id != document.patient_id or observation.document_id != document.id:
            raise PineconeConnectionError("Observation does not belong to the document being indexed.")
    for record in records:
        record["source_chunk_count"] = chunk_count
        record["observation_count"] = len(observations)
    for number, observation in enumerate(observations):
        identity = f"{document.patient_id}|{document.kind}|{document.hash}|observation|{number}"
        records.append({"_id": hashlib.sha256(identity.encode()).hexdigest(), "record_type": "observation",
                        "chunk_text": observation.source_text or observation.name,
                        "patient_id": document.patient_id, "document_id": document.id,
                        "source_hash": document.hash, "kind": document.kind,
                        "observation_json": observation.model_dump_json()})
    info = check_connection(secrets)
    field = info["field_map"].get("text")
    if not info["model"] or not isinstance(field, str) or not field:
        raise PineconeConnectionError("This index needs integrated text embeddings with a text field mapping.")
    key = str(os.getenv("PINECONE_API_KEY") or (secrets or {}).get("PINECONE_API_KEY", "")).strip()
    namespace = "patient-" + document.patient_id
    headers = {"Api-Key": key, "X-Pinecone-Api-Version": "2025-10", "Content-Type": "application/x-ndjson"}
    endpoint = f"https://{info['host']}/records/namespaces/{quote(namespace, safe='')}/upsert"
    try:
        for offset in range(0, len(records), 96):
            batch = []
            for record in records[offset:offset + 96]:
                record = record.copy()
                text = record.pop("chunk_text")
                record[field] = text
                batch.append(json.dumps(record, ensure_ascii=False))
            payload = ("\n".join(batch) + "\n").encode("utf-8")
            with urlopen(Request(endpoint, data=payload, headers=headers, method="POST"), timeout=30) as response:
                if response.status != 201:
                    raise PineconeConnectionError("Pinecone did not confirm chunk storage. Retry the document sync.")
    except HTTPError as exc:
        raise PineconeConnectionError(f"Pinecone chunk upload failed (HTTP {exc.code}). Check write permissions, embedding configuration, and quota. Some batches may have saved; retrying uses the same chunk IDs.") from None
    except (URLError, TimeoutError, OSError):
        raise PineconeConnectionError("Could not confirm Pinecone chunk storage. Check network access and retry. Stable chunk IDs prevent duplicates.") from None
    return {"chunk_count": chunk_count, "namespace": namespace}


def load_patient_records(patient_id, secrets=None):
    """List and fetch the complete selected namespace, never similarity top-k."""
    info = check_connection(secrets)
    key = str(os.getenv("PINECONE_API_KEY") or (secrets or {}).get("PINECONE_API_KEY", "")).strip()
    headers = {"Api-Key": key, "X-Pinecone-Api-Version": "2025-10"}
    base = "https://" + info["host"]
    namespace = "patient-" + patient_id
    records, token, seen = [], None, set()
    try:
        while True:
            params = {"namespace": namespace, "limit": 100}
            if token:
                params["paginationToken"] = token
            with urlopen(Request(base + "/vectors/list?" + urlencode(params), headers=headers), timeout=15) as response:
                listing = json.loads(response.read())
            ids = [v["id"] for v in listing.get("vectors", [])]
            if ids:
                params = [("namespace", namespace)] + [("ids", rid) for rid in ids]
                with urlopen(Request(base + "/vectors/fetch?" + urlencode(params), headers=headers), timeout=15) as response:
                    fetched = json.loads(response.read()).get("vectors", {})
                if set(fetched) != set(ids):
                    raise PineconeConnectionError("Some Pinecone records are not yet readable. Retry Refresh patient records shortly.")
                for vector in fetched.values():
                    record = vector.get("metadata", {})
                    if record.get("patient_id") != patient_id:
                        raise PineconeConnectionError("Pinecone record patient metadata does not match the selected patient. No cloud records loaded.")
                    records.append(record)
            token = listing.get("pagination", {}).get("next")
            if not token:
                break
            if token in seen:
                raise PineconeConnectionError("Pinecone returned repeated pagination. No cloud records loaded.")
            seen.add(token)
        return restore_documents(patient_id, records, info["field_map"].get("text", "chunk_text"))
    except HTTPError as exc:
        raise PineconeConnectionError(f"Could not load patient records from Pinecone (HTTP {exc.code}). Check read permissions.") from None
    except (URLError, TimeoutError, OSError):
        raise PineconeConnectionError("Could not load Pinecone patient records. Check network access and retry.") from None
    except (ValueError, KeyError, TypeError, AttributeError):
        raise PineconeConnectionError("Pinecone patient records have invalid or incomplete metadata. Re-sync their source documents.") from None


def restore_documents(patient_id, records, text_field):
    """Restore source evidence and typed observations; parse legacy text records."""
    from healthlens.models import Document, Observation, DischargeSummary
    from healthlens.ingestion import ingest
    from healthlens.discharge import extract_sections
    groups = {}
    for record in records:
        if record.get("patient_id") != patient_id:
            raise PineconeConnectionError("Patient scope mismatch in Pinecone records.")
        groups.setdefault((record["source_hash"], record.get("kind", "Laboratory report")), []).append(record)
    restored = []
    for (source_hash, _), group in groups.items():
        sources = [r for r in group if r.get("record_type", "source") == "source"]
        if not sources:
            raise PineconeConnectionError("Pinecone document source is incomplete. Re-sync the document.")
        first = sources[0]
        expected = first.get("source_chunk_count")
        if expected is not None and len(sources) != int(expected):
            raise PineconeConnectionError("Pinecone document chunks are incomplete. Re-sync the document.")
        pages = {}
        for record in sources:
            page_key = (int(record.get("page_index", 0)), record["locator"])
            pages.setdefault(page_key, []).append(record)
        reconstructed = []
        for (_, locator), chunks in sorted(pages.items()):
            text = ""
            for chunk in sorted(chunks, key=lambda r: int(r["chunk_start"])):
                start = int(chunk["chunk_start"])
                part = chunk[text_field]
                if start > len(text):
                    raise PineconeConnectionError("Pinecone source has missing text. Re-sync the document.")
                text = text[:start] + part + text[start + len(part):]
            reconstructed.append({"text": text, "locator": locator})
        if first.get("document_json"):
            metadata = json.loads(first["document_json"])
            if metadata["patient_id"] != patient_id or metadata["hash"] != source_hash:
                raise PineconeConnectionError("Pinecone document scope mismatch.")
            document = Document.model_validate({**metadata, "pages": reconstructed, "source": "Pinecone"})
        else:
            document = Document(id=first["document_id"], patient_id=patient_id, name=first["source_name"],
                                hash=source_hash, kind=first.get("kind", "Laboratory report"), pages=reconstructed, source="Pinecone")
        observation_records = [r for r in group if r.get("record_type") == "observation"]
        expected = first.get("observation_count")
        if expected is not None and int(expected) != len(observation_records):
            raise PineconeConnectionError("Pinecone laboratory records are incomplete. Re-sync the document.")
        observations = [Observation.model_validate(json.loads(r["observation_json"])) for r in observation_records]
        if any(o.patient_id != patient_id or o.document_id != document.id for o in observations):
            raise PineconeConnectionError("Pinecone observation scope mismatch.")
        summary = None
        if document.kind == "Discharge summary":
            summary = DischargeSummary(patient_id=patient_id, document_id=document.id, sections=extract_sections(reconstructed))
        elif expected is None:
            # Old text-only vectors have no typed lab data; use the existing parser.
            _, observations = ingest("\n".join(p["text"] for p in reconstructed).encode(), "restored.txt", patient_id)
            for observation in observations:
                observation.document_id = document.id
            document.warnings.append("Restored from legacy text chunks. Re-sync the original report to preserve table extraction and exact source locations.")
        if observations:
            document.status = "Imported"
        restored.append((document, observations, summary))
    return restored
