import { Suspense, lazy, useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Modal } from "./components/Modal";
import type { TreeNode, Warning, WorkspaceInfo } from "./types";

const Home = lazy(() =>
  import("./components/Home").then((m) => ({ default: m.Home }))
);
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
const Decisions = lazy(() =>
  import("./components/Decisions").then((m) => ({ default: m.Decisions }))
);
const Audit = lazy(() =>
  import("./components/Audit").then((m) => ({ default: m.Audit }))
);
const Memory = lazy(() =>
  import("./components/Memory").then((m) => ({ default: m.Memory }))
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
const CommandPalette = lazy(() =>
  import("./components/CommandPalette").then((m) => ({ default: m.CommandPalette }))
);

type Tab =
  | "home"
  | "testcases"
  | "requirements"
  | "executions"
  | "defects"
  | "decisions"
  | "audit"
  | "memory"
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
  { key: "home", label: "Hoje" },
  { key: "testcases", label: "Test cases" },
  { key: "requirements", label: "Requisitos" },
  { key: "executions", label: "Execuções" },
  { key: "defects", label: "Defeitos" },
  { key: "decisions", label: "Decisões" },
  { key: "audit", label: "Auditoria" },
  { key: "memory", label: "Memória do Projeto" },
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

// -- deep-link por hash (0084): #/<aba>?filtro=valor, sem lib de router -----
const TAB_KEYS = NAV.map((n) => n.key) as Tab[];

function parseHash(): { tab: Tab; params: Record<string, string> } {
  const raw = window.location.hash.replace(/^#\/?/, "");
  const [tabPart, queryPart] = raw.split("?");
  const tab = (TAB_KEYS as string[]).includes(tabPart) ? (tabPart as Tab) : "home";
  const params: Record<string, string> = {};
  if (queryPart) {
    for (const [k, v] of new URLSearchParams(queryPart)) params[k] = v;
  }
  return { tab, params };
}

function buildHash(tab: Tab, params: Record<string, string>): string {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v),
  ).toString();
  return `#/${tab}${qs ? `?${qs}` : ""}`;
}

// Agrupamento semântico do menu (doc de ajustes §3)
const NAV_GROUPS: { title: string; keys: Tab[] }[] = [
  { title: "Planejamento", keys: ["requirements", "testcases", "executions"] },
  { title: "Acompanhamento", keys: ["defects", "decisions", "audit", "memory", "todos", "dashboard", "daily", "meetings"] },
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
  live = false,
}: {
  item: { key: Tab; label: string };
  tab: Tab;
  setTab: (t: Tab) => void;
  problemCount: number;
  pinned: boolean;
  onTogglePin: () => void;
  // indicador "algo executando" (0076): dot pulsante no item
  live?: boolean;
}) {
  return (
    <div className={`nav-row ${tab === item.key ? "active" : ""}`}>
      <button
        className={`nav-item ${tab === item.key ? "active" : ""}`}
        onClick={() => setTab(item.key)}
        aria-current={tab === item.key ? "page" : undefined}
      >
        {item.label}
        {live && <span className="nav-live-dot" title="automação executando" />}
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
  const initialHash = parseHash();
  const [tab, setTab] = useState<Tab>(initialHash.tab);
  // filtros de alto valor serializados no hash (0084); a URL é a fonte da
  // verdade desses filtros — back/forward e deep-link "grátis".
  const [hashParams, setHashParams] = useState<Record<string, string>>(
    initialHash.params,
  );
  const applyingHash = useRef(false);

  // escreve o hash quando aba/filtros mudam (a menos que a mudança tenha vindo
  // de um hashchange — evita loop)
  useEffect(() => {
    const next = buildHash(tab, hashParams);
    if (applyingHash.current) {
      applyingHash.current = false;
      return;
    }
    if (`#${window.location.hash.replace(/^#/, "")}` !== next) {
      window.location.hash = next;
    }
  }, [tab, hashParams]);

  // back/forward do navegador → restaura aba + filtros
  useEffect(() => {
    function onHash() {
      const parsed = parseHash();
      applyingHash.current = true;
      setTab(parsed.tab);
      setHashParams(parsed.params);
    }
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  // troca de aba pelo menu limpa os filtros do hash (filtros são por-aba)
  const selectTab = useCallback((key: Tab) => {
    setTab(key);
    setHashParams({});
  }, []);

  const setHashParam = useCallback((key: string, value: string) => {
    setHashParams((old) => {
      const next = { ...old };
      if (value) next[key] = value;
      else delete next[key];
      return next;
    });
  }, []);
  const [workspace, setWorkspace] = useState<WorkspaceInfo | null>(null);
  const [tree, setTree] = useState<TreeNode | null>(null);
  const [warnings, setWarnings] = useState<Warning[]>([]);
  const [selectedCt, setSelectedCt] = useState<string | null>(null);
  const [selectedReq, setSelectedReq] = useState<string | null>(null);
  const [selectedExec, setSelectedExec] = useState<string | null>(null);
  const [selectedDefect, setSelectedDefect] = useState<string | null>(null);
  const [selectedDecision, setSelectedDecision] = useState<string | null>(null);
  const [execCreating, setExecCreating] = useState(false);
  const [cmdkOpen, setCmdkOpen] = useState(false);
  // runs de automação ativos → dot pulsante no item Automação (0076)
  const [activeRuns, setActiveRuns] = useState(0);
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
    // indicador "executando" no menu — fora do try principal: falha aqui
    // não pode virar banner de erro (é acessório)
    api
      .runsActive()
      .then((r) => setActiveRuns(r.count))
      .catch(() => {});
  }, []);

  useEffect(() => {
    void refresh();
    const timer = setInterval(refresh, 5000); // reflete edições externas (watcher)
    return () => clearInterval(timer);
  }, [refresh]);

  // Busca global: Ctrl/Cmd+K abre a paleta de comandos de qualquer tela.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCmdkOpen((v) => !v);
      }
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

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
    } else if (prefix === "DEC") {
      setSelectedDecision(id);
      setTab("decisions");
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

  const quickActions = [
    {
      id: "new-ct",
      label: "Novo caso de teste",
      hint: "criar",
      run: () => {
        setTab("testcases");
        setCreatingCt(true);
      },
    },
    {
      id: "new-exec",
      label: "Nova execução",
      hint: "criar",
      run: () => {
        setSelectedExec(null);
        setExecCreating(true);
        setTab("executions");
      },
    },
    {
      id: "reindex",
      label: "Reindexar workspace",
      hint: "ação",
      run: () => void reindex(),
    },
  ];

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
        <button className="cmdk-trigger" onClick={() => setCmdkOpen(true)}>
          <span>Buscar…</span>
          <kbd>Ctrl K</kbd>
        </button>
        <span className="meta mono">{workspace?.root}</span>
        <button onClick={() => void reindex()} disabled={reindexing}>
          {reindexing ? "Reindexando…" : "Reindexar"}
        </button>
      </header>
      {cmdkOpen && (
        <Suspense fallback={null}>
          <CommandPalette
            onClose={() => setCmdkOpen(false)}
            onNavigate={navigateTo}
            actions={quickActions}
          />
        </Suspense>
      )}
      <div className="app-body">
        <aside className="sidebar">
          <nav className="nav">
            <div className="nav-group">
              <button
                className={`nav-item ${tab === "home" ? "active" : ""}`}
                onClick={() => selectTab("home")}
                aria-current={tab === "home" ? "page" : undefined}
              >
                Hoje
              </button>
            </div>
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
                      setTab={selectTab}
                      problemCount={problemCount}
                      pinned
                      onTogglePin={() => togglePin(k)}
                      live={k === "automation" && activeRuns > 0}
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
                      setTab={selectTab}
                      problemCount={problemCount}
                      pinned={pins.includes(k)}
                      onTogglePin={() => togglePin(k)}
                      live={k === "automation" && activeRuns > 0}
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
          {tab === "home" ? (
            <Suspense fallback={<p className="empty">Carregando…</p>}>
              <Home
                workspace={workspace}
                warnings={warnings}
                onNavigate={navigateTo}
                onOpen={(t) => setTab(t as Tab)}
              />
            </Suspense>
          ) : tab === "problems" ? (
            <Suspense fallback={<p className="empty">Carregando problemas…</p>}>
              <WarningsView
                warnings={warnings}
                onChanged={() => void refresh()}
                onError={setError}
              />
            </Suspense>
          ) : tab === "dashboard" ? (
            <Suspense fallback={<p className="empty">Carregando dashboard…</p>}>
              <Dashboard
                onError={setError}
                onNavigate={navigateTo}
                squad={hashParams.squad ?? ""}
                onSquadChange={(v) => setHashParam("squad", v)}
              />
            </Suspense>
          ) : tab === "automation" ? (
            <Suspense fallback={<p className="empty">Carregando automação…</p>}>
              <Automation
                onChanged={() => void refresh()}
                onError={setError}
                onNavigate={navigateTo}
                innerTab={hashParams.atab}
                onInnerTabChange={(v) => setHashParam("atab", v)}
              />
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
          ) : tab === "decisions" ? (
            <Suspense fallback={<p className="empty">Carregando decisões…</p>}>
              <Decisions
                onError={setError}
                onNavigate={navigateTo}
                openId={selectedDecision}
                onOpened={() => setSelectedDecision(null)}
              />
            </Suspense>
          ) : tab === "audit" ? (
            <Suspense fallback={<p className="empty">Carregando auditoria…</p>}>
              <Audit onError={setError} />
            </Suspense>
          ) : tab === "memory" ? (
            <Suspense fallback={<p className="empty">Carregando memória do projeto…</p>}>
              <Memory
                onError={setError}
                onNavigate={navigateTo}
                year={hashParams.year ?? ""}
                onYearChange={(v) => setHashParam("year", v)}
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
                  <span className="crumbs caption">
                    <span className="muted">Execuções</span>
                    <span className="crumb-sep">/</span>
                    <span>nova</span>
                  </span>
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
                  <span className="crumbs caption">
                    <span className="muted">Execuções</span>
                    <span className="crumb-sep">/</span>
                    <span className="mono">{selectedExec}</span>
                  </span>
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
                  onNavigate={navigateTo}
                />
              </Suspense>
            )
          ) : tab === "requirements" ? (
            selectedReq ? (
              <Suspense fallback={<p className="empty">Carregando requisito…</p>}>
                <div className="back-bar">
                  <button onClick={() => setSelectedReq(null)}>← Voltar</button>
                  <span className="crumbs caption">
                    <span className="muted">Requisitos</span>
                    <span className="crumb-sep">/</span>
                    <span className="mono">{selectedReq}</span>
                  </span>
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
                  onNavigate={navigateTo}
                  onChanged={() => void refresh()}
                  onError={setError}
                />
              </Suspense>
            )
          ) : selectedCt ? (
            <Suspense fallback={<p className="empty">Carregando test case…</p>}>
              <div className="back-bar">
                <button onClick={() => setSelectedCt(null)}>← Voltar</button>
                <span className="crumbs caption">
                  <span className="muted">Test cases</span>
                  <span className="crumb-sep">/</span>
                  <span className="mono">{selectedCt}</span>
                </span>
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
                statusFilter={hashParams.status ?? ""}
                onStatusFilterChange={(v) => setHashParam("status", v)}
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
