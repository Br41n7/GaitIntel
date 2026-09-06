"""
ClinicalKnowledgeEngine: loads deviation knowledge from JSON files and
answers `analyze(finding_id)` with possible contributors, assessments
to consider, and training targets.

v0.1: JSON files on disk, loaded fresh each call (fine at this scale;
add caching only once it's measurably slow).

v0.2+: swap the loader for a database-backed one. The public interface
(`analyze`) does not change — only `_load_all()` does — so nothing
calling this engine needs to know or care where the knowledge lives.

The engine never returns a diagnosis. It returns structured
possibilities the clinician must interpret. Vocabulary matters here:
"possible contributor", never "cause"; "consider assessing", never
"assessment shows".
"""
import json
import os
from dataclasses import asdict

from app.pipeline.gait_types import ClinicalHypothesis

KNOWLEDGE_BASE_VERSION = "0.1.0"


class ClinicalKnowledgeEngine:
    def __init__(self, knowledge_dir: str | None = None):
        self.knowledge_dir = knowledge_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "knowledge",
            "deviations",
        )

    def _load_all(self) -> dict[str, dict]:
        # v0.2+: replace this method body with a DB query. Everything
        # else in this class stays the same.
        entries = {}
        if not os.path.isdir(self.knowledge_dir):
            return entries
        for filename in os.listdir(self.knowledge_dir):
            if not filename.endswith(".json"):
                continue
            with open(os.path.join(self.knowledge_dir, filename)) as f:
                data = json.load(f)
                entries[data["id"]] = data
        return entries

    def analyze(self, finding_id: str) -> ClinicalHypothesis:
        entries = self._load_all()
        entry = entries.get(finding_id)

        if entry is None:
            # Unknown finding: return an empty, honest result rather
            # than guessing — a missing knowledge entry should be
            # visible to the trainer, not silently papered over.
            return ClinicalHypothesis(
                finding_id=finding_id,
                possible_contributors=[],
                clinical_assessments=[],
                training_targets=[],
                interpretation_confidence="low",
                knowledge_version=KNOWLEDGE_BASE_VERSION,
            )

        return ClinicalHypothesis(
            finding_id=finding_id,
            possible_contributors=entry.get("possible_contributors", []),
            clinical_assessments=entry.get("clinical_assessments", []),
            training_targets=entry.get("training_targets", []),
            interpretation_confidence="moderate",
            knowledge_version=KNOWLEDGE_BASE_VERSION,
        )

    def analyze_as_dict(self, finding_id: str) -> dict:
        return asdict(self.analyze(finding_id))
