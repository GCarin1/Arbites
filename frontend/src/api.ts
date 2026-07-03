import type { Requirement, TestCase, TreeNode, Warning, WorkspaceInfo } from "./types";

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
};
