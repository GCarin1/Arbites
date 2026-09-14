import type {
  ActivityEntry,
  AdminOverview,
  AgentToken,
  ExternalLink,
  LoginAttempt,
  ManagedUser,
  Role,
  SessionInfo,
  SessionUser,
  Switch,
  ActivityHeatmapData,
  AiProvidersInfo,
  ExecutiveSummaryResult,
  AuditHistoryEntry,
  AuditReport,
  AutomationReport,
  CiRun,
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
  TestCaseVersion,
  TimelineEntry,
  Execution,
  ExecutionSummary,
  ExecutionDiff,
  FlakyReport,
  GeneratePreview,
  HealthScore,
  MetricsSummary,
  Observability,
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

// Assinantes avisados quando o backend recusa a sessao: o AuthGate devolve a
// SPA para a tela de login sem depender de cada tela tratar o 401.
const unauthenticatedListeners = new Set<() => void>();

export function onUnauthenticated(listener: () => void): () => void {
  unauthenticatedListeners.add(listener);
  return () => unauthenticatedListeners.delete(listener);
}

/**
 * Mensagem de falha de REDE (change 0134).
 *
 * Quando a requisição não chega a ter resposta, o `fetch` rejeita com a
 * mensagem interna do navegador — "Failed to fetch". Repassada crua, ela
 * aparece em inglês na caixa de erro do login e fica indistinguível de
 * "a senha está errada": a pessoa troca a senha, desconfia da conta, e o
 * problema era o servidor não ter respondido.
 */
const SEM_RESPOSTA =
  "Não foi possível falar com o servidor. Verifique se o Arbites está no ar " +
  "e se este aparelho alcança o endereço dele.";

/** Envolve um `fetch` para separar "não respondeu" de "respondeu e recusou". */
export async function fetchOuAvisar(
  input: RequestInfo,
  init?: RequestInit,
): Promise<Response> {
  try {
    return await fetch(input, init);
  } catch {
    // O navegador não conta o motivo (é de propósito, por privacidade);
    // o que dá para afirmar é que resposta não houve.
    throw new Error(SEM_RESPOSTA);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetchOuAvisar(BASE + path, {
    headers: { "Content-Type": "application/json" },
    // A sessao e um cookie httpOnly: sem isto ele nao acompanha o fetch.
    credentials: "same-origin",
    ...init,
  });
  if (resp.status === 401 && !path.startsWith("/auth/")) {
    for (const listener of unauthenticatedListeners) listener();
  }
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
  // -- sessao (capability auth) --------------------------------------------
  me: () => request<SessionInfo>("/auth/me"),
  login: (email: string, password: string) =>
    request<{ user: SessionUser }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string, name: string) =>
    request<{ user: SessionUser; message: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    }),
  logout: () => request<{ ok: boolean }>("/auth/logout", { method: "POST" }),
  switches: () => request<{ switches: Switch[] }>("/admin/switches"),

  // -- Observabilidade (changes 0153/0154/0155) ----------------------------
  observability: (days: number) =>
    request<Observability>(`/ci/observability?days=${days}`),
  ciRun: (id: string) => request<CiRun>(`/ci/runs/${encodeURIComponent(id)}`),
  ciIngest: () =>
    request<{ ingested: string[]; errors: { code: string; message: string }[];
              stopped?: string }>("/ci/ingest", { method: "POST" }),
  ciAttachmentUrl: (path: string) =>
    `${BASE}/ci/attachment?path=${encodeURIComponent(path)}`,

  // -- MCP (changes 0146/0149) ---------------------------------------------
  agentTokens: () =>
    request<{ tokens: AgentToken[] }>("/profile/agent-tokens"),
  // o token em claro vem UMA vez: quem não guardar, gera outro
  createAgentToken: (name: string) =>
    request<{ token: string; name: string; created_at: string }>(
      "/profile/agent-tokens",
      { method: "POST", body: JSON.stringify({ name }) },
    ),
  revokeAgentToken: (id: string) =>
    request<void>(`/profile/agent-tokens/${id}`, { method: "DELETE" }),
  externalLinks: (params: { system?: string; state?: string } = {}) =>
    request<{ links: ExternalLink[]; count: number }>(
      "/integrations/links?" +
        new URLSearchParams(
          Object.entries(params).filter(([, v]) => v) as [string, string][],
        ),
    ),

  // -- painel de administração (capability admin) --------------------------
  adminUsers: () => request<{ users: ManagedUser[] }>("/admin/users"),
  adminAccessLog: (limit = 100, offset = 0) =>
    request<{ attempts: LoginAttempt[] }>(
      `/admin/access-log?limit=${limit}&offset=${offset}`,
    ),
  adminOverview: () => request<AdminOverview>("/admin/overview"),
  adminActivity: (filters: { user?: string; path?: string } = {}) => {
    const qs = new URLSearchParams({ limit: "200" });
    if (filters.user) qs.set("user", filters.user);
    if (filters.path) qs.set("path", filters.path);
    return request<{ entries: ActivityEntry[] }>(`/admin/activity?${qs}`);
  },
  adminApprove: (id: number, role: Role) =>
    request<{ user: ManagedUser }>(`/admin/users/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ role }),
    }),
  adminReject: (id: number) =>
    request<{ user: ManagedUser }>(`/admin/users/${id}/reject`, { method: "POST" }),
  adminDisable: (id: number) =>
    request<{ user: ManagedUser }>(`/admin/users/${id}/disable`, { method: "POST" }),
  adminEnable: (id: number) =>
    request<{ user: ManagedUser }>(`/admin/users/${id}/enable`, { method: "POST" }),
  adminSetRole: (id: number, role: Role) =>
    request<{ user: ManagedUser }>(`/admin/users/${id}/role`, {
      method: "PUT",
      body: JSON.stringify({ role }),
    }),
  adminResetPassword: (id: number, password: string) =>
    request<{ user: ManagedUser }>(`/admin/users/${id}/password`, {
      method: "POST",
      body: JSON.stringify({ password }),
    }),
  adminRevokeSessions: (id: number) =>
    request<{ revoked: number; user: ManagedUser }>(
      `/admin/users/${id}/sessions`,
      { method: "DELETE" },
    ),
  setSwitch: (name: string, enabled: boolean) =>
    request<{ switch: Switch }>(`/admin/switches/${name}`, {
      method: "PUT",
      body: JSON.stringify({ enabled }),
    }),
  changePassword: (currentPassword: string, newPassword: string) =>
    request<{ user: SessionUser }>("/auth/password", {
      method: "POST",
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    }),

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

  // -- versões do caso de teste (change 0112) ------------------------------
  testcaseVersions: (id: string) =>
    request<{ versions: TestCaseVersion[] }>(`/testcases/${id}/versions`),
  testcaseVersionDiff: (id: string, a: string, b = "") =>
    request<string>(
      `/testcases/${id}/versions/diff?a=${encodeURIComponent(a)}` +
        (b ? `&b=${encodeURIComponent(b)}` : ""),
    ),
  restoreTestcaseVersion: (id: string, sha: string) =>
    request<TestCase>(`/testcases/${id}/versions/${sha}/restore`, { method: "POST" }),
  moveTestcase: (id: string, folder: string) =>
    request<TestCase>(`/testcases/${id}/move`, {
      method: "POST",
      body: JSON.stringify({ folder }),
    }),
  aiImportFile: async (file: File): Promise<GeneratePreview & { folder: string }> => {
    const form = new FormData();
    form.append("file", file);
    const resp = await fetchOuAvisar(`${BASE}/import/ai`, { method: "POST", body: form });
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
  // -- ciclo de teste (change 0111 / ADR 0013) -----------------------------
  patchExecution: (id: string, body: object) =>
    request<Execution>(`/executions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  resultAssignee: (execId: string, ctId: string, assignee: string | null) =>
    request<Execution>(`/executions/${execId}/results/${ctId}/assignee`, {
      method: "POST",
      body: JSON.stringify({ assignee }),
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
    const resp = await fetchOuAvisar(`${BASE}/executions/${execId}/results/${ctId}/evidences`, {
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
  deleteAudit: (id: string) =>
    request<void>(`/audit/${id}`, { method: "DELETE" }),
  // `before` é exclusivo: a rodada exatamente dessa data NÃO é levada
  deleteAuditsBefore: (before: string) =>
    request<{ removed: string[]; count: number }>(
      `/audit?before=${encodeURIComponent(before)}`,
      { method: "DELETE" },
    ),

  profile: () => request<{ name: string; memory: string }>("/profile"),

  // -- avatar da conta (change 0110) ---------------------------------------
  // O GET nao passa por aqui: a imagem e servida direto no `src` da <img>,
  // que ja cai no identicon quando o backend responde 404.
  putAvatar: async (file: File): Promise<{ ok: boolean; format: string }> => {
    const form = new FormData();
    form.append("file", file);
    const resp = await fetchOuAvisar(`${BASE}/profile/avatar`, {
      method: "PUT",
      credentials: "same-origin",
      body: form,
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data?.error?.message ?? `${resp.status}`);
    return data;
  },
  deleteAvatar: () => request<void>("/profile/avatar", { method: "DELETE" }),

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
  exportUrl: (format: "md" | "pdf", sprint: string, squad = "", summary = "") =>
    `${BASE}/metrics/traceability/export?format=${format}` +
    `&sprint=${encodeURIComponent(sprint)}&squad=${encodeURIComponent(squad)}` +
    (summary ? `&summary=${encodeURIComponent(summary)}` : ""),
  executiveSummary: (sprint: string, squad = "", provider?: string | null) =>
    request<ExecutiveSummaryResult>("/ai/executive-summary", {
      method: "POST",
      body: JSON.stringify({ sprint: sprint || null, squad: squad || null, provider: provider ?? null }),
    }),
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
