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

export interface ResultEntry {
  testcase_id: string;
  status: string;
  column: string;
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
  closed_at: string | null;
  status: "draft" | "in_progress" | "closed";
  results: ResultEntry[];
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
  created_at: string;
  closed_at: string | null;
  path: string;
  result_counts: Record<string, number>;
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

export interface MetricsSummary {
  requirement_coverage: MetricValue;
  execution_coverage: MetricValue;
  pass_rate: MetricValue;
  blocked_rate: MetricValue;
  rework_rate: MetricValue;
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
