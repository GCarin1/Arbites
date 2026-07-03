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
  tags?: string[];
  body?: string;
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
