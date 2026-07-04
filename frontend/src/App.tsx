import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { TreeNode, Warning, WorkspaceInfo } from "./types";
import { Tree } from "./components/Tree";
import { TestCaseEditor } from "./components/TestCaseEditor";
import { RequirementsList, RequirementEditor } from "./components/Requirements";
import { WarningsView } from "./components/Warnings";
import {
  ExecutionBoard,
  ExecutionCreate,
  ExecutionsList,
} from "./components/Executions";
import { Dashboard } from "./components/Dashboard";
import { XrayImport } from "./components/XrayImport";
import { Automation } from "./components/Automation";

type Tab =
  | "testcases"
  | "requirements"
  | "executions"
  | "dashboard"
  | "automation"
  | "migration"
  | "problems";

export default function App() {
  const [tab, setTab] = useState<Tab>("testcases");
  const [workspace, setWorkspace] = useState<WorkspaceInfo | null>(null);
  const [tree, setTree] = useState<TreeNode | null>(null);
  const [warnings, setWarnings] = useState<Warning[]>([]);
  const [selectedCt, setSelectedCt] = useState<string | null>(null);
  const [selectedReq, setSelectedReq] = useState<string | null>(null);
  const [selectedExec, setSelectedExec] = useState<string | null>(null);
  const [execCreating, setExecCreating] = useState(false);
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
              className={tab === "executions" ? "active" : ""}
              onClick={() => setTab("executions")}
            >
              Execuções
            </button>
            <button
              className={tab === "dashboard" ? "active" : ""}
              onClick={() => setTab("dashboard")}
            >
              Dashboard
            </button>
            <button
              className={tab === "automation" ? "active" : ""}
              onClick={() => setTab("automation")}
            >
              Automação
            </button>
            <button
              className={tab === "migration" ? "active" : ""}
              onClick={() => setTab("migration")}
            >
              Migração
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
            {tab === "executions" && (
              <ExecutionsList
                version={reqVersion}
                selected={selectedExec}
                onSelect={(id) => {
                  setExecCreating(false);
                  setSelectedExec(id);
                }}
                onNew={() => {
                  setSelectedExec(null);
                  setExecCreating(true);
                }}
                onError={setError}
              />
            )}
            {tab === "dashboard" && (
              <p className="muted" style={{ padding: 8 }}>
                Métricas, tendência e matriz de rastreabilidade no painel
                principal. Cada linha da matriz expande até a evidência.
              </p>
            )}
            {tab === "automation" && (
              <p className="muted" style={{ padding: 8 }}>
                Targets do arbites.yaml, re-scan de features e runs Behave
                com log ao vivo no painel principal. Uma execução por
                target; excedentes entram em fila FIFO.
              </p>
            )}
            {tab === "migration" && (
              <p className="muted" style={{ padding: 8 }}>
                Import do XML do Xray (preview → confirm, idempotente) no
                painel principal. Export Markdown fica no próprio wizard.
              </p>
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
          ) : tab === "dashboard" ? (
            <Dashboard onError={setError} />
          ) : tab === "automation" ? (
            <Automation onChanged={() => void refresh()} onError={setError} />
          ) : tab === "migration" ? (
            <XrayImport onImported={() => void refresh()} onError={setError} />
          ) : tab === "executions" ? (
            execCreating ? (
              <ExecutionCreate
                onCreated={(id) => {
                  setExecCreating(false);
                  setSelectedExec(id);
                  void refresh();
                }}
                onError={setError}
              />
            ) : selectedExec ? (
              <ExecutionBoard id={selectedExec} onChanged={refresh} onError={setError} />
            ) : (
              <p className="empty">Selecione uma execução ou crie uma nova.</p>
            )
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
