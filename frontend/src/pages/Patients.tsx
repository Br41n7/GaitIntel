import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { Patient } from "../types";

export default function Patients() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [identifier, setIdentifier] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api
      .listPatients()
      .then(setPatients)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim()) return;
    setError(null);
    try {
      await api.createPatient({ identifier, display_name: displayName || undefined });
      setIdentifier("");
      setDisplayName("");
      load();
    } catch (e) {
      setError(String(e));
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Patients</h1>
        <p className="mt-1 text-sm text-slate-500">
          Use a clinic-assigned identifier, not a full name, where possible.
        </p>
      </div>

      <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <div>
          <label className="block text-xs font-medium text-slate-600">Identifier</label>
          <input
            className="mt-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="e.g. PT-0042"
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600">Display name (optional)</label>
          <input
            className="mt-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
        </div>
        <button
          type="submit"
          className="rounded-md bg-slate-900 px-4 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
        >
          Add patient
        </button>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : patients.length === 0 ? (
        <p className="text-sm text-slate-500">No patients yet. Add one above.</p>
      ) : (
        <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {patients.map((p) => (
            <li key={p.id} className="px-4 py-3 hover:bg-slate-50">
              <Link to={`/patients/${p.id}`} className="flex justify-between text-sm">
                <span className="font-medium">{p.identifier}</span>
                <span className="text-slate-500">{p.display_name ?? "—"}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
