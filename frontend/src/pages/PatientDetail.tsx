import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../lib/api";
import type { Assessment, Patient } from "../types";

export default function PatientDetail() {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!patientId) return;
    api.getPatient(patientId).then(setPatient).catch((e) => setError(String(e)));
    api.listAssessments(patientId).then(setAssessments).catch((e) => setError(String(e)));
  }, [patientId]);

  const handleNewAssessment = async () => {
    if (!patientId) return;
    setCreating(true);
    try {
      const assessment = await api.createAssessment(patientId);
      navigate(`/assessments/${assessment.id}`);
    } catch (e) {
      setError(String(e));
    } finally {
      setCreating(false);
    }
  };

  if (!patient) return <p className="text-sm text-slate-500">Loading…</p>;

  return (
    <div className="space-y-6">
      <div>
        <Link to="/patients" className="text-sm text-slate-500 hover:underline">
          ← Patients
        </Link>
        <h1 className="mt-1 text-2xl font-semibold">{patient.identifier}</h1>
        {patient.display_name && <p className="text-sm text-slate-500">{patient.display_name}</p>}
      </div>

      <button
        onClick={handleNewAssessment}
        disabled={creating}
        className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
      >
        {creating ? "Creating…" : "New assessment"}
      </button>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div>
        <h2 className="text-sm font-medium text-slate-600">Assessments</h2>
        {assessments.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">No assessments yet.</p>
        ) : (
          <ul className="mt-2 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
            {assessments.map((a) => (
              <li key={a.id} className="px-4 py-3 hover:bg-slate-50">
                <Link to={`/assessments/${a.id}`} className="flex justify-between text-sm">
                  <span>{new Date(a.created_at).toLocaleString()}</span>
                  <span className="capitalize text-slate-500">{a.status.replace("_", " ")}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
