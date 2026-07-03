import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { TreeNode, Warning, WorkspaceInfo } from "./types";
import { Tree } from "./components/Tree";
import { TestCaseEditor } from "./components/TestCaseEditor";
import { RequirementsList, RequirementEditor } from "./components/Requirements";
import { WarningsView } from "./components/Warnings";

type Tab = "testcases" | "requirements" | "problems";

export default function App() {
  const [tab, setTab] = useState<Tab>("testcases");
  const [workspace, setWorkspace] = useState<WorkspaceInfo | null>(null);
  const [tree, setTree] = useState<TreeNode | null>(null);
  const [warnings, setWarnings] = useState<Warning[]>([]);
  const [selectedCt, setSelectedCt] = useState<string | null>(null);
  const [selectedReq, setSelectedReq] = useState<string | null>(null);
  const [reqVersion, setReqVersion] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [reindexing, setReindexing] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [wsInfo, treeData, warningData] = await Promise.all([
        api.workspace(),
        api.tree(),
        api.warnings(),
      ]);
      setWorkspace(wsInfo);
      setTree(treeData);
      setWarnings(warningData);
      setReqVersion((v) => v + 1);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = setInterval(refresh, 5000); // reflete edições externas (watcher)
    return () => clearInterval(timer);
  }, [refresh]);

  async function reindex() {
    setReindexing(true);
    try {
      await api.reindex();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setReindexing(false);
    }
  }

  async function newTestcase() {
    const title = window.prompt("Título do novo test case:");
    if (!title) return;
    const folder = window.prompt("Pasta (ex.: frontend/login — vazio = raiz):") ?? "";
    try {
      const created = await api.createTestcase({ title, folder });
      await refresh();
      setSelectedCt(created.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  const problemCount = warnings.length;

  return (
    <>
      <header className="topbar">
        <span className="brand">Arbites</span>
        <span className="meta">
          {workspace?.config.workspace?.name ?? "…"} ·{" "}
          {workspace?.index.testcases ?? 0} CTs · {workspace?.index.requirements ?? 0}{" "}
          requisitos
        </span>
        <span className="spacer" />
        <span className="meta mono">{workspace?.root}</span>
        <button onClick={() => void reindex()} disabled={reindexing}>
          {reindexing ? "Reindexando…" : "Reindexar"}
        </button>
      </header>
      <div className="layout">
        <aside className="sidebar">
          <nav className="tabs">
            <button
              className={tab === "testcases" ? "active" : ""}
              onClick={() => setTab("testcases")}
            >
              Test cases
            </button>
            <button
              className={tab === "requirements" ? "active" : ""}
              onClick={() => setTab("requirements")}
            >
              Requisitos
            </button>
            <button
              className={tab === "problems" ? "active" : ""}
              onClick={() => setTab("problems")}
            >
              Problemas{problemCount > 0 ? ` (${problemCount})` : ""}
            </button>
          </nav>
          <div className="scroll">
            {tab === "testcases" && tree && (
              <Tree root={tree} selected={selectedCt} onSelect={setSelectedCt} />
            )}
            {tab === "requirements" && (
              <RequirementsList
                version={reqVersion}
                selected={selectedReq}
                onSelect={setSelectedReq}
                onCreated={(id) => {
                  setSelectedReq(id);
                  void refresh();
                }}
                onError={setError}
              />
            )}
            {tab === "problems" && (
              <p className="muted" style={{ padding: 8 }}>
                {problemCount === 0
                  ? "Nenhum problema de integridade."
                  : "Detalhes no painel principal."}
              </p>
            )}
          </div>
          {tab === "testcases" && (
            <div className="actions">
              <button className="primary" onClick={() => void newTestcase()}>
                Novo test case
              </button>
            </div>
          )}
        </aside>
        <main className="main">
          {error && <div className="error-banner">{error}</div>}
          {tab === "problems" ? (
            <WarningsView warnings={warnings} />
          ) : tab === "requirements" ? (
            selectedReq ? (
              <RequirementEditor
                id={selectedReq}
                onChanged={refresh}
                onDeleted={() => {
                  setSelectedReq(null);
                  void refresh();
                }}
              />
            ) : (
              <p className="empty">Selecione ou crie um requisito na lateral.</p>
            )
          ) : selectedCt ? (
            <TestCaseEditor
              id={selectedCt}
              onChanged={refresh}
              onDeleted={() => {
                setSelectedCt(null);
                void refresh();
              }}
            />
          ) : (
            <p className="empty">Selecione um test case na árvore ou crie um novo.</p>
          )}
        </main>
      </div>
    </>
  );
}
