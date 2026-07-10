import { Suspense, lazy, useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Modal } from "./components/Modal";
import type { TreeNode, Warning, WorkspaceInfo } from "./types";

const TcRepository = lazy(() =>
  import("./components/TcRepository").then((m) => ({ default: m.TcRepository }))
);
const TestCaseEditor = lazy(() =>
  import("./components/TestCaseEditor").then((m) => ({ default: m.TestCaseEditor }))
);
const ReqRepository = lazy(() =>
  import("./components/Requirements").then((m) => ({ default: m.ReqRepository }))
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
const ExecutionsRepo = lazy(() =>
  import("./components/Executions").then((m) => ({ default: m.ExecutionsRepo }))
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
const Defects = lazy(() =>
  import("./components/Defects").then((m) => ({ default: m.Defects }))
);
const Daily = lazy(() =>
  import("./components/Daily").then((m) => ({ default: m.Daily }))
);
const Meetings = lazy(() =>
  import("./components/Meetings").then((m) => ({ default: m.Meetings }))
);
const Profile = lazy(() =>
  import("./components/Profile").then((m) => ({ default: m.Profile }))
);

type Tab =
  | "testcases"
  | "requirements"
  | "executions"
  | "defects"
  | "todos"
  | "daily"
  | "meetings"
  | "dashboard"
  | "automation"
  | "ia"
  | "migration"
  | "problems"
  | "profile";

const NAV: { key: Tab; label: string }[] = [
  { key: "testcases", label: "Test cases" },
  { key: "requirements", label: "Requisitos" },
  { key: "executions", label: "Execuções" },
  { key: "defects", label: "Defeitos" },
  { key: "todos", label: "Afazeres" },
  { key: "daily", label: "Daily" },
  { key: "meetings", label: "Reuniões" },
  { key: "dashboard", label: "Dashboard" },
  { key: "automation", label: "Automação" },
  { key: "ia", label: "IA" },
  { key: "migration", label: "Migração" },
  { key: "problems", label: "Problemas" },
  { key: "profile", label: "Perfil" },
];

// Agrupamento semântico do menu (doc de ajustes §3)
const NAV_GROUPS: { title: string; keys: Tab[] }[] = [
  { title: "Planejamento", keys: ["requirements", "testcases", "executions"] },
  { title: "Acompanhamento", keys: ["defects", "todos", "dashboard", "daily", "meetings"] },
  { title: "Ferramentas", keys: ["automation", "ia", "migration"] },
  { title: "Suporte", keys: ["problems", "profile"] },
];

const NAV_BY_KEY = Object.fromEntries(NAV.map((n) => [n.key, n])) as Record<
  Tab,
  { key: Tab; label: string }
>;

function loadJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function NavItem({
  item,
  tab,
  setTab,
  problemCount,
  pinned,
  onTogglePin,
}: {
  item: { key: Tab; label: string };
  tab: Tab;
  setTab: (t: Tab) => void;
  problemCount: number;
  pinned: boolean;
  onTogglePin: () => void;
}) {
  return (
    <div className={`nav-row ${tab === item.key ? "active" : ""}`}>
      <button
        className={`nav-item ${tab === item.key ? "active" : ""}`}
        onClick={() => setTab(item.key)}
        aria-current={tab === item.key ? "page" : undefined}
      >
        {item.label}
        {item.key === "problems" && problemCount > 0 && (
          <span className="count">{problemCount}</span>
        )}
      </button>
      <button
        className={`nav-pin ${pinned ? "pinned" : ""}`}
        onClick={onTogglePin}
        title={pinned ? "Desafixar do acesso rápido" : "Fixar no acesso rápido"}
        aria-label={pinned ? `Desafixar ${item.label}` : `Fixar ${item.label}`}
      >
        {pinned ? "★" : "☆"}
      </button>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState<Tab>("testcases");
  const [workspace, setWorkspace] = useState<WorkspaceInfo | null>(null);
  const [tree, setTree] = useState<TreeNode | null>(null);
  const [warnings, setWarnings] = useState<Warning[]>([]);
  const [selectedCt, setSelectedCt] = useState<string | null>(null);
  const [selectedReq, setSelectedReq] = useState<string | null>(null);
  const [selectedExec, setSelectedExec] = useState<string | null>(null);
  const [selectedDefect, setSelectedDefect] = useState<string | null>(null);
  const [execCreating, setExecCreating] = useState(false);
  const [reqVersion, setReqVersion] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [reindexing, setReindexing] = useState(false);
  const [creatingCt, setCreatingCt] = useState(false);
  const [pins, setPins] = useState<Tab[]>(() => loadJson<Tab[]>("arbites.pins", []));
  const [collapsed, setCollapsed] = useState<string[]>(() =>
    loadJson<string[]>("arbites.navCollapsed", []),
  );

  function togglePin(key: Tab) {
    setPins((old) => {
      const next = old.includes(key) ? old.filter((k) => k !== key) : [...old, key];
      localStorage.setItem("arbites.pins", JSON.stringify(next));
      return next;
    });
  }

  function toggleGroup(title: string) {
    setCollapsed((old) => {
      const next = old.includes(title) ? old.filter((t) => t !== title) : [...old, title];
      localStorage.setItem("arbites.navCollapsed", JSON.stringify(next));
      return next;
    });
  }

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

  // Navega até um artefato pelo id (aba inferida do prefixo) — usado pelos
  // links e menções @ dos afazeres.
  const navigateTo = useCallback((id: string) => {
    const prefix = id.split("-")[0];
    if (prefix === "CT") {
      setSelectedCt(id);
      setTab("testcases");
    } else if (prefix === "EP" || prefix === "ST") {
      setSelectedReq(id);
      setTab("requirements");
    } else if (prefix === "EXEC") {
      setExecCreating(false);
      setSelectedExec(id);
      setTab("executions");
    } else if (prefix === "TD") {
      setTab("todos");
    } else if (prefix === "DF") {
      setSelectedDefect(id);
      setTab("defects");
    }
  }, []);

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
            {pins.length > 0 && (
              <div className="nav-group">
                <div className="nav-group-title">
                  <span>Acesso rápido</span>
                </div>
                {pins
                  .filter((k) => NAV_BY_KEY[k])
                  .map((k) => (
                    <NavItem
                      key={`pin-${k}`}
                      item={NAV_BY_KEY[k]}
                      tab={tab}
                      setTab={setTab}
                      problemCount={problemCount}
                      pinned
                      onTogglePin={() => togglePin(k)}
                    />
                  ))}
              </div>
            )}
            {NAV_GROUPS.map((group) => (
              <div key={group.title} className="nav-group">
                <button
                  className="nav-group-title"
                  onClick={() => toggleGroup(group.title)}
                  aria-expanded={!collapsed.includes(group.title)}
                >
                  <span>{group.title}</span>
                  <span className="nav-chevron">
                    {collapsed.includes(group.title) ? "▸" : "▾"}
                  </span>
                </button>
                {!collapsed.includes(group.title) &&
                  group.keys.map((k) => (
                    <NavItem
                      key={k}
                      item={NAV_BY_KEY[k]}
                      tab={tab}
                      setTab={setTab}
                      problemCount={problemCount}
                      pinned={pins.includes(k)}
                      onTogglePin={() => togglePin(k)}
                    />
                  ))}
              </div>
            ))}
          </nav>
        </aside>
        <main className="main">
          <div className="main-inner">
          {error && <div className="error-banner">{error}</div>}
          <ErrorBoundary key={tab}>
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
          ) : tab === "defects" ? (
            <Suspense fallback={<p className="empty">Carregando defeitos…</p>}>
              <Defects
                onError={setError}
                onNavigate={navigateTo}
                openId={selectedDefect}
                onOpened={() => setSelectedDefect(null)}
              />
            </Suspense>
          ) : tab === "todos" ? (
            <Suspense fallback={<p className="empty">Carregando afazeres…</p>}>
              <Todos onError={setError} onNavigate={navigateTo} />
            </Suspense>
          ) : tab === "daily" ? (
            <Suspense fallback={<p className="empty">Carregando daily…</p>}>
              <Daily onError={setError} />
            </Suspense>
          ) : tab === "meetings" ? (
            <Suspense fallback={<p className="empty">Carregando reuniões…</p>}>
              <Meetings onError={setError} />
            </Suspense>
          ) : tab === "profile" ? (
            <Suspense fallback={<p className="empty">Carregando perfil…</p>}>
              <Profile onError={setError} />
            </Suspense>
          ) : tab === "migration" ? (
            <Suspense fallback={<p className="empty">Carregando migração…</p>}>
              <XrayImport onImported={() => void refresh()} onError={setError} />
            </Suspense>
          ) : tab === "executions" ? (
            execCreating ? (
              <Suspense fallback={<p className="empty">Carregando criação…</p>}>
                <div className="back-bar">
                  <button onClick={() => setExecCreating(false)}>← Voltar</button>
                </div>
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
                <div className="back-bar">
                  <button onClick={() => setSelectedExec(null)}>← Voltar</button>
                </div>
                <ExecutionBoard id={selectedExec} onChanged={refresh} onError={setError} />
              </Suspense>
            ) : (
              <Suspense fallback={<p className="empty">Carregando execuções…</p>}>
                <ExecutionsRepo
                  version={reqVersion}
                  onOpen={(id) => {
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
            )
          ) : tab === "requirements" ? (
            selectedReq ? (
              <Suspense fallback={<p className="empty">Carregando requisito…</p>}>
                <div className="back-bar">
                  <button onClick={() => setSelectedReq(null)}>← Voltar</button>
                </div>
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
              <Suspense fallback={<p className="empty">Carregando requisitos…</p>}>
                <ReqRepository
                  version={reqVersion}
                  onOpen={setSelectedReq}
                  onChanged={() => void refresh()}
                  onError={setError}
                />
              </Suspense>
            )
          ) : selectedCt ? (
            <Suspense fallback={<p className="empty">Carregando test case…</p>}>
              <div className="back-bar">
                <button onClick={() => setSelectedCt(null)}>← Voltar</button>
              </div>
              <TestCaseEditor
                id={selectedCt}
                onChanged={refresh}
                onDeleted={() => {
                  setSelectedCt(null);
                  void refresh();
                }}
              />
            </Suspense>
          ) : tree ? (
            <Suspense fallback={<p className="empty">Carregando repositório…</p>}>
              <TcRepository
                root={tree}
                onOpen={setSelectedCt}
                onChanged={() => void refresh()}
                onError={setError}
                onNew={() => setCreatingCt(true)}
              />
            </Suspense>
          ) : (
            <p className="empty">Carregando repositório…</p>
          )}
          </ErrorBoundary>
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
