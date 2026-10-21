const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function fetchVacancy() {
  const res = await fetch(`${API_BASE}/api/vacancy`);
  if (!res.ok) throw new Error("Failed to load vacancy");
  return res.json();
}

export async function fetchCandidates() {
  const res = await fetch(`${API_BASE}/api/candidates`);
  if (!res.ok) throw new Error("Failed to load candidates");
  return res.json();
}

export async function fetchKnowledgeGraph() {
  const res = await fetch(`${API_BASE}/api/knowledge-graph`);
  if (!res.ok) throw new Error("Failed to load knowledge graph");
  return res.json();
}

export async function toggleProxyRule(targetSkill: string, proxySkill: string, isEnabled: boolean) {
  const res = await fetch(`${API_BASE}/api/knowledge-graph/toggle`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ targetSkill, proxySkill, isEnabled }),
  });
  if (!res.ok) throw new Error("Failed to toggle proxy rule");
  return res.json();
}

export async function fetchResumeStatus() {
  const res = await fetch(`${API_BASE}/api/resumes/status`);
  if (!res.ok) throw new Error("Failed to load resume status");
  return res.json();
}

export async function triggerBatchProcess(limit: number | null) {
  const res = await fetch(`${API_BASE}/api/resumes/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ limit, batchSize: 5, asOfDate: "2026-10-21" }),
  });
  if (!res.ok) throw new Error("Failed to trigger batch processing");
  return res.json();
}

export async function fetchValidationReport() {
  const res = await fetch(`${API_BASE}/api/report`);
  if (!res.ok) throw new Error("Failed to load validation report");
  return res.json();
}

export function getExportUrl(format: "jsonl" | "csv") {
  return `${API_BASE}/api/export/${format}`;
}

export async function fetchVacancies() {
  const res = await fetch(`${API_BASE}/api/vacancies`);
  if (!res.ok) throw new Error("Failed to load vacancies list");
  return res.json();
}

export async function selectVacancy(vacancyId: string) {
  const res = await fetch(`${API_BASE}/api/vacancies/select`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ vacancyId }),
  });
  if (!res.ok) throw new Error("Failed to switch vacancy");
  return res.json();
}

export async function createVacancy(payload: {
  title: string;
  experienceMinYears: number;
  experienceMaxYears: number;
  location: string;
  requiredCoreSkills: string[];
  requiredDomainSkills: string[];
  requiredInfraSkills: string[];
  preferredSkills: string[];
  jdText?: string;
}) {
  const res = await fetch(`${API_BASE}/api/vacancies/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to create new vacancy");
  return res.json();
}

export async function deleteVacancy(vacancyId: string) {
  const res = await fetch(`${API_BASE}/api/vacancies/${encodeURIComponent(vacancyId)}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to delete vacancy" }));
    throw new Error(err.detail || "Failed to delete vacancy");
  }
  return res.json();
}


