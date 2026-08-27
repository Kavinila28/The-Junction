const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `API error ${response.status} on ${path}`);
  }
  return response.json();
}

export function getHealth() {
  return request("/health");
}

export function getMeta() {
  return request("/meta");
}

export function listAnalyses() {
  return request("/analyses");
}

export function getAnalysis(id) {
  return request(`/analyses/${id}`);
}

export function startUpload(file) {
  const body = new FormData();
  body.append("file", file);
  return request("/analyses", { method: "POST", body });
}

export const uploadVideo = startUpload;

export function startDemoAnalysis() {
  return request("/analyses/demo", { method: "POST" });
}

export function getVideoUrl(id) {
  return `${API_BASE}/analyses/${id}/video`;
}

export function simulateInterventions(analysisId, selectedInterventions) {
  return request(`/analyses/${analysisId}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selected_interventions: selectedInterventions }),
  });
}