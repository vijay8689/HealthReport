"""Session-isolated demo repository with review history and stale report tracking."""
import hashlib

from healthlens.demo import PATIENTS, demo_records
from healthlens.models import Document, Observation, Revision
from healthlens.workflow import analyze


class Workspace:
    def __init__(self):
        self.patients = [p.model_copy(deep=True) for p in PATIENTS]
        self.documents: list[Document] = []
        self.observations: list[Observation] = []
        self.revisions: list[Revision] = []
        self.reports: list[dict] = []
        self.originals: dict[str, bytes] = {}
        self.ensure_demo_records()

    def ensure_demo_records(self):
        """Add the bundled dummy history to new and already-open demo sessions."""
        if self.docs("DUMMY-0001"):
            return
        documents, observations, revisions, originals = demo_records()
        self.documents.extend(documents)
        self.observations.extend(observations)
        self.revisions.extend(revisions)
        self.originals.update(originals)
        self.reports.append(analyze(
            "DUMMY-0001", self.obs("DUMMY-0001"), self.fingerprint("DUMMY-0001")
        ))

    def patient(self, patient_id):
        return next(p for p in self.patients if p.id == patient_id)

    def docs(self, patient_id) -> list[Document]:
        return sorted([d for d in self.documents if d.patient_id == patient_id],
                      key=lambda d: str(d.date or ""), reverse=True)

    def obs(self, patient_id) -> list[Observation]:
        return [o for o in self.observations if o.patient_id == patient_id]

    def fingerprint(self, patient_id) -> str:
        manifest = "|".join(sorted(o.model_dump_json() for o in self.obs(patient_id)))
        manifest += "|".join(sorted(d.id for d in self.docs(patient_id)))
        return hashlib.sha256(manifest.encode()).hexdigest()

    def add(self, document, observations, original) -> bool:
        if any(d.hash == document.hash and d.patient_id == document.patient_id for d in self.documents):
            return False
        if any(o.patient_id != document.patient_id or o.document_id != document.id for o in observations):
            raise ValueError("Observation does not belong to the imported document.")
        self.documents.append(document)
        self.observations.extend(observations)
        self.originals[document.id] = original
        return True

    def review(self, patient_id, observation_id, expected_version, updates, reason):
        old = next(o for o in self.obs(patient_id) if o.id == observation_id)
        if old.version != expected_version:
            raise ValueError("This observation changed. Reload it before saving.")
        if not reason.strip():
            raise ValueError("Please enter a review reason.")
        allowed = {"value", "unit", "low", "high", "date", "status", "comparator"}
        if set(updates) - allowed:
            raise ValueError("Unsupported observation update.")
        new = Observation.model_validate({**old.model_dump(), **updates, "version": old.version + 1})
        self.revisions.append(Revision(observation_id=old.id, reason=reason,
                                      before=old.model_dump(mode="json"), after=new.model_dump(mode="json")))
        self.observations[self.observations.index(old)] = new
        doc = next(d for d in self.documents if d.id == old.document_id)
        related = [o for o in self.observations if o.document_id == doc.id]
        doc.status = "Needs review" if any(o.status == "needs_review" for o in related) else "Reviewed"

    def remove_document(self, patient_id, document_id):
        doc = next(d for d in self.docs(patient_id) if d.id == document_id)
        self.documents.remove(doc)
        ids = {o.id for o in self.observations if o.document_id == document_id}
        self.observations = [o for o in self.observations if o.id not in ids]
        self.revisions = [r for r in self.revisions if r.observation_id not in ids]
        self.originals.pop(document_id, None)
        # Remove derived reports rather than retaining deleted source content.
        self.reports = [r for r in self.reports if r["patient_id"] != patient_id]
