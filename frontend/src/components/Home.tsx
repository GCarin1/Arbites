import { useEffect, useState, type ReactNode } from "react";
import { api } from "../api";
import type {
  Defect,
  ExecutionSummary,
  Todo,
  Warning,
  WorkspaceInfo,
} from "../types";

const today = () => new Date().toISOString().slice(0, 10);

const SEV_DOT: Record<string, string> = {
  critical: "dot-col-failed",
  high: "dot-col-failed",
  medium: "dot-col-blocked",
  low: "dot-col-pending",
};

function fmtWhen(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString([], {
      day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

/**
 * Tela "Hoje" (0080) — landing de orientação diária. Compõe o estado
 * operacional do dia a partir de endpoints que já existem (nada de
 * agregador novo no backend). Cada card busca sua fonte de forma isolada:
 * a falha de UMA fonte não derruba a tela — o card só fica com um "—".
 */
export function Home({
  workspace,
  warnings,
  onNavigate,
  onOpen,
}: {
  workspace: WorkspaceInfo | null;
  warnings: Warning[];
  onNavigate: (id: string) => void;
  onOpen: (tab: string) => void;
}) {
  const [runs, setRuns] = useState<{ exec_id: string; target: string; status: string }[] | null>(null);
  const [execs, setExecs] = useState<ExecutionSummary[] | null>(null);
  const [defects, setDefects] = useState<Defect[] | null>(null);
  const [todos, setTodos] = useState<Todo[] | null>(null);
  const [dailyDone, setDailyDone] = useState<boolean | null>(null);

  // fetch isolado por fonte — catch mantém o estado em null (card fica "—")
  useEffect(() => {
    api.runsActive().then((r) => setRuns(r.runs)).catch(() => setRuns(null));
    api.executions().then(setExecs).catch(() => setExecs(null));
    api.defects("?status=open").then(setDefects).catch(() => setDefects(null));
    api.todos().then(setTodos).catch(() => setTodos(null));
    api.getDaily(today()).then(() => setDailyDone(true)).catch(() => setDailyDone(false));
  }, []);

  const idx = workspace?.index;
  const firstUse = !!idx && idx.requirements === 0 && idx.testcases === 0;

  if (firstUse) {
    return (
      <div>
        <div className="page-head">
          <h1 className="page-title">Hoje</h1>
        </div>
        <div className="empty-state">
          <div className="empty-title">Bem-vindo ao Arbites</div>
          <div className="empty-body">
            Seu workspace está vazio. Comece a cadeia de rastreabilidade:
            crie um <strong>epic</strong>, depois uma <strong>story</strong>{" "}
            dentro dele e um <strong>caso de teste</strong> vinculado.
            <div className="step-row" style={{ marginTop: 12 }}>
              <button className="primary" onClick={() => onOpen("requirements")}>
                Criar requisito
              </button>
              <button onClick={() => onOpen("testcases")}>Ir para test cases</button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // afazeres do dia: não-concluídos, vencidos ou para hoje (due <= hoje)
  const dueList = (todos ?? [])
    .filter((t) => t.status !== "done" && t.due && t.due <= today())
    .sort((a, b) => (a.due ?? "").localeCompare(b.due ?? ""));
  const blockedCount = (todos ?? []).filter((t) => t.status === "blocked").length;
  const openDefects = defects ?? [];
  const recentExecs = (execs ?? []).slice(0, 5);

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Hoje</h1>
        <span className="spacer" />
        <span className="caption muted">
          {workspace?.config?.workspace?.name ?? "workspace"} ·{" "}
          {idx?.last_reindex ? `indexado ${fmtWhen(idx.last_reindex)}` : "sem reindex"}
        </span>
      </div>
      <p className="subtitle">
        Situação do dia — runs, afazeres, defeitos, execuções recentes e a
        daily. Cada bloco abre a aba correspondente.
      </p>

      <div className="home-grid">
        {/* Automação rodando agora */}
        <HomeCard title="Automação" onOpen={() => onOpen("automation")}>
          {runs === null ? (
            <p className="caption muted">indisponível</p>
          ) : runs.length === 0 ? (
            <p className="caption muted">nenhuma automação rodando</p>
          ) : (
            runs.map((r) => (
              <button
                key={r.exec_id}
                type="button"
                className="home-row"
                onClick={() => onNavigate(r.exec_id)}
              >
                <span className="status-dot dot-col-in_progress home-pulse" />
                <span className="mono">{r.exec_id}</span>
                <span className="caption muted">{r.target}</span>
                <span className="spacer" />
                <span className="caption">{r.status}</span>
              </button>
            ))
          )}
        </HomeCard>

        {/* Afazeres do dia */}
        <HomeCard
          title="Afazeres de hoje"
          count={dueList.length}
          onOpen={() => onOpen("todos")}
        >
          {todos === null ? (
            <p className="caption muted">indisponível</p>
          ) : (
            <>
              {blockedCount > 0 && (
                <p className="caption">
                  <span className="status-dot dot-col-blocked" />
                  {blockedCount} impedimento{blockedCount === 1 ? "" : "s"}
                </p>
              )}
              {dueList.length === 0 ? (
                <p className="caption muted">nada vencido ou para hoje</p>
              ) : (
                dueList.slice(0, 6).map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    className="home-row"
                    onClick={() => onNavigate(t.id)}
                  >
                    <span
                      className={`status-dot ${
                        t.due && t.due < today() ? "dot-col-failed" : "dot-col-in_progress"
                      }`}
                    />
                    <span className="home-row-title">{t.title}</span>
                    <span className="spacer" />
                    <span className="caption mono muted">{t.due}</span>
                  </button>
                ))
              )}
            </>
          )}
        </HomeCard>

        {/* Defeitos abertos */}
        <HomeCard
          title="Defeitos abertos"
          count={openDefects.length}
          onOpen={() => onOpen("defects")}
        >
          {defects === null ? (
            <p className="caption muted">indisponível</p>
          ) : openDefects.length === 0 ? (
            <p className="caption muted">nenhum defeito aberto</p>
          ) : (
            openDefects.slice(0, 5).map((d) => (
              <button
                key={d.id}
                type="button"
                className="home-row"
                onClick={() => onNavigate(d.id)}
              >
                <span className={`status-dot ${SEV_DOT[d.severity ?? ""] ?? "dot-col-pending"}`} />
                <span className="mono">{d.id}</span>
                <span className="home-row-title">{d.title}</span>
              </button>
            ))
          )}
        </HomeCard>

        {/* Últimas execuções */}
        <HomeCard title="Execuções recentes" onOpen={() => onOpen("executions")}>
          {execs === null ? (
            <p className="caption muted">indisponível</p>
          ) : recentExecs.length === 0 ? (
            <p className="caption muted">nenhuma execução ainda</p>
          ) : (
            recentExecs.map((e) => (
              <button
                key={e.id}
                type="button"
                className="home-row"
                onClick={() => onNavigate(e.id)}
              >
                <span
                  className={`status-dot ${
                    e.status === "closed" ? "dot-col-passed" : "dot-col-in_progress"
                  }`}
                />
                <span className="home-row-title">{e.name}</span>
                <span className="spacer" />
                <span className="caption mono muted">
                  {e.result_counts.passed ?? 0}✓ {e.result_counts.failed ?? 0}✗{" "}
                  {e.result_counts.blocked ?? 0}⊘
                </span>
              </button>
            ))
          )}
        </HomeCard>

        {/* Daily de hoje */}
        <HomeCard title="Daily de hoje" onOpen={() => onOpen("daily")}>
          {dailyDone === null ? (
            <p className="caption muted">indisponível</p>
          ) : dailyDone ? (
            <p className="caption">
              <span className="status-dot dot-col-passed" />
              registrada — clique para revisar
            </p>
          ) : (
            <p className="caption">
              <span className="status-dot dot-col-pending" />
              pendente — gerar a daily do dia
            </p>
          )}
        </HomeCard>

        {/* Problemas do workspace */}
        <HomeCard
          title="Problemas"
          count={warnings.length}
          onOpen={() => onOpen("problems")}
        >
          {warnings.length === 0 ? (
            <p className="caption muted">nenhum warning no índice</p>
          ) : (
            <p className="caption">
              <span className="status-dot dot-col-blocked" />
              {warnings.length} warning{warnings.length === 1 ? "" : "s"} de indexação
            </p>
          )}
        </HomeCard>
      </div>
    </div>
  );
}

function HomeCard({
  title,
  count,
  onOpen,
  children,
}: {
  title: string;
  count?: number;
  onOpen: () => void;
  children: ReactNode;
}) {
  return (
    <div className="card home-card">
      <div className="card-head">
        <button type="button" className="home-card-title" onClick={onOpen}>
          {title}
        </button>
        {count !== undefined && count > 0 && <span className="count">{count}</span>}
        <span className="spacer" />
        <button type="button" className="btn-sm" onClick={onOpen}>
          abrir →
        </button>
      </div>
      <div className="home-card-body">{children}</div>
    </div>
  );
}
