import { useState } from "react";
import type { FindingWithKnowledge } from "../types";

export default function FindingCard({ item }: { item: FindingWithKnowledge }) {
  const [expanded, setExpanded] = useState(false);
  const { finding, clinical_hypothesis } = item;

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <div>
          <p className="text-sm font-medium text-slate-900">
            ⚠ {finding.id.replace(/_/g, " ")} ({finding.side})
          </p>
          <p className="text-xs text-slate-600">
            {finding.phase.replace(/_/g, " ")} · {finding.value}
            {finding.unit} · detection confidence {Math.round(finding.confidence * 100)}%
          </p>
        </div>
        <span className="text-slate-400">{expanded ? "−" : "+"}</span>
      </button>

      {expanded && (
        <div className="space-y-4 border-t border-amber-200 px-4 py-4 text-sm">
          <p className="text-xs text-slate-500">
            Observed pattern — not a diagnosis. Interpretation confidence:{" "}
            <span className="font-medium">{clinical_hypothesis.interpretation_confidence}</span>. Requires
            clinical correlation.
          </p>

          <div>
            <p className="font-medium text-slate-700">Possible contributors</p>
            <ol className="mt-1 list-decimal space-y-1 pl-5">
              {clinical_hypothesis.possible_contributors.map((c) => (
                <li key={c.id}>{c.description}</li>
              ))}
            </ol>
          </div>

          <div>
            <p className="font-medium text-slate-700">Clinical assessments to consider</p>
            <ul className="mt-1 space-y-1 pl-1">
              {clinical_hypothesis.clinical_assessments.map((a) => (
                <li key={a.id}>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" /> {a.name}
                  </label>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="font-medium text-slate-700">Training targets</p>
            <ul className="mt-1 space-y-1 pl-1">
              {clinical_hypothesis.training_targets.map((t) => (
                <li key={t.id}>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" /> {t.name}
                  </label>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
