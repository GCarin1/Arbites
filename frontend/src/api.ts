import type {
  AiProvidersInfo,
  Defect,
  EvidenceEntry,
  Execution,
  ExecutionSummary,
  FlakyReport,
  GeneratePreview,
  MetricsSummary,
  Requirement,
  ReviewResponse,
  TestCase,
  TraceabilityMatrix,
  TreeNode,
  TrendPoint,
  Warning,
  WorkspaceInfo,
} from "./types";

const BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) {
    let message = `${resp.status} ${resp.statusText}`;
    try {
      const data = await resp.json();
      if (data?.error?.message) message = data.error.message;
    } catch {
      /* corpo não-JSON */
    }
    throw new Error(message);
  }
  if (resp.status === 204) return undefined as T;
  const text = await resp.text();
  try {
    return JSON.parse(text) as T;
  } catch {
    return text as T;
  }
}

export const api = {
  workspace: () => request<WorkspaceInfo>("/workspace"),
  reindex: () => request<unknown>("/workspace/reindex", { method: "POST" }),
  warnings: () => request<Warning[]>("/warnings"),
  tree: () => request<TreeNode>("/tree"),

  requirements: (params = "") => request<Requirement[]>(`/requirements${params}`),
  requirement: (id: string) => request<Requirement>(`/requirements/${id}`),
  createRequirement: (body: object) =>
    request<Requirement>("/requirements", { method: "POST", body: JSON.stringify(body) }),
  updateRequirement: (id: string, body: object) =>
    request<Requirement>(`/requirements/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteRequirement: (id: string) =>
    request<void>(`/requirements/${id}`, { method: "DELETE" }),

  testcases: (params = "") => request<TestCase[]>(`/testcases${params}`),
  testcase: (id: string) => request<TestCase>(`/testcases/${id}`),
  createTestcase: (body: object) =>
    request<TestCase>("/testcases", { method: "POST", body: JSON.stringify(body) }),
  updateTestcase: (id: string, body: object) =>
    request<TestCase>(`/testcases/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteTestcase: (id: string) =>
    request<void>(`/testcases/${id}`, { method: "DELETE" }),
  testcaseRaw: (id: string) => request<string>(`/testcases/${id}/raw`),
  putTestcaseRaw: (id: string, content: string) =>
    request<TestCase>(`/testcases/${id}/raw`, {
      method: "PUT",
      body: JSON.stringify({ content }),
    }),

  executions: () => request<ExecutionSummary[]>("/executions"),
  execution: (id: string) => request<Execution>(`/executions/${id}`),
  createExecution: (body: object) =>
    request<Execution>("/executions", { method: "POST", body: JSON.stringify(body) }),
  resultStatus: (execId: string, ctId: string, body: object) =>
    request<Execution>(`/executions/${execId}/results/${ctId}/status`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  stepStatus: (execId: string, ctId: string, step: number, status: string) =>
    request<Execution>(`/executions/${execId}/results/${ctId}/steps/${step}`, {
      method: "POST",
      body: JSON.stringify({ status }),
    }),
  uploadEvidence: async (
    execId: string,
    ctId: string,
    file: File,
    note: string,
  ): Promise<EvidenceEntry> => {
    const form = new FormData();
    form.append("file", file);
    if (note) form.append("note", note);
    const resp = await fetch(`${BASE}/executions/${execId}/results/${ctId}/evidences`, {
      method: "POST",
      body: form, // sem Content-Type manual: o browser define o boundary
    });
    if (!resp.ok) {
      const data = await resp.json().catch(() => null);
      throw new Error(data?.error?.message ?? `${resp.status} ${resp.statusText}`);
    }
    return resp.json();
  },
  deleteEvidence: (execId: string, ctId: string, index: number) =>
    request<Execution>(`/executions/${execId}/results/${ctId}/evidences/${index}`, {
      method: "DELETE",
    }),
  closeExecution: (id: string) =>
    request<Execution>(`/executions/${id}/close`, { method: "POST" }),

  defects: () => request<Defect[]>("/defects"),
  createDefect: (body: object) =>
    request<Defect>("/defects", { method: "POST", body: JSON.stringify(body) }),

  metricsSummary: (sprint: string, days: number) =>
    request<MetricsSummary>(
      `/metrics/summary?sprint=${encodeURIComponent(sprint)}&days=${days}`,
    ),
  metricsTrend: (days: number, sprint: string) =>
    request<TrendPoint[]>(
      `/metrics/trend?days=${days}&sprint=${encodeURIComponent(sprint)}`,
    ),
  metricsFlaky: (window: number) =>
    request<FlakyReport>(`/metrics/flaky?window=${window}`),
  traceability: (epic: string, sprint: string) =>
    request<TraceabilityMatrix>(
      `/metrics/traceability?epic=${encodeURIComponent(epic)}&sprint=${encodeURIComponent(sprint)}`,
    ),
  exportUrl: (format: "md" | "pdf", sprint: string) =>
    `${BASE}/metrics/traceability/export?format=${format}&sprint=${encodeURIComponent(sprint)}`,
  evidenceFileUrl: (execId: string, ctId: string, index: number) =>
    `${BASE}/executions/${execId}/results/${ctId}/evidences/${index}/file`,

  aiProviders: () => request<AiProvidersInfo>("/ai/providers"),
  putAiProviders: (body: object) =>
    request<AiProvidersInfo>("/ai/providers", {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  aiGenerate: (body: { source: string; provider?: string | null }) =>
    request<GeneratePreview>("/ai/generate-testcases", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  aiReview: (ctId: string, body: { provider?: string | null }) =>
    request<ReviewResponse>(`/ai/review/${ctId}`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  aiNegativeCases: (ctId: string, body: { provider?: string | null }) =>
    request<GeneratePreview>(`/ai/negative-cases/${ctId}`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
