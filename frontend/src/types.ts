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
  path: string;
  body?: string;
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
  body?: string;
}

export interface TodoLink {
  id: string;
  kind: string | null;
  title: string | null;
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
}

export interface GeneratePreview {
  preview: boolean;
  testcases: GeneratedTestcase[];
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
