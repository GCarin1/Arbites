import { Suspense, lazy, useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { Modal } from "./components/Modal";
import type { TreeNode, Warning, WorkspaceInfo } from "./types";

const Tree = lazy(() => import("./components/Tree").then((m) => ({ default: m.Tree })));
const TestCaseEditor = lazy(() =>
  import("./components/TestCaseEditor").then((m) => ({ default: m.TestCaseEditor }))
);
const RequirementsList = lazy(() =>
  import("./components/Requirements").then((m) => ({ default: m.RequirementsList }))
);
const RequirementEditor = lazy(() =>
  import("./components/Requirements").then((m) => ({ default: m.RequirementEditor }))
);
const WarningsView = lazy(() =>
  import("./components/Warnings").then((m) => ({ default: m.WarningsView }))
);
const ExecutionBoard = lazy(() =>
  import("./components/Executions").then((m) => ({ default: m.ExecutionBoard }))
);
const ExecutionCreate = lazy(() =>
  import("./components/Executions").then((m) => ({ default: m.ExecutionCreate }))
);
const ExecutionsList = lazy(() =>
  import("./components/Executions").then((m) => ({ default: m.ExecutionsList }))
);
const Dashboard = lazy(() =>
  import("./components/Dashboard").then((m) => ({ default: m.Dashboard }))
);
const XrayImport = lazy(() =>
  import("./components/XrayImport").then((m) => ({ default: m.XrayImport }))
);
const Automation = lazy(() =>
  import("./components/Automation").then((m) => ({ default: m.Automation }))
);
const AiAssist = lazy(() =>
  import("./components/AiAssist").then((m) => ({ default: m.AiAssist }))
);
const Todos = lazy(() =>
  import("./components/Todos").then((m) => ({ default: m.Todos }))
);
const Daily = lazy(() =>
  import("./components/Daily").then((m) => ({ default: m.Daily }))
);

type Tab =
  | "testcases"
  | "requirements"
  | "executions"
  | "todos"
  | "daily"
  | "dashboard"
  | "automation"
  | "ia"
  | "migration"
  | "problems";

const NAV: { key: Tab; label: string }[] = [
  { key: "testcases", label: "Test cases" },
  { key: "requirements", label: "Requisitos" },
  { key: "executions", label: "Execuções" },
  { key: "todos", label: "Afazeres" },
  { key: "daily", label: "Daily" },
  { key: "dashboard", label: "Dashboard" },
  { key: "automation", label: "Automação" },
  { key: "ia", label: "IA" },
  { key: "migration", label: "Migração" },
  { key: "problems", label: "Problemas" },
];

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
  const [creatingCt, setCreatingCt] = useState(false);

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

  async function createTestcase(title: string, folder: string) {
    try {
      const created = await api.createTestcase({ title, folder });
      setCreatingCt(false);
      await refresh();
      setSelectedCt(created.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  const problemCount = warnings.length;

  return (
    <>
      <header className="app-header">
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
      <div className="app-body">
        <aside className="sidebar">
          <nav className="nav">
            {NAV.map((item) => (
              <button
                key={item.key}
                className={`nav-item ${tab === item.key ? "active" : ""}`}
                onClick={() => setTab(item.key)}
                aria-current={tab === item.key ? "page" : undefined}
              >
                {item.label}
                {item.key === "problems" && problemCount > 0 && (
                  <span className="count">{problemCount}</span>
                )}
              </button>
            ))}
          </nav>
          <div className="panel">
            {tab === "testcases" && tree && (
              <Suspense fallback={<p className="empty">Carregando árvore…</p>}>
                <Tree root={tree} selected={selectedCt} onSelect={setSelectedCt} />
              </Suspense>
            )}
            {tab === "requirements" && (
              <Suspense fallback={<p className="empty">Carregando requisitos…</p>}>
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
              </Suspense>
            )}
            {tab === "executions" && (
              <Suspense fallback={<p className="empty">Carregando execuções…</p>}>
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
              </Suspense>
            )}
            {tab === "dashboard" && (
              <p className="panel-hint">
                Métricas, tendência e matriz de rastreabilidade no painel
                principal. Cada linha da matriz expande até a evidência.
              </p>
            )}
            {tab === "automation" && (
              <p className="panel-hint">
                Targets do arbites.yaml, re-scan de features e runs Behave
                com log ao vivo no painel principal. Uma execução por
                target; excedentes entram em fila FIFO.
              </p>
            )}
            {tab === "ia" && (
              <p className="panel-hint">
                IA é opcional: configure providers (chaves no keyring) e gere,
                revise ou proponha casos negativos no painel principal. Toda
                saída é preview — nada é gravado sem você aceitar.
              </p>
            )}
            {tab === "todos" && (
              <p className="panel-hint">
                Lista de afazeres com prazo, status e links para CT/execução/
                story. Impedimentos (blocked) e concluídos ficam no histórico —
                e alimentam a daily.
              </p>
            )}
            {tab === "daily" && (
              <p className="panel-hint">
                Escolha o dia no calendário. A IA (opcional) digere afazeres +
                atividade + diff de métricas + defeitos e gera o texto da daily
                com action items — que viram afazeres.
              </p>
            )}
            {tab === "migration" && (
              <p className="panel-hint">
                Import do XML do Xray (preview → confirm, idempotente) no
                painel principal. Export Markdown fica no próprio wizard.
              </p>
            )}
            {tab === "problems" && (
              <p className="panel-hint">
                {problemCount === 0
                  ? "Nenhum problema de integridade."
                  : "Detalhes no painel principal."}
              </p>
            )}
          </div>
          {tab === "testcases" && (
            <div className="actions">
              <button className="primary" onClick={() => setCreatingCt(true)}>
                Novo test case
              </button>
            </div>
          )}
        </aside>
        <main className="main">
          <div className="main-inner">
          {error && <div className="error-banner">{error}</div>}
          {tab === "problems" ? (
            <Suspense fallback={<p className="empty">Carregando problemas…</p>}>
              <WarningsView warnings={warnings} />
            </Suspense>
          ) : tab === "dashboard" ? (
            <Suspense fallback={<p className="empty">Carregando dashboard…</p>}>
              <Dashboard onError={setError} />
            </Suspense>
          ) : tab === "automation" ? (
            <Suspense fallback={<p className="empty">Carregando automação…</p>}>
              <Automation onChanged={() => void refresh()} onError={setError} />
            </Suspense>
          ) : tab === "ia" ? (
            <Suspense fallback={<p className="empty">Carregando IA…</p>}>
              <AiAssist onChanged={() => void refresh()} onError={setError} />
            </Suspense>
          ) : tab === "todos" ? (
            <Suspense fallback={<p className="empty">Carregando afazeres…</p>}>
              <Todos onError={setError} />
            </Suspense>
          ) : tab === "daily" ? (
            <Suspense fallback={<p className="empty">Carregando daily…</p>}>
              <Daily onError={setError} />
            </Suspense>
          ) : tab === "migration" ? (
            <Suspense fallback={<p className="empty">Carregando migração…</p>}>
              <XrayImport onImported={() => void refresh()} onError={setError} />
            </Suspense>
          ) : tab === "executions" ? (
            execCreating ? (
              <Suspense fallback={<p className="empty">Carregando criação…</p>}>
                <ExecutionCreate
                  onCreated={(id) => {
                    setExecCreating(false);
                    setSelectedExec(id);
                    void refresh();
                  }}
                  onError={setError}
                />
              </Suspense>
            ) : selectedExec ? (
              <Suspense fallback={<p className="empty">Carregando execução…</p>}>
                <ExecutionBoard id={selectedExec} onChanged={refresh} onError={setError} />
              </Suspense>
            ) : (
              <div className="empty-state">
                <div className="empty-title">Nenhuma execução aberta</div>
                <div className="empty-body">
                  Selecione uma execução na lista ou crie uma nova para começar
                  a registrar resultados.
                </div>
              </div>
            )
          ) : tab === "requirements" ? (
            selectedReq ? (
              <Suspense fallback={<p className="empty">Carregando requisito…</p>}>
                <RequirementEditor
                  id={selectedReq}
                  onChanged={refresh}
                  onDeleted={() => {
                    setSelectedReq(null);
                    void refresh();
                  }}
                />
              </Suspense>
            ) : (
              <div className="empty-state">
                <div className="empty-title">Nenhum requisito selecionado</div>
                <div className="empty-body">
                  Selecione um epic ou story na lista à esquerda, ou crie um novo
                  requisito.
                </div>
              </div>
            )
          ) : selectedCt ? (
            <Suspense fallback={<p className="empty">Carregando test case…</p>}>
              <TestCaseEditor
                id={selectedCt}
                onChanged={refresh}
                onDeleted={() => {
                  setSelectedCt(null);
                  void refresh();
                }}
              />
            </Suspense>
          ) : (
            <div className="empty-state">
              <div className="empty-title">Nenhum test case selecionado</div>
              <div className="empty-body">
                Selecione um test case na árvore à esquerda ou crie um novo para
                começar a editar.
              </div>
            </div>
          )}
          </div>
        </main>
      </div>
      {creatingCt && (
        <NewTestcaseModal
          onSubmit={createTestcase}
          onClose={() => setCreatingCt(false)}
        />
      )}
    </>
  );
}

function NewTestcaseModal({
  onSubmit,
  onClose,
}: {
  onSubmit: (title: string, folder: string) => void;
  onClose: () => void;
}) {
  const [title, setTitle] = useState("");
  const [folder, setFolder] = useState("");
  const titleRef = useRef<HTMLInputElement>(null);

  function submit() {
    if (!title.trim()) return;
    onSubmit(title.trim(), folder.trim());
  }

  return (
    <Modal
      title="Novo test case"
      onClose={onClose}
      initialFocus={titleRef}
      footer={
        <>
          <button onClick={onClose}>Cancelar</button>
          <button className="primary" onClick={submit} disabled={!title.trim()}>
            Criar
          </button>
        </>
      }
    >
      <form
        className="modal-field"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <label htmlFor="new-ct-title">Título</label>
        <input
          id="new-ct-title"
          ref={titleRef}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Ex.: Login com credenciais válidas"
        />
      </form>
      <div className="modal-field">
        <label htmlFor="new-ct-folder">Pasta (opcional)</label>
        <input
          id="new-ct-folder"
          className="mono"
          value={folder}
          onChange={(e) => setFolder(e.target.value)}
          placeholder="frontend/login — vazio = raiz"
        />
      </div>
    </Modal>
  );
}
