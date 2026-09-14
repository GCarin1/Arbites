import { Suspense, lazy, useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Modal } from "./components/Modal";
import { AccountMenu } from "./components/AccountMenu";
import { NavIcon } from "./components/NavIcons";
import { SWITCHES_CHANGED } from "./switches";
import type { SessionUser, Switch, TreeNode, Warning, WorkspaceInfo } from "./types";

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
const ExecutionGuided = lazy(() =>
  import("./components/ExecutionGuided").then((m) => ({ default: m.ExecutionGuided }))
);
const Dashboard = lazy(() =>
  import("./components/Dashboard").then((m) => ({ default: m.Dashboard }))
);
const Observability = lazy(() =>
  import("./components/Observability").then((m) => ({ default: m.Observability }))
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
const Admin = lazy(() =>
  import("./components/Admin").then((m) => ({ default: m.Admin }))
);
const NotificationBell = lazy(() =>
  import("./components/NotificationBell").then((m) => ({
    default: m.NotificationBell,
  }))
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
  | "observability"
  | "automation"
  | "ia"
  | "migration"
  | "problems"
  | "profile"
  | "admin";

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
  { key: "observability", label: "Observabilidade" },
  { key: "automation", label: "Automação" },
  { key: "ia", label: "IA" },
  { key: "migration", label: "Migração" },
  { key: "problems", label: "Problemas" },
  { key: "profile", label: "Perfil" },
  { key: "admin", label: "Administração" },
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
// Agrupamento por foco (ADR 0012). "Mais" reúne o que foi congelado: as
// telas continuam funcionando e o dado continua lá, mas saem do caminho de
// quem usa o produto para o que ele é — repositório, ciclo e execução.
const NAV_GROUPS: { title: string; keys: Tab[] }[] = [
  // Negócio vem PRIMEIRO porque é a ordem do fluxo: o requisito existe antes
  // do caso, que existe antes da execução. E vem com cabeçalho próprio, não
  // solto: o cabeçalho é o que diz de QUEM é a coisa — requisito é insumo do
  // time de negócio, e o QA cobre o que eles escreveram (change 0152). Um
  // item sob "Testes" afirmava o contrário, e menu que mente sobre a dona da
  // coisa ensina o modelo errado para quem chega.
  { title: "Negócio", keys: ["requirements"] },
  // Automação entra aqui, e não em "Mais" (change 0161): rodar o teste É
  // trabalho de teste. A ADR 0012 congelou a PERIFERIA para focar em
  // repositório, ciclo e execução — automação é o braço da execução, então
  // ela estava do lado errado da régua, não do lado certo.
  { title: "Testes", keys: ["testcases", "executions", "automation"] },
  {
    title: "Acompanhamento",
    // Observabilidade fica ao lado do Dashboard, e não dentro dele: a
    // diferença não é o nome, é o eixo (ADR 0016). Dashboard responde
    // "como está agora"; Observabilidade, "o que mudou e por quê".
    // Fundir as duas produz uma tela que não serve bem a ninguém.
    keys: ["dashboard", "observability", "defects", "todos", "audit"],
  },
];

// Vazio desde a change 0158: Requisitos ganhou o grupo "Negócio" acima. A
// constante fica porque o topo do menu é onde o próximo item de fluxo entra —
// e porque tirá-la e recolocá-la depois custa mais do que mantê-la.
const NAV_LOOSE_TOP: Tab[] = [];

// Itens sem grupo, entre o trabalho do dia e o que foi congelado.
// "Ferramentas" tinha UM item: um cabeçalho para um item ocupa uma linha
// inteira para dizer o que o próprio item já diz (change 0129).
const NAV_LOOSE: Tab[] = ["ia"];

// As capabilities congeladas (ADR 0012) vêm por último, antes do rodapé:
// continuam alcançáveis e fora do caminho de quem usa o produto para o que
// ele é.
const NAV_FROZEN_GROUP = {
  title: "Mais",
  keys: ["decisions", "memory", "daily", "meetings", "migration"] as Tab[],
};

// Rodapé da navegação: o que é de manutenção, não de trabalho do dia, fica
// ancorado embaixo depois de uma régua — não compete com a regressão de
// hoje. `profile` NÃO entra: é da pessoa e mora no menu do avatar desde a
// change 0110; repeti-lo aqui era navegação duplicada.
const NAV_FOOTER: Tab[] = ["problems", "admin"];

// Capabilities congeladas: o grupo "Mais" nasce recolhido, e cada item leva
// a marca para que ninguém confunda "está aqui" com "é para usar".
const FROZEN_TABS: Tab[] = [
  "decisions", "memory", "daily", "meetings", "migration",
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

/**
 * Um módulo que o administrador desligou (ADR 0014).
 *
 * O interruptor tem que significar a mesma coisa nas três camadas. O
 * servidor já recusa os caminhos do módulo com 403; aqui a TELA deixa de
 * montar, em vez de abrir com todos os botões e falhar no primeiro envio.
 * Não é uma mensagem de erro: nada quebrou, esta instância só não usa isso.
 */
function ModuleOff({
  label,
  isAdmin,
  onHome,
  onAdmin,
}: {
  label: string;
  isAdmin: boolean;
  onHome: () => void;
  onAdmin: () => void;
}) {
  return (
    <div className="empty-state block">
      <div className="empty-art" aria-hidden="true">
        <NavIcon name="admin" />
      </div>
      <div className="empty-title">{label} está desligado nesta instância</div>
      <div className="empty-body">
        O administrador desligou este módulo. Ele não aparece no menu e o
        servidor recusa as chamadas dele — não é uma falha, é uma escolha de
        quem administra o Arbites aqui.
      </div>
      <div className="empty-actions">
        <button className="primary" onClick={onHome}>
          Voltar para Hoje
        </button>
        {isAdmin && <button onClick={onAdmin}>Ligar em Administração</button>}
      </div>
    </div>
  );
}

function NavItem({
  item,
  tab,
  setTab,
  problemCount,
  pinned,
  onTogglePin,
  live = false,
  frozen = false,
}: {
  item: { key: Tab; label: string };
  tab: Tab;
  setTab: (t: Tab) => void;
  problemCount: number;
  pinned: boolean;
  onTogglePin: () => void;
  // indicador "algo executando" (0076): dot pulsante no item
  live?: boolean;
  // capability congelada (ADR 0012): funciona, mas não recebe investimento
  frozen?: boolean;
}) {
  return (
    <div className={`nav-row ${tab === item.key ? "active" : ""}`}>
      <button
        className={`nav-item ${tab === item.key ? "active" : ""} ${
          frozen ? "frozen" : ""
        }`}
        title={
          frozen
            ? "Congelada: continua funcionando, mas fora do foco do produto"
            : undefined
        }
        onClick={() => setTab(item.key)}
        aria-current={tab === item.key ? "page" : undefined}
      >
        <NavIcon name={item.key} />
        <span className="nav-item-label">{item.label}</span>
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

export default function App({
  user,
  onLogout,
}: {
  user: SessionUser;
  onLogout: () => void;
}) {
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
    // Navegar fecha a gaveta: num celular ela cobre a tela, e deixá-la
    // aberta esconderia justamente o que a pessoa acabou de pedir.
    setNavOpen(false);
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
  const [switches, setSwitches] = useState<Switch[]>([]);
  // sem isto a tela de um modulo desligado PISCA antes de sumir: no
  // primeiro render a lista ainda esta vazia e tudo parece ligado
  const [switchesLoaded, setSwitchesLoaded] = useState(false);
  const [tree, setTree] = useState<TreeNode | null>(null);
  const [warnings, setWarnings] = useState<Warning[]>([]);
  const [selectedCt, setSelectedCt] = useState<string | null>(null);
  const [selectedReq, setSelectedReq] = useState<string | null>(null);
  const [selectedExec, setSelectedExec] = useState<string | null>(null);
  const [selectedDefect, setSelectedDefect] = useState<string | null>(null);
  const [selectedDecision, setSelectedDecision] = useState<string | null>(null);
  const [execCreating, setExecCreating] = useState(false);
  // modo guiado (change 0113): complementa o Kanban, não o substitui
  const [execGuided, setExecGuided] = useState(false);
  // Gaveta de navegação em tela estreita (change 0125). A lateral sai do
  // fluxo em vez de comer 240px de uma tela de 390.
  const [navOpen, setNavOpen] = useState(false);
  const navToggle = useRef<HTMLButtonElement>(null);
  const [cmdkOpen, setCmdkOpen] = useState(false);
  // runs de automação ativos → dot pulsante no item Automação (0076)
  const [activeRuns, setActiveRuns] = useState(0);
  const [reqVersion, setReqVersion] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [reindexing, setReindexing] = useState(false);
  const [creatingCt, setCreatingCt] = useState(false);
  const [pins, setPins] = useState<Tab[]>(() => loadJson<Tab[]>("arbites.pins", []));
  const [collapsed, setCollapsed] = useState<string[]>(() =>
    loadJson<string[]>("arbites.navCollapsed", ["Mais"]),
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

  /**
   * Leva para a ORIGEM de uma notificação (change 0161).
   *
   * Quando o alvo traz um ID, cai no item; quando traz só a aba, cai na aba.
   * Parar na lista e obrigar a procurar de novo é metade de um link — e o
   * pedido era justamente poder clicar e chegar onde a coisa está.
   */
  const goToTarget = useCallback(
    (target: { tab: string; id?: string; run?: string; atab?: string }) => {
      if (target.id) {
        navigateTo(target.id);
        if (target.tab) setTab(target.tab as Tab);
        setNavOpen(false);
        return;
      }
      setTab(target.tab as Tab);
      setHashParams(target.atab ? { atab: target.atab } : {});
      setNavOpen(false);
    },
    [navigateTo],
  );

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

  // Uma aba so aparece quando o papel alcanca e o admin nao desligou. Sem
  // isto a UI oferece caminhos que a API vai recusar com 403.
  //
  // O modulo desligado (ADR 0014) some do menu E nao monta a tela: quem tem
  // o link na mao nao abre mais um formulario inteiro para descobrir no
  // primeiro envio que a feature nao existe nesta instancia. A lista de
  // modulos vem do SERVIDOR — a mesma que gera o bloqueio no gate —, entao o
  // que a UI esconde e o que o servidor recusa nao tem como divergir.
  const moduleOffFor = (key: Tab): Switch | undefined =>
    switches.find((s) => s.kind === "module" && s.tab === key && !s.enabled);

  const isReachable = (key: Tab): boolean => {
    if (moduleOffFor(key)) return false;
    if (key === "admin") return user.role === "admin";
    if (key === "migration") return user.role === "admin";
    return true;
  };

  const loadSwitches = useCallback(() => {
    api
      .switches()
      .then((r) => setSwitches(r.switches))
      .catch(() => setSwitches([]))
      .finally(() => setSwitchesLoaded(true));
  }, []);

  useEffect(() => {
    loadSwitches();
    // O painel vive em outro componente e não tem como avisar a casca por
    // prop: sem este canal, o admin desligava um módulo e o menu só mudava
    // no próximo carregamento da página — com o item ainda clicável nesse
    // meio-tempo. Um evento do documento é o canal mais barato aqui, e o
    // estado continua vindo do SERVIDOR (o evento só diz "releia").
    window.addEventListener(SWITCHES_CHANGED, loadSwitches);
    return () => window.removeEventListener(SWITCHES_CHANGED, loadSwitches);
  }, [loadSwitches]);

  // Esc fecha a gaveta e devolve o foco a quem a abriu: sem isso o teclado
  // volta para o topo do documento e a pessoa se perde.
  useEffect(() => {
    if (!navOpen) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setNavOpen(false);
        navToggle.current?.focus();
      }
    }
    document.addEventListener("keydown", onKey);
    // trava a rolagem do conteúdo atrás da gaveta
    const antes = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = antes;
    };
  }, [navOpen]);

  return (
    <>
      <header className="app-header">
        <button
          ref={navToggle}
          className="nav-toggle"
          onClick={() => setNavOpen((v) => !v)}
          aria-label={navOpen ? "Fechar menu" : "Abrir menu"}
          aria-expanded={navOpen}
        >
          <span aria-hidden="true">☰</span>
        </button>
        <span className="brand">Arbites</span>
        {/* `wide-only`: contadores e reindexar são controles de quem administra
            a instância sentado numa mesa — não de quem abre o celular para ver
            como está a regressão (change 0125). O caminho no disco virou dica
            aqui: é informação de instalação, consultada uma vez por mês, e não
            merecia espaço fixo no topo de toda tela (change 0130). */}
        <span className="meta wide-only" title={workspace?.root ?? undefined}>
          {workspace?.config.workspace?.name ?? "…"} ·{" "}
          {workspace?.index.testcases ?? 0} CTs · {workspace?.index.requirements ?? 0}{" "}
          requisitos
        </span>
        <span className="spacer" />
        <button className="cmdk-trigger" onClick={() => setCmdkOpen(true)}>
          <span>Buscar…</span>
          <kbd>Ctrl K</kbd>
        </button>
        <Suspense fallback={null}>
          <NotificationBell onGo={goToTarget} onError={setError} />
        </Suspense>
        <button
          className="header-icon-btn wide-only"
          onClick={() => void reindex()}
          disabled={reindexing}
          title={reindexing ? "Reindexando…" : "Reindexar o índice do workspace"}
          aria-label="Reindexar"
        >
          <NavIcon name="reindex" />
        </button>
        <AccountMenu
          user={user}
          onProfile={() => selectTab("profile")}
          onAdmin={() => selectTab("admin")}
          onLogout={onLogout}
        />
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
      <div className={`app-body ${navOpen ? "nav-open" : ""}`}>
        {/* O fundo escurecido é o alvo do "toque fora" — num celular o gesto
            de fechar varia, e nenhum deles é o óbvio para todo mundo. */}
        {navOpen && (
          <div
            className="nav-backdrop"
            onClick={() => setNavOpen(false)}
            aria-hidden="true"
          />
        )}
        <aside className="sidebar">
          <nav className="nav">
            <div className="nav-group">
              <button
                className={`nav-item ${tab === "home" ? "active" : ""}`}
                onClick={() => selectTab("home")}
                aria-current={tab === "home" ? "page" : undefined}
              >
                <NavIcon name="home" />
                <span className="nav-item-label">Hoje</span>
              </button>
            </div>
            {pins.length > 0 && (
              <div className="nav-group">
                <div className="nav-group-title">
                  <span>Acesso rápido</span>
                </div>
                {pins
                  .filter((k) => NAV_BY_KEY[k] && isReachable(k))
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
            {/* Insumo do negócio, antes do trabalho de QA (0152). */}
            <div className="nav-group">
              {NAV_LOOSE_TOP.filter(isReachable).map((k) => (
                <NavItem
                  key={k}
                  item={NAV_BY_KEY[k]}
                  tab={tab}
                  setTab={selectTab}
                  problemCount={problemCount}
                  pinned={pins.includes(k)}
                  onTogglePin={() => togglePin(k)}
                />
              ))}
            </div>
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
                  group.keys.filter(isReachable).map((k) => (
                    <NavItem
                      key={k}
                      item={NAV_BY_KEY[k]}
                      tab={tab}
                      setTab={selectTab}
                      problemCount={problemCount}
                      pinned={pins.includes(k)}
                      onTogglePin={() => togglePin(k)}
                      live={k === "automation" && activeRuns > 0}
                      frozen={FROZEN_TABS.includes(k)}
                    />
                  ))}
              </div>
            ))}

            {/* Item sem grupo: um cabeçalho para um item só é ruído. */}
            <div className="nav-group">
              {NAV_LOOSE.filter(isReachable).map((k) => (
                <NavItem
                  key={k}
                  item={NAV_BY_KEY[k]}
                  tab={tab}
                  setTab={selectTab}
                  problemCount={problemCount}
                  pinned={pins.includes(k)}
                  onTogglePin={() => togglePin(k)}
                  frozen={FROZEN_TABS.includes(k)}
                />
              ))}
            </div>

            <div className="nav-group">
              <button
                className="nav-group-title"
                onClick={() => toggleGroup(NAV_FROZEN_GROUP.title)}
                aria-expanded={!collapsed.includes(NAV_FROZEN_GROUP.title)}
              >
                <span>{NAV_FROZEN_GROUP.title}</span>
                <span className="nav-chevron">
                  {collapsed.includes(NAV_FROZEN_GROUP.title) ? "▸" : "▾"}
                </span>
              </button>
              {!collapsed.includes(NAV_FROZEN_GROUP.title) &&
                NAV_FROZEN_GROUP.keys.filter(isReachable).map((k) => (
                  <NavItem
                    key={k}
                    item={NAV_BY_KEY[k]}
                    tab={tab}
                    setTab={selectTab}
                    problemCount={problemCount}
                    pinned={pins.includes(k)}
                    onTogglePin={() => togglePin(k)}
                    live={k === "automation" && activeRuns > 0}
                    frozen={FROZEN_TABS.includes(k)}
                  />
                ))}
            </div>

            {/* Rodapé ancorado: manutenção não compete com o trabalho do dia. */}
            <div className="nav-footer">
              {NAV_FOOTER.filter(isReachable).map((k) => (
                <NavItem
                  key={k}
                  item={NAV_BY_KEY[k]}
                  tab={tab}
                  setTab={selectTab}
                  problemCount={problemCount}
                  pinned={pins.includes(k)}
                  onTogglePin={() => togglePin(k)}
                  frozen={FROZEN_TABS.includes(k)}
                />
              ))}
            </div>
          </nav>
        </aside>
        <main className="main">
          <div className="main-inner">
          {error && <div className="error-banner">{error}</div>}
          <ErrorBoundary key={tab}>
          {/* GUARDA DE ROTA (ADR 0014). Antes, `isReachable` decidia só o
              MENU: o link `#/ia` de um módulo desligado montava a tela
              inteira e a pessoa só descobria no primeiro envio. Aqui o
              módulo desligado não monta nada.

              `switchesLoaded` evita o pisca-pisca: no primeiro render a
              lista ainda está vazia e tudo pareceria ligado. O núcleo
              (`home`) nunca é guardado, senão a espera deixaria a tela
              inicial em branco. */}
          {tab !== "home" && !switchesLoaded ? (
            <p className="empty">Carregando…</p>
          ) : moduleOffFor(tab) ? (
            <ModuleOff
              label={moduleOffFor(tab)!.label}
              isAdmin={user.role === "admin"}
              onHome={() => selectTab("home")}
              onAdmin={() => selectTab("admin")}
            />
          ) : tab === "home" ? (
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
          ) : tab === "observability" ? (
            <Suspense fallback={<p className="empty">Carregando observabilidade…</p>}>
              <Observability onError={setError} />
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
              <AiAssist
                onChanged={() => void refresh()}
                onError={setError}
                isAdmin={user.role === "admin"}
              />
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
              <Audit onError={setError} isAdmin={user.role === "admin"} />
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
              <Profile user={user} onError={setError} />
            </Suspense>
          ) : tab === "admin" ? (
            <Suspense fallback={<p className="empty">Carregando administração…</p>}>
              <Admin currentUserId={user.id} />
            </Suspense>
          ) : tab === "migration" ? (
            <Suspense fallback={<p className="empty">Carregando migração…</p>}>
              <XrayImport onImported={() => void refresh()} onError={setError} />
            </Suspense>
          ) : tab === "executions" ? (
            execGuided ? (
              <Suspense fallback={<p className="empty">Carregando modo guiado…</p>}>
                <div className="back-bar">
                  <button onClick={() => setExecGuided(false)}>← Voltar</button>
                  <span className="crumbs caption">
                    <span className="muted">Execuções</span>
                    <span className="crumb-sep">/</span>
                    <span>modo guiado</span>
                  </span>
                </div>
                <ExecutionGuided
                  initialId={selectedExec}
                  onChanged={refresh}
                  onError={setError}
                />
              </Suspense>
            ) : execCreating ? (
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
                <ExecutionBoard
                  id={selectedExec}
                  onChanged={refresh}
                  onError={setError}
                  onGuided={() => setExecGuided(true)}
                />
              </Suspense>
            ) : (
              <Suspense fallback={<p className="empty">Carregando execuções…</p>}>
                <ExecutionsRepo
                  version={reqVersion}
                  onGuided={() => setExecGuided(true)}
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
                  onNavigate={navigateTo}
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
