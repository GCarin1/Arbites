import type {
  AiProvidersInfo,
  DailyContext,
  DailyDigestResult,
  Defect,
  DefectsReport,
  EvidenceEntry,
  Meeting,
  MeetingSummaryResult,
  SavedDaily,
  Execution,
  ExecutionSummary,
  FlakyReport,
  GeneratePreview,
  MetricsSummary,
  Requirement,
  ReviewResponse,
  SearchResult,
  TestCase,
  Todo,
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
  moveTestcase: (id: string, folder: string) =>
    request<TestCase>(`/testcases/${id}/move`, {
      method: "POST",
      body: JSON.stringify({ folder }),
    }),
  aiImportFile: async (file: File): Promise<GeneratePreview & { folder: string }> => {
    const form = new FormData();
    form.append("file", file);
    const resp = await fetch(`${BASE}/import/ai`, { method: "POST", body: form });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data?.error?.message ?? `${resp.status}`);
    return data;
  },
  createTcFolder: (path: string) =>
    request<{ path: string }>("/testcases/folders", {
      method: "POST",
      body: JSON.stringify({ path }),
    }),
  deleteTcFolder: (path: string) =>
    request<void>(`/testcases/folders?path=${encodeURIComponent(path)}`, {
      method: "DELETE",
    }),
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

  todos: (query = "") => request<Todo[]>(`/todos${query}`),
  todo: (id: string) => request<Todo>(`/todos/${id}`),
  createTodo: (body: object) =>
    request<Todo>("/todos", { method: "POST", body: JSON.stringify(body) }),
  updateTodo: (id: string, body: object) =>
    request<Todo>(`/todos/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteTodo: (id: string) => request<void>(`/todos/${id}`, { method: "DELETE" }),
  todosExportUrl: (format: "md" | "xml", params: Record<string, string>) => {
    const qs = new URLSearchParams({ format, ...params });
    return `${BASE}/todos/export?${qs.toString()}`;
  },
  search: (q: string, limit = 8, kinds = "") =>
    request<{ results: SearchResult[] }>(
      `/search?q=${encodeURIComponent(q)}&limit=${limit}&kinds=${encodeURIComponent(kinds)}`,
    ),

  metricsSnapshot: () => request<unknown>("/metrics/snapshot", { method: "POST" }),
  dailyContext: (day: string) => request<DailyContext>(`/daily/${day}/context`),
  generateDaily: (day: string, provider?: string | null) =>
    request<DailyDigestResult>(`/daily/${day}/generate`, {
      method: "POST",
      body: JSON.stringify({ provider: provider ?? null }),
    }),
  dailies: () => request<{ dailies: string[] }>("/dailies"),
  getDaily: (day: string) => request<SavedDaily>(`/daily/${day}`),
  putDaily: (day: string, body: object) =>
    request<SavedDaily>(`/daily/${day}`, { method: "PUT", body: JSON.stringify(body) }),

  meetings: (query = "") => request<Meeting[]>(`/meetings${query}`),
  meeting: (id: string) => request<Meeting>(`/meetings/${id}`),
  createMeeting: (body: object) =>
    request<Meeting>("/meetings", { method: "POST", body: JSON.stringify(body) }),
  updateMeeting: (id: string, body: object) =>
    request<Meeting>(`/meetings/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteMeeting: (id: string) => request<void>(`/meetings/${id}`, { method: "DELETE" }),
  summarizeMeeting: (id: string, provider?: string | null) =>
    request<MeetingSummaryResult>(`/meetings/${id}/summarize`, {
      method: "POST",
      body: JSON.stringify({ provider: provider ?? null }),
    }),

  squads: () => request<{ squads: string[] }>("/squads"),
  metricsSummary: (sprint: string, days: number, squad = "") =>
    request<MetricsSummary>(
      `/metrics/summary?sprint=${encodeURIComponent(sprint)}&days=${days}` +
        `&squad=${encodeURIComponent(squad)}`,
    ),
  metricsTrend: (days: number, sprint: string, squad = "") =>
    request<TrendPoint[]>(
      `/metrics/trend?days=${days}&sprint=${encodeURIComponent(sprint)}` +
        `&squad=${encodeURIComponent(squad)}`,
    ),
  metricsFlaky: (window: number) =>
    request<FlakyReport>(`/metrics/flaky?window=${window}`),
  metricsDefects: (squad = "") =>
    request<DefectsReport>(`/metrics/defects?squad=${encodeURIComponent(squad)}`),
  traceability: (epic: string, sprint: string, squad = "") =>
    request<TraceabilityMatrix>(
      `/metrics/traceability?epic=${encodeURIComponent(epic)}` +
        `&sprint=${encodeURIComponent(sprint)}&squad=${encodeURIComponent(squad)}`,
    ),
  exportUrl: (format: "md" | "pdf", sprint: string, squad = "") =>
    `${BASE}/metrics/traceability/export?format=${format}` +
    `&sprint=${encodeURIComponent(sprint)}&squad=${encodeURIComponent(squad)}`,
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
