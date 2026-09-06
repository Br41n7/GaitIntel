import type { Assessment, Patient } from "../types";
import type { PoseFrame } from "../types/pose";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json();
}

export const api = {
  listPatients: () => request<Patient[]>("/api/patients"),

  createPatient: (data: { identifier: string; display_name?: string }) =>
    request<Patient>("/api/patients", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getPatient: (id: string) => request<Patient>(`/api/patients/${id}`),

  listAssessments: (patientId?: string) =>
    request<Assessment[]>(
      patientId ? `/api/assessments?patient_id=${patientId}` : "/api/assessments"
    ),

  createAssessment: (patientId: string) =>
    request<Assessment>("/api/assessments", {
      method: "POST",
      body: JSON.stringify({ patient_id: patientId }),
    }),

  getAssessment: (id: string) => request<Assessment>(`/api/assessments/${id}`),

  uploadVideo: async (assessmentId: string, file: File): Promise<Assessment> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_URL}/api/assessments/${assessmentId}/video`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  },

  runAnalysis: (assessmentId: string) =>
    request<Assessment>(`/api/analysis/${assessmentId}/run`, { method: "POST" }),

  updateNotes: (assessmentId: string, notes: string) =>
    request<Assessment>(`/api/assessments/${assessmentId}/notes`, {
      method: "PATCH",
      body: JSON.stringify({ clinician_notes: notes }),
    }),
};

export const poseApi = {
  extractPose: (assessmentId: string) =>
    request<Assessment>(`/api/pose/${assessmentId}/extract`, { method: "POST" }),

  getPoseData: (assessmentId: string) =>
    request<{ provider_version: string; frame_count: number; frames: PoseFrame[] }>(
      `/api/pose/${assessmentId}`
    ),
};

export function mediaUrl(storageKey: string): string {
  return `${API_URL}/media/${storageKey}`;
}
