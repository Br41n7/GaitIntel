import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, mediaUrl, poseApi } from "../lib/api";
import FindingCard from "../components/FindingCard";
import PoseOverlayVideo from "../components/PoseOverlayVideo";
import VideoUpload from "../components/VideoUpload";
import type { Assessment } from "../types";
import type { PoseFrame } from "../types/pose";

const METRIC_LABELS: Record<string, string> = {
  cadence_steps_per_min: "Cadence (steps/min)",
  step_asymmetry: "Step asymmetry",
  left_knee_rom_deg: "Left knee ROM (°)",
  right_knee_rom_deg: "Right knee ROM (°)",
  left_stance_time_s: "Left stance time (s)",
  right_stance_time_s: "Right stance time (s)",
};

export default function AssessmentDetail() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [poseFrames, setPoseFrames] = useState<PoseFrame[] | null>(null);
  const [notes, setNotes] = useState("");
  const [extracting, setExtracting] = useState(false);
  const [running, setRunning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    if (!assessmentId) return;
    api
      .getAssessment(assessmentId)
      .then((a) => {
        setAssessment(a);
        setNotes(a.clinician_notes ?? "");
        if (a.status === "pose_extracted" || a.status === "analyzed" || a.status === "reviewed") {
          poseApi
            .getPoseData(assessmentId)
            .then((d) => setPoseFrames(d.frames))
            .catch(() => setPoseFrames(null));
        }
      })
      .catch((e) => setError(String(e)));
  };

  useEffect(load, [assessmentId]);

  const handleUpload = async (file: File) => {
    if (!assessmentId) return;
    await api.uploadVideo(assessmentId, file);
    load();
  };

  const handleExtractPose = async () => {
    if (!assessmentId) return;
    setExtracting(true);
    setError(null);
    try {
      await poseApi.extractPose(assessmentId);
      load();
    } catch (e) {
      setError(String(e));
    } finally {
      setExtracting(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!assessmentId) return;
    setRunning(true);
    setError(null);
    try {
      await api.runAnalysis(assessmentId);
      load();
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(false);
    }
  };

  const handleSaveNotes = async () => {
    if (!assessmentId) return;
    setSaving(true);
    try {
      await api.updateNotes(assessmentId, notes);
      load();
    } catch (e) {
      setError(String(e));
    } finally {
      setSaving(false);
    }
  };

  if (!assessment) return <p className="text-sm text-slate-500">Loading…</p>;

  return (
    <div className="space-y-8">
      <div>
        <Link to={`/patients/${assessment.patient_id}`} className="text-sm text-slate-500 hover:underline">
          ← Patient
        </Link>
        <h1 className="mt-1 text-2xl font-semibold">Assessment</h1>
        <p className="text-sm capitalize text-slate-500">{assessment.status.replace("_", " ")}</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {!assessment.video_storage_key && <VideoUpload onUpload={handleUpload} />}

      {assessment.video_storage_key && !poseFrames && (
        <div className="space-y-3">
          <video src={mediaUrl(assessment.video_storage_key)} controls className="w-full max-w-xl rounded-lg bg-black" />
          <button
            onClick={handleExtractPose}
            disabled={extracting}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {extracting ? "Extracting pose…" : "Extract pose"}
          </button>
        </div>
      )}

      {assessment.video_storage_key && poseFrames && (
        <div className="space-y-3">
          <PoseOverlayVideo videoUrl={mediaUrl(assessment.video_storage_key)} frames={poseFrames} />
          {assessment.status !== "analyzed" && (
            <button
              onClick={handleRunAnalysis}
              disabled={running}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            >
              {running ? "Analyzing…" : "Run gait analysis"}
            </button>
          )}
        </div>
      )}

      {assessment.results && (
        <div className="space-y-6">
          <div>
            <h2 className="text-sm font-medium text-slate-600">Gait summary</h2>
            <div className="mt-2 grid grid-cols-2 gap-3 sm:grid-cols-3">
              {Object.entries(METRIC_LABELS).map(([key, label]) => {
                const value = (assessment.results!.metrics as any)[key];
                if (value === null || value === undefined) return null;
                return (
                  <div key={key} className="rounded-lg border border-slate-200 bg-white p-3">
                    <p className="text-xs text-slate-500">{label}</p>
                    <p className="text-lg font-semibold">{value}</p>
                  </div>
                );
              })}
            </div>
          </div>

          <div>
            <h2 className="text-sm font-medium text-slate-600">Detected findings</h2>
            <div className="mt-2 space-y-2">
              {assessment.results.findings.map((f) => (
                <FindingCard key={f.finding.id} item={f} />
              ))}
            </div>
          </div>
        </div>
      )}

      <div>
        <h2 className="text-sm font-medium text-slate-600">Clinician notes</h2>
        <textarea
          className="mt-2 w-full rounded-md border border-slate-300 p-3 text-sm"
          rows={4}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
        <button
          onClick={handleSaveNotes}
          disabled={saving}
          className="mt-2 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save assessment"}
        </button>
      </div>

      <p className="border-t border-slate-200 pt-4 text-xs text-slate-400">
        This system provides research/clinical decision-support information and does not independently
        diagnose conditions or prescribe treatment. Findings require assessment and interpretation by an
        appropriately qualified clinician.
      </p>
    </div>
  );
}
