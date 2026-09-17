// -- sessao (capability auth) ------------------------------------------------

export type Role = "admin" | "editor" | "viewer";
export type UserStatus = "pending" | "active" | "disabled" | "rejected";

export interface SessionUser {
  id: number;
  email: string;
  name: string;
  role: Role;
  status: UserStatus;
  must_change_password: boolean;
  created_at: string | null;
  last_login_at: string | null;
}

export interface Switch {
  name: string;
  label: string;
  /** "surface" governa uma CAPACIDADE técnica; "module", uma TELA (ADR 0014). */
  kind: "surface" | "module";
  /** Aba que o módulo possui — só em `kind: "module"`. */
  tab: string | null;
  enabled: boolean;
  updated_at: string | null;
  updated_by: string | null;
}

/** Credencial do agente MCP (change 0146) — separada da sessão do navegador. */
export interface AgentToken {
  id: string;
  name: string;
  created_at: string;
  last_used_at: string | null;
}

/** Vínculo com um sistema externo (change 0145). */
export interface ExternalLink {
  kind: string;
  entity_id: string;
  title: string;
  system: string | null;
  remote_id: string | null;
  revision: string | null;
  synced_at: string | null;
  state: "never_synced" | "in_sync" | "local_changed" | "remote_changed" | "conflict";
}

export interface ManagedUser extends SessionUser {
  open_sessions: number;
}

export interface LoginAttempt {
  email: string;
  ip: string;
  user_agent: string;
  ok: boolean;
  at: string;
}

export interface ActivityEntry {
  at: string;
  user_email: string;
  method: string;
  path: string;
  status_code: number;
  ip: string;
}

export interface AdminOverview {
  version: string;
  users: Record<UserStatus, number>;
  index: { last_reindex: string | null; last_reindex_seconds: string | null };
  trash_items: number;
  switches: Switch[];
}

export interface SessionInfo {
  user: SessionUser | null;
  auth_enabled: boolean;
  signup_enabled?: boolean;
  /** Nenhum admin ativo: um cadastro feito agora ficaria pendente sem quem aprove. */
  no_admin?: boolean;
  /** Há ARBITES_ADMIN_EMAIL declarado, então cadastrar-se com ele já vira admin. */
  owner_declared?: boolean;
}

export interface WorkspaceInfo {
  config: {
    workspace?: { name?: string; id_prefixes?: Record<string, string> };
  };
  root: string;
  index: {
    last_reindex: string | null;
    last_reindex_seconds: string | null;
    requirements: number;
    testcases: number;
    warnings: number;
  };
}

export interface Requirement {
  id: string;
  kind: "epic" | "story";
  title: string;
  epic_id: string | null;
  status: string;
  external_key: string | null;
  confluence_url: string | null;
  tags: string[];
  squad: string | null;
  created?: string | null;
  path: string;
  body?: string;
  /** Onde este requisito vive, se não for aqui (change 0158, ADR 0015). */
  external?: { system: string; id: string; revision?: string | null }[];
  owned_elsewhere?: boolean;
}

export interface ChainTestcase {
  id: string;
  title: string;
  type: string;
  status: string;
  last_result: { status: string; executed_at: string | null } | null;
  evidence_count: number;
  executions: {
    execution_id: string;
    execution_name: string;
    status: string;
    executed_at: string | null;
  }[];
}

export interface StoryChain {
  story: { id: string; title: string; status: string; epic_id: string | null; squad: string | null };
  epic: { id: string; title: string; status: string } | null;
  testcases: ChainTestcase[];
  executions: { id: string; name: string; status: string; created_at: string | null }[];
  defects: {
    id: string;
    title: string;
    status: string;
    severity: string | null;
    testcase_id: string | null;
    execution_id: string | null;
  }[];
  summary: {
    testcases: number;
    passing: number;
    failing: number;
    untested: number;
    executions: number;
    defects: number;
    evidences: number;
  };
}

export interface Criterion {
  ears_id: string;
  ord: number;
  text: string;
  form: string | null; // ubiquitous|event|state|unwanted|optional | null (fora de EARS)
  // Cobertura POR CRITÉRIO (change 0158): "a story tem 4 CTs" não responde
  // "este critério foi verificado?" — quatro casos podem cobrir o mesmo.
  covered_by?: { id: string; title: string; last_status: string | null }[];
  coverage?: "uncovered" | "untested" | "failing" | "passing";
}

export interface TestCase {
  id: string;
  title: string;
  type: "manual" | "automated" | "hybrid";
  priority: string;
  status: string;
  story_id: string | null;
  path: string;
  automation_target: string | null;
  scenario_tag: string | null;
  squad: string | null;
  squad_effective: string | null;
  quarantine?: boolean; // fora do pass rate quando true (0089)
  needs_rerun?: boolean; // re-base de steps pendente de re-execução (0090)
  tags?: string[];
  criteria?: string[]; // EARS ids da story que este CT cobre (0092)
  body?: string;
}

export interface TestCaseResult {
  execution_id: string;
  execution_name: string;
  status: string;
  executed_at: string | null;
  duration_seconds: number | null;
}

export interface TodoLink {
  id: string;
  kind: string | null;
  title: string | null;
}

export interface SearchResult {
  id: string;
  title: string | null;
  kind: string;
}

export interface Todo {
  id: string;
  title: string;
  status: "open" | "doing" | "blocked" | "done";
  due: string | null;
  squad: string | null;
  links: TodoLink[];
  created: string | null;
  path: string;
  body?: string;
  /** De que linha de lista este afazer participa (change 0164). É CONSULTA:
   *  o vínculo mora na linha, e guardá-lo aqui também abriria a chance de os
   *  dois se contradizerem. */
  list_item?: {
    list_id: string;
    item_id: string;
    text: string;
    done: boolean;
    list_title: string;
    list_due: string | null;
  } | null;
}

export interface DailyMetricDiff {
  metric: string;
  label: string;
  today: number | null;
  previous: number | null;
  delta: number | null;
}

export interface DailyContext {
  date: string;
  todos: {
    blocked: { id: string; title: string }[];
    in_progress: { id: string; title: string; due: string | null }[];
    done_count: number;
  };
  activity: {
    executions: { execution_id: string; name: string; passed: number; failed: number; blocked: number }[];
    defects_opened: { id: string; title: string; severity: string | null }[];
  };
  metrics_diff: {
    previous_date: string;
    has_today: boolean;
    has_previous: boolean;
    metrics: DailyMetricDiff[];
  };
  markdown: string;
}

export interface DailyDigestResult {
  preview: boolean;
  date: string;
  summary: string;
  impediments: string[];
  progress: string;
  action_items: string[];
  context_markdown: string;
}

export interface SavedDaily {
  date: string;
  action_items: string[];
  body: string;
}

export interface Meeting {
  id: string;
  title: string;
  date: string | null;
  summary: string | null;
  path: string;
  body?: string;
}

export interface MeetingSummaryResult {
  preview: boolean;
  id: string;
  summary: string;
  decisions: string[];
  action_items: string[];
}

export interface MeetingActionItems {
  id: string;
  deterministic: string[];
  converted: { id: string; title: string; status: string }[];
}

export interface ExecutiveSummaryResult {
  preview: boolean;
  synthesis: string;
  risks: string[];
  recommendation: string;
  context_markdown: string;
}

export interface TreeNode {
  name: string;
  path: string;
  dirs: TreeNode[];
  files: {
    path: string;
    id: string | null;
    title: string;
    type: string | null;
    status: string | null;
    created: string | null;
  }[];
}

export interface Warning {
  source_path: string;
  code: string;
  message: string;
  created_at: string;
}

export interface TrashItem {
  name: string;
  origin: string | null;
  trashed_at: string | null;
  kind: string;
  is_dir: boolean;
}

export interface StepEntry {
  index: number;
  text: string;
  status: "pending" | "passed" | "failed" | "blocked";
}

export interface EvidenceEntry {
  path: string;
  sha256: string;
  mime: string;
  captured_at: string;
  note: string | null;
}

/** Uma versão do arquivo do caso de teste no git do workspace (change 0112). */
export interface TestCaseVersion {
  sha: string;
  short: string;
  author: string;
  email: string;
  at: string;
  message: string;
}

export interface ResultEntry {
  testcase_id: string;
  status: string;
  column: string;
  // Responsável por ESTE caso dentro do ciclo (ADR 0013): é o que divide uma
  // regressão entre duas ou mais pessoas sem duplicar a execution.
  assignee?: string | null;
  executed_by: string | null;
  executed_at: string | null;
  duration_seconds: number | null;
  steps: StepEntry[];
  evidences: EvidenceEntry[];
  defects: string[];
  comment: string | null;
  error: string | null;
}

export interface Execution {
  schema_version: number;
  id: string;
  name: string;
  owner: string;
  sprint: string | null;
  environment: string | null;
  origin: string;
  squad: string | null;
  created_at: string;
  // Período do ciclo (ADR 0013) — ausente nos execution.json anteriores.
  starts_on?: string | null;
  ends_on?: string | null;
  closed_at: string | null;
  status: "draft" | "in_progress" | "closed";
  results: ResultEntry[];
  progress?: {
    counts: Record<string, number>;
    total: number;
    done: number;
    percent: number;
  };
  history: { at: string; who: string; event: string; [k: string]: unknown }[];
}

export interface ExecutionSummary {
  id: string;
  name: string;
  owner: string;
  sprint: string | null;
  environment: string | null;
  origin: string;
  status: string;
  // Período do ciclo (ADR 0013) — ausente nos execution.json anteriores.
  starts_on?: string | null;
  ends_on?: string | null;
  created_at: string;
  closed_at: string | null;
  path: string;
  result_counts: Record<string, number>;
}

export interface ExecutionDiffEntry {
  testcase_id: string;
  title: string | null;
  status_a: string | null;
  status_b: string | null;
}

export type ExecutionDiffCategory =
  | "regressed"
  | "fixed"
  | "added"
  | "removed"
  | "unchanged";

export interface ExecutionDiff {
  a: string;
  b: string;
  categories: Record<ExecutionDiffCategory, ExecutionDiffEntry[]>;
  counts: Record<ExecutionDiffCategory, number>;
}

export interface Defect {
  id: string;
  title: string;
  status: string;
  severity: string | null;
  testcase_id: string | null;
  execution_id: string | null;
  external_key: string | null;
  path: string;
  opened_at: string | null;
  root_cause: string | null;
  fix: string | null;
  prevention: string | null;
  lesson_when?: string | null; // lição estruturada (0095)
  lesson_procedure?: string | null;
  lesson_antipattern?: string | null;
  body?: string;
}

export interface Decision {
  id: string;
  title: string;
  status: "proposed" | "accepted" | "superseded";
  squad: string | null;
  tags: string[];
  supersedes: string | null;
  path: string;
  created: string | null;
  mtime: number;
  body?: string;
}

export interface MetricValue {
  formula: string;
  numerator: number;
  denominator: number;
  value: number | null;
  status?: "ok" | "warn" | "bad" | "none";
  threshold?: { warn?: number; bad?: number; direction?: string } | null;
}

export interface QuarantineSummary {
  count: number;
  testcases: { testcase_id: string; title: string | null }[];
}

export interface MetricsSummary {
  requirement_coverage: MetricValue;
  execution_coverage: MetricValue;
  pass_rate: MetricValue;
  blocked_rate: MetricValue;
  rework_rate: MetricValue;
  quarantine?: QuarantineSummary;
}

export interface TrendPoint {
  day: string;
  passed: number;
  failed: number;
  blocked: number;
}

export interface FlakyReport {
  formula: string;
  window: number;
  testcases: { testcase_id: string; sequence: string[] }[];
}

export interface DefectItem {
  id: string;
  title: string;
  severity: string | null;
  testcase_id: string | null;
  execution_id: string | null;
  external_key: string | null;
  opened_at: string | null;
  squad: string;
  age_days: number | null;
}

export interface DefectsReport {
  squad_filter: string | null;
  open_count: number;
  by_severity: Record<string, number>;
  by_squad: Record<string, number>;
  aging_buckets: Record<string, number>;
  items: DefectItem[];
}

export interface AutomationRepoRow {
  repo: string;
  runs: number;
  passed: number;
  failed: number;
  other: number;
  pass_rate: number | null;
  failure_rate: number | null;
  envs: string[];
  last_run_at: string | null;
  last_outcome: string | null;
  recent: { at: string; outcome: string }[];
  mttr_hours: number | null;
  broken_since: string | null;
  flaky: number;
}

export interface AutomationFailingCt {
  testcase_id: string;
  title: string | null;
  failed: number;
  runs: number;
  failure_rate: number | null;
  repos: string[];
}

export interface AutomationReport {
  total_runs: number;
  passed_runs: number;
  failed_runs: number;
  pass_rate: number | null;
  by_repo: AutomationRepoRow[];
  by_env: { env: string; runs: number; failed: number; failure_rate: number | null }[];
  envs: string[];
  env_filter: string | null;
  top_failing_testcases: AutomationFailingCt[];
  flaky_testcases: { testcase_id: string; title: string | null; repos: string[] }[];
  unparsed: number;
  pattern: string;
  pattern_error: string | null;
}

export interface AuditFinding {
  category: "indexing" | "coverage" | "defects" | "automation" | string;
  code: string;
  severity: "bad" | "warn" | "info";
  message: string;
  ref: string | null;
}

export interface AuditReport {
  id: string;
  ran_at: string;
  trigger: "manual" | "auto";
  total: number;
  by_severity: Record<string, number>;
  by_category: Record<string, number>;
  findings: AuditFinding[];
}

export interface AuditHistoryEntry {
  id: string;
  ran_at: string;
  trigger: "manual" | "auto";
  total: number;
  by_severity: Record<string, number>;
  by_category: Record<string, number>;
}

export interface TimelineEntry {
  at: string;
  kind: "requirement" | "defect" | "lesson" | "decision" | "agent";
  id: string;
  title: string;
  summary: string;
}

export interface DashboardAlert {
  severity: "bad" | "warn" | "info";
  category: string;
  message: string;
  ref: string | null;
}

export interface DashboardOverview {
  last_reindex: string | null;
  pass_rate_trend: {
    days: number;
    current: number | null;
    previous: number | null;
    delta: number | null;
  };
  alerts: DashboardAlert[];
  top_problems: {
    worst_repos: {
      repo: string;
      failed: number;
      runs: number;
      failure_rate: number | null;
      broken_since: string | null;
    }[];
    top_failing_testcases: AutomationFailingCt[];
    oldest_defects: {
      id: string;
      title: string;
      severity: string | null;
      age_days: number;
    }[];
  };
  recommended_actions: { message: string; ref: string | null; category: string }[];
}

export interface HealthComponent {
  value: number | null;
  weight: number;
  formula: string;
}

export interface HealthScore {
  score: number | null;
  components: {
    coverage: HealthComponent;
    defects: HealthComponent;
    automation: HealthComponent;
    debt: HealthComponent;
  };
}

export interface RiskMapFile {
  path: string;
  churn: number;
  defect_commits: number;
}

export interface RiskMapRepo {
  repo: string;
  error: string | null;
  total_commits: number;
  files: RiskMapFile[];
  automation_pass_rate: number | null;
}

export interface RiskMap {
  since_days: number;
  repos: RiskMapRepo[];
}

export interface ActivityDay {
  date: string;
  executions: number;
  defects: number;
  testcases: number;
  requirements: number;
  auto_runs: number;
  total: number;
}

export interface ActivityHeatmapData {
  from: string;
  to: string;
  days: ActivityDay[];
  totals: {
    executions: number;
    defects: number;
    testcases: number;
    requirements: number;
    auto_runs: number;
    total: number;
  };
  years: number[];
  year_filter: number | null;
}

export interface MatrixLastResult {
  status: string;
  execution_id: string;
  executed_at: string | null;
}

export interface MatrixTestcase {
  id: string;
  title: string;
  status: string;
  last_result: MatrixLastResult | null;
}

export interface MatrixStory {
  id: string;
  title: string;
  status: string;
  ct_count: number;
  covered: boolean;
  coverage_state: "uncovered" | "untested" | "passing" | "failing";
  criteria_total: number;
  criteria_covered: number;
  last_status: string | null;
  last_execution: string | null;
  evidence_count: number;
  defects: { id: string; title: string; status: string }[];
  testcases: MatrixTestcase[];
}

export interface MatrixEpic {
  id: string;
  title: string;
  status: string;
  stories: MatrixStory[];
}

export interface TraceabilityMatrix {
  epic_filter: string | null;
  sprint_filter: string | null;
  epics: MatrixEpic[];
  /** Stories sem epic. Sem elas a tela dizia "sem cobertura" para story
   *  coberta — cobertura falsa é pior que ausente (change 0158). */
  orphan_stories?: MatrixStory[];
}

// ------------------------------------------------------------------ IA (M5)

export interface AiProvider {
  name: string;
  kind: string;
  model: string;
  base_url: string | null;
  key_configured: boolean;
}

export interface AiProvidersInfo {
  default_provider: string | null;
  providers: AiProvider[];
}

export interface GeneratedTestcase {
  title: string;
  type: string;
  priority: string;
  tags: string[];
  objetivo: string;
  pre_condicoes: string[];
  passos: string[];
  resultado_esperado: string;
  body: string;
  criteria?: string[]; // vínculo EARS quando gerado por critério (0093)
}

export interface GeneratePreview {
  preview: boolean;
  story?: string; // story de origem quando gerado por critério (0093)
  testcases: GeneratedTestcase[];
  lessons_used?: { id: string; title: string }[];
}

export interface ReviewIssue {
  kind: string;
  message: string;
  step_index: number | null;
}

export interface ReviewResponse {
  preview: boolean;
  similar_considered: { id: string; title: string }[];
  issues: ReviewIssue[];
  summary: string;
}

// -- Observabilidade (changes 0153/0154/0155, ADR 0016) ---------------------

export interface CiSignalPoint {
  at: string;
  value: number;
  run_id: string;
  conclusion?: string | null;
  url?: string | null;
}

export interface CiSignalSeries {
  /** De onde o número veio: `declarado` pelo pipeline, ou `derivado` — o
      Arbites calculou a partir do que ele mesmo apurou (ADR 0019). Mostrar
      um derivado como se o pipeline o tivesse medido seria mentir sobre a
      procedência. */
  source?: "declarado" | "derivado";
  name: string;
  kind: string;
  unit: string | null;
  points: CiSignalPoint[];
  current: number | null;
  average: number | null;
  previous_average: number | null;
  delta_pct: number | null;
  /** "lower" | "higher" — declarado no arbites.yaml, nunca inferido. */
  direction: string | null;
  goal: number | null;
}

export interface CiJob {
  name: string;
  conclusion: string | null;
  started_at: string | null;
  finished_at: string | null;
  url: string | null;
}

export interface CiAttachment {
  kind: string;
  path: string;
  title: string | null;
  sha256: string;
  bytes: number;
}

export interface CiRun {
  id: string;
  provider: string;
  repo: string;
  workflow: string;
  run_id: string;
  event: string | null;
  conclusion: string | null;
  commit_sha: string | null;
  branch: string | null;
  started_at: string | null;
  finished_at: string | null;
  url: string | null;
  ingested_at: string;
  ingest_warning: string | null;
  signals: { kind: string; name: string; value: number; unit: string | null; at: string }[];
  attachments: CiAttachment[];
  jobs: CiJob[];
  analysis?: string;
}

export interface CiChange {
  kind: "silence" | "broke" | "signal" | "convention" | "flaky";
  text: string;
  run_id?: string;
  signal?: string;
  scenario?: string;
  testcase_id?: string;
  goal_miss?: boolean;
}

/** Cenário que passa E falha no período (change 0159). */
export interface CiFlaky {
  scenario: string;
  testcase_id: string | null;
  runs: number;
  failures: number;
  flips: number;
  /** Estava estável no período anterior — é o que separa notícia de ruído. */
  newly_flaky: boolean;
  last_run: string | null;
}

export interface Observability {
  period: { since: string; until: string; days: number };
  previous: { since: string; until: string };
  health: {
    runs: number;
    runs_previous: number;
    /** O denominador da taxa: só as execuções que deram um veredito. */
    conclusive_runs: number;
    inconclusive_runs: number;
    success_rate: number | null;
    success_rate_previous: number | null;
    last_run_at: string | null;
    days_since_last_run: number | null;
    goal: number | null;
  };
  signals: CiSignalSeries[];
  flaky: CiFlaky[];
  changes: CiChange[];
  runs: CiRun[];
  /** Divisões do período — a pergunta "de que é feito", que a série não responde. */
  distribution: {
    /** Só o veredito: passou, falhou, estourou o tempo. */
    runs_by_conclusion: CiFatia[];
    /** Cancelada e skipped — fora da conta, dentro da tela (change 0191). */
    runs_inconclusive: CiFatia[];
    inconclusive_total: number;
    scenarios_by_status: CiFatia[];
  };
  findings: CiAchados;
  /** Saúde por repositório de teste e por rótulo declarado no manifesto. */
  by_repo: CiRecorte[];
  /** Saúde por repositório que DISPAROU a suíte — a aplicação, não o teste. */
  by_origin: CiRecorte[];
  errors_by_origin: CiFatia[];
  label_names: string[];
  by_label: Record<string, CiRecorte[]>;
}

export interface CiFatia {
  label: string;
  value: number;
  /** Calculada no servidor: duas telas dividindo por conta própria discordam. */
  pct: number;
}

export interface CiRecorte {
  name: string;
  runs: number;
  conclusive: number;
  inconclusive: number;
  failures: number;
  success_rate: number | null;
  success_rate_previous: number | null;
  delta_pct: number | null;
  last_run_at: string | null;
}

export interface CiRegra {
  rule: string;
  impact: string;
  wcag: string | null;
  level: string | null;
  count: number;
  runs: number;
  help: string | null;
  help_url: string | null;
}

export interface CiAchados {
  total: number;
  previous_total: number;
  delta_pct: number | null;
  by_impact: CiFatia[];
  by_category: CiFatia[];
  top_rules: CiRegra[];
  by_wcag: { wcag: string; level: string | null; count: number }[];
  top_pages: { page: string; count: number }[];
}

export interface GithubTokenStatus {
  configured: boolean;
  expires_at: string | null;
  days_until_expiry: number | null;
  last_refusal: { at: string; status: number; message: string } | null;
  last_success_at: string | null;
  healthy: boolean;
}

export interface CiRetention {
  retention: { signals_days: number; attachments_days: number };
  usage: {
    runs: number;
    documents_bytes: number;
    attachments_bytes: number;
    total_bytes: number;
  };
  would_remove: {
    attachments: { id: string; path: string; at: string; bytes: number; files: number }[];
    runs: { id: string; path: string; at: string; bytes: number }[];
    bytes: number;
  };
}

// -- o sino (change 0161) ---------------------------------------------------

export interface NotificationTarget {
  tab: string;
  id?: string;
  path?: string;
  run?: string;
  atab?: string;
}

export interface Notification {
  id: string;
  kind: "problema" | "prazo" | "observabilidade" | "feito" | "info";
  severity: "problem" | "attention" | "done" | "info";
  /** O nome do arquivo/card, separado da frase para poder ir em destaque. */
  subject: string;
  subject_full: string;
  message: string;
  at: string;
  target: NotificationTarget;
  read: boolean;
}

export interface NotificationsResponse {
  items: Notification[];
  unread: number;
  cleared_at: string;
}

// -- listas de To Do (change 0164) ------------------------------------------

export interface TodoListItem {
  id: string;
  text: string;
  done: boolean;
  /** O afazer vinculado — o vínculo mora AQUI, na linha, e só aqui. */
  todo: string | null;
  todo_ref?: { id: string; title: string; status: string; due: string | null } | null;
}

export interface TodoList {
  id: string;
  title: string;
  status: "active" | "done" | "archived";
  due: string | null;
  created: string | null;
  path: string;
  items: TodoListItem[];
  progress: { total: number; done: number; open: number };
  body: string;
}

/** Repositório de onde a observabilidade puxa execuções (change 0173). */
export interface CiSource {
  provider?: string;
  repo: string;
  /** Vazio = todos os workflows do repositório. */
  workflow?: string | null;
  /** Vazio = todos os artifacts do run. */
  artifact?: string | null;
}

/** Uma análise da observabilidade guardada no workspace (change 0179). */
export interface CiAnaliseResumo {
  id: string;
  created_at: string;
  days: number | null;
  provider: string | null;
  saude_geral: string | null;
  sintese: string | null;
  runs: number | null;
  success_rate: number | null;
  findings_total: number | null;
  riscos: number;
  path: string;
}

export interface CiAnalise extends CiAnaliseResumo {
  body: string;
  riscos_detalhe?: { titulo: string; evidencia: string; gravidade: string }[];
}

export interface CiComparativo {
  from: string;
  to: string;
  from_at: string | null;
  to_at: string | null;
  veredito: string;
  sintese: string;
  melhoras: string[];
  pioras: string[];
  permanece: string[];
  proximo_passo: string;
}

/** Uma evidência do período, com o contexto do run colado (change 0180). */
export interface CiEvidencia {
  kind: string;
  path: string;
  title: string | null;
  bytes: number | null;
  sha256: string | null;
  run_id: string;
  workflow: string | null;
  conclusion: string | null;
  repo: string | null;
  trigger_repo: string | null;
  url: string | null;
  at: string | null;
}

export interface CiEvidencias {
  items: CiEvidencia[];
  by_kind: CiFatia[];
  total_bytes: number;
  /** O limite foi atingido: há mais evidência do que a lista mostra. */
  truncated: boolean;
}
