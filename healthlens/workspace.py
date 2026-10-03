"""Session-isolated demo repository with review history and stale report tracking."""
import hashlib

from healthlens.demo import PATIENTS, demo_records
from healthlens.discharge import discharge_patient_names
from healthlens.models import DischargeSummary, Document, Observation, Revision
from healthlens.workflow import analyze


class Workspace:
    def __init__(self):
        self.patients = [p.model_copy(deep=True) for p in PATIENTS]
        self.documents: list[Document] = []
        self.observations: list[Observation] = []
        self.revisions: list[Revision] = []
        self.reports: list[dict] = []
        self.originals: dict[str, bytes] = {}
        self.discharge_summaries: list[DischargeSummary] = []
        self.ensure_demo_records()

    @classmethod
    def from_session(cls, existing):
        """Upgrade session objects retained from an earlier app version in place."""
        if existing is None:
            return cls()
        if type(existing) is cls:
            workspace = existing
        else:
            workspace = cls.__new__(cls)
            workspace.__dict__.update(vars(existing))
        # Older releases may not have every repository collection.
        defaults = dict(patients=[p.model_copy(deep=True) for p in PATIENTS],
                        documents=[], observations=[], revisions=[], reports=[], originals={}, discharge_summaries=[])
        for name, value in defaults.items():
            workspace.__dict__.setdefault(name, value)
        # Apply the name-presence policy to discharge uploads in open sessions.
        documents = {d.id: d for d in workspace.documents if d.kind == "Discharge summary"}
        for summary in workspace.discharge_summaries:
            document = documents.get(summary.document_id)
            if document is not None and discharge_patient_names(document.pages):
                if summary.status == "quarantined":
                    summary.status = "needs_review"
                if document.status == "Quarantined":
                    document.status = "Needs review"
                document.warnings = [warning for warning in document.warnings
                                     if not warning.startswith(("Patient name could not be matched to the selected profile.",
                                                                "No patient name was found in the document."))]
        return workspace

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

    def discharges(self, patient_id) -> list[DischargeSummary]:
        return [s for s in self.discharge_summaries if s.patient_id == patient_id]

    def add_discharge(self, document, summary, original) -> bool:
        if document.kind != "Discharge summary" or summary.patient_id != document.patient_id or summary.document_id != document.id:
            raise ValueError("Discharge summary does not belong to the imported document.")
        if any(d.hash == document.hash and d.patient_id == document.patient_id and d.kind == document.kind for d in self.documents):
            return False
        self.documents.append(document)
        self.discharge_summaries.append(summary)
        self.originals[document.id] = original
        return True

    def fingerprint(self, patient_id) -> str:
        manifest = "|".join(sorted(o.model_dump_json() for o in self.obs(patient_id)))
        manifest += "|".join(sorted(d.id for d in self.docs(patient_id)))
        return hashlib.sha256(manifest.encode()).hexdigest()

    def add(self, document, observations, original) -> bool:
        if any(o.patient_id != document.patient_id or o.document_id != document.id for o in observations):
            raise ValueError("Observation does not belong to the imported document.")
        previous = next((d for d in self.documents if d.hash == document.hash and d.patient_id == document.patient_id), None)
        if previous:
            if previous.status not in {"Text only", "Quarantined"} or not observations or any(o.document_id == previous.id for o in self.observations):
                return False
            # Retry a previously unparsed upload after the extractor gains support.
            self.documents.remove(previous)
            self.originals.pop(previous.id, None)
        self.documents.append(document)
        self.observations.extend(observations)
        self.originals[document.id] = original
        if observations:
            self.refresh_analysis(document.patient_id)
        return True

    def refresh_analysis(self, patient_id):
        fingerprint = self.fingerprint(patient_id)
        if not any(r["patient_id"] == patient_id and r["fingerprint"] == fingerprint for r in self.reports):
            self.reports.append(analyze(patient_id, self.obs(patient_id), fingerprint))

    def activate_pending_uploads(self):
        """Make uploads from already-open sessions available without a review step."""
        changed = set()
        for document in self.documents:
            if document.source != "Local upload" or document.status == "Quarantined":
                continue
            for observation in self.obs(document.patient_id):
                if observation.document_id == document.id and observation.status == "needs_review":
                    observation.status = "accepted"
                    document.status = "Imported"
                    changed.add(document.patient_id)
        for patient_id in changed:
            self.refresh_analysis(patient_id)

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
        self.discharge_summaries = [s for s in self.discharge_summaries if s.document_id != document_id]
        # Remove derived reports rather than retaining deleted source content.
        self.reports = [r for r in self.reports if r["patient_id"] != patient_id]
