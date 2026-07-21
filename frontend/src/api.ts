import type {
  ActivityHeatmapData,
  AiProvidersInfo,
  AuditHistoryEntry,
  AuditReport,
  AutomationReport,
  DailyContext,
  DailyDigestResult,
  DashboardOverview,
  Decision,
  Defect,
  DefectsReport,
  EvidenceEntry,
  Meeting,
  MeetingSummaryResult,
  MeetingActionItems,
  RiskMap,
  SavedDaily,
  TestCaseResult,
  TimelineEntry,
  Execution,
  ExecutionSummary,
  ExecutionDiff,
  FlakyReport,
  GeneratePreview,
  HealthScore,
  MetricsSummary,
  Criterion,
  Requirement,
  StoryChain,
  ReviewResponse,
  SearchResult,
  TestCase,
  Todo,
  TraceabilityMatrix,
  TreeNode,
  TrendPoint,
  TrashItem,
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
  trash: () => request<TrashItem[]>("/trash"),
  restoreTrash: (name: string) =>
    request<{ restored: string }>(`/trash/${encodeURIComponent(name)}/restore`, {
      method: "POST",
    }),
  emptyTrash: () => request<{ removed: number }>("/trash", { method: "DELETE" }),
  tree: () => request<TreeNode>("/tree"),

  requirements: (params = "") => request<Requirement[]>(`/requirements${params}`),
  requirement: (id: string) => request<Requirement>(`/requirements/${id}`),
  requirementChain: (id: string) =>
    request<StoryChain>(`/requirements/${id}/chain`),
  requirementCriteria: (id: string) =>
    request<Criterion[]>(`/requirements/${id}/criteria`),
  createRequirement: (body: object) =>
    request<Requirement>("/requirements", { method: "POST", body: JSON.stringify(body) }),
  updateRequirement: (id: string, body: object) =>
    request<Requirement>(`/requirements/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteRequirement: (id: string) =>
    request<void>(`/requirements/${id}`, { method: "DELETE" }),

  testcases: (params = "") => request<TestCase[]>(`/testcases${params}`),
  testcase: (id: string) => request<TestCase>(`/testcases/${id}`),
  testcaseResults: (id: string) =>
    request<TestCaseResult[]>(`/testcases/${id}/results`),
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
  moveTcFolder: (path: string, dest: string) =>
    request<{ path: string }>("/testcases/folders/move", {
      method: "POST",
      body: JSON.stringify({ path, dest }),
    }),
  putTestcaseRaw: (id: string, content: string) =>
    request<TestCase>(`/testcases/${id}/raw`, {
      method: "PUT",
      body: JSON.stringify({ content }),
    }),

  executions: (query = "") => request<ExecutionSummary[]>(`/executions${query}`),
  deleteExecution: (id: string) =>
    request<void>(`/executions/${id}`, { method: "DELETE" }),
  runsActive: () =>
    request<{ count: number; runs: { exec_id: string; target: string; status: string }[] }>(
      "/runs/active",
    ),
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
  linkDefect: (execId: string, ctId: string, defectId: string) =>
    request<Execution>(`/executions/${execId}/results/${ctId}/defects`, {
      method: "POST",
      body: JSON.stringify({ defect_id: defectId }),
    }),
  unlinkDefect: (execId: string, ctId: string, defectId: string) =>
    request<Execution>(`/executions/${execId}/results/${ctId}/defects/${defectId}`, {
      method: "DELETE",
    }),
  closeExecution: (id: string) =>
    request<Execution>(`/executions/${id}/close`, { method: "POST" }),
  executionsDiff: (a: string, b: string) =>
    request<ExecutionDiff>(
      `/executions/diff?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`,
    ),

  defects: (query = "") => request<Defect[]>(`/defects${query}`),
  defect: (id: string) => request<Defect>(`/defects/${id}`),
  createDefect: (body: object) =>
    request<Defect>("/defects", { method: "POST", body: JSON.stringify(body) }),
  updateDefect: (id: string, body: object) =>
    request<Defect>(`/defects/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteDefect: (id: string) => request<void>(`/defects/${id}`, { method: "DELETE" }),

  decisions: (query = "") => request<Decision[]>(`/decisions${query}`),
  decision: (id: string) => request<Decision>(`/decisions/${id}`),
  createDecision: (body: object) =>
    request<Decision>("/decisions", { method: "POST", body: JSON.stringify(body) }),
  updateDecision: (id: string, body: object) =>
    request<Decision>(`/decisions/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteDecision: (id: string) => request<void>(`/decisions/${id}`, { method: "DELETE" }),

  runAudit: () => request<AuditReport>("/audit/run", { method: "POST" }),
  auditLatest: () => request<AuditReport>("/audit/latest"),
  auditHistory: (limit = 20) =>
    request<AuditHistoryEntry[]>(`/audit/history?limit=${limit}`),
  audit: (id: string) => request<AuditReport>(`/audit/${id}`),

  profile: () => request<{ name: string; memory: string }>("/profile"),

  memoryTimeline: (kinds = "", limit = 50, dateFrom = "", dateTo = "") => {
    const qs = new URLSearchParams({ kinds, limit: String(limit) });
    if (dateFrom) qs.set("date_from", dateFrom);
    if (dateTo) qs.set("date_to", dateTo);
    return request<TimelineEntry[]>(`/memory/timeline?${qs.toString()}`);
  },
  memoryTimelineYears: (kinds = "") =>
    request<string[]>(
      `/memory/timeline/years?kinds=${encodeURIComponent(kinds)}`,
    ),

  contextPackUrl: (params: Record<string, string>) => {
    const qs = new URLSearchParams(params);
    return `${BASE}/context-pack?${qs.toString()}`;
  },
  agentPackUrl: (params: Record<string, string>) => {
    const qs = new URLSearchParams(params);
    return `${BASE}/agent-pack?${qs.toString()}`;
  },
  contextPack: (params: Record<string, string>) => {
    const qs = new URLSearchParams({ ...params, format: "json" });
    return request<{
      scope: Record<string, string>;
      counts: { requirements: number; testcases: number; defects: number; decisions: number };
      bytes: number;
      markdown: string;
    }>(`/context-pack?${qs.toString()}`);
  },

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
  meetingActionItems: (id: string) =>
    request<MeetingActionItems>(`/meetings/${id}/action-items`),
  generateMeetingActionItems: (id: string, provider?: string | null) =>
    request<{ preview: boolean; id: string; action_items: string[] }>(
      `/meetings/${id}/action-items/generate`,
      { method: "POST", body: JSON.stringify({ provider: provider ?? null }) },
    ),
  acceptMeetingActionItems: (id: string, items: string[]) =>
    request<{ created: string[]; converted: { id: string; title: string; status: string }[] }>(
      `/meetings/${id}/action-items/accept`,
      { method: "POST", body: JSON.stringify({ items }) },
    ),

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
  metricsAutomation: (days = 0, env = "") =>
    request<AutomationReport>(
      `/metrics/automation?days=${days}&env=${encodeURIComponent(env)}`,
    ),
  metricsActivity: (days = 371, year = 0) =>
    request<ActivityHeatmapData>(`/metrics/activity?days=${days}&year=${year}`),
  metricsHealth: (sprint = "", days = 0, squad = "") =>
    request<HealthScore>(
      `/metrics/health?sprint=${encodeURIComponent(sprint)}&days=${days}` +
        `&squad=${encodeURIComponent(squad)}`,
    ),
  metricsDashboard: (sprint = "", days = 30, squad = "") =>
    request<DashboardOverview>(
      `/metrics/dashboard?sprint=${encodeURIComponent(sprint)}&days=${days}` +
        `&squad=${encodeURIComponent(squad)}`,
    ),
  riskMap: (days = 90) => request<RiskMap>(`/risk-map?days=${days}`),
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
  aiGenerate: (body: {
    source: string;
    provider?: string | null;
    criteria?: string[];
  }) =>
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
  aiProviderTest: (body: {
    name?: string;
    kind?: string;
    model?: string;
    base_url?: string | null;
    key?: string;
  }) =>
    request<{ ok: boolean; error: string | null }>("/ai/providers/test", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  aiAnalyzeRun: (execId: string, body: { provider?: string | null } = {}) =>
    request<{
      preview: boolean;
      summary: string;
      probable_cause: string;
      defect: { title: string; severity: string; description: string; testcase: string; execution: string };
    }>(`/ai/analyze-run/${execId}`, { method: "POST", body: JSON.stringify(body) }),
  aiStructureLesson: (defectId: string, body: { provider?: string | null } = {}) =>
    request<{
      preview: boolean;
      lesson_when: string;
      lesson_procedure: string;
      lesson_antipattern: string;
    }>(`/ai/structure-lesson/${defectId}`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
