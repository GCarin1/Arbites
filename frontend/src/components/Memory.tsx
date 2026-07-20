import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { TimelineEntry } from "../types";

const KIND_LABEL: Record<string, string> = {
  requirement: "Requisito",
  testcase: "Caso de teste",
  defect: "Defeito",
  lesson: "Lição aprendida",
  decision: "Decisão",
  agent: "Agente de IA",
  result: "Resultado de execução",
};

const KIND_DOT: Record<string, string> = {
  requirement: "dot-col-in_progress",
  testcase: "dot-col-in_progress",
  defect: "dot-col-failed",
  lesson: "dot-col-blocked",
  decision: "dot-col-passed",
  agent: "dot-col-pending",
  result: "dot-col-retest",
};

const ALL_KINDS = [
  "requirement", "testcase", "defect", "lesson", "decision", "agent", "result",
];
// `result` é verboso (cada transição de status) — começa DESLIGADO (opt-in)
const DEFAULT_KINDS = ALL_KINDS.filter((k) => k !== "result");
const NAVIGABLE = new Set(["requirement", "testcase", "defect", "decision", "result"]);

const MONTHS = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];
// quantos dias (grupos) mais recentes começam expandidos
const EXPANDED_DAYS = 3;

function formatDate(iso: string): string {
  if (!iso) return "—";
  try {
    if (iso.length <= 10) {
      const [y, m, d] = iso.split("-");
      return `${d}/${m}/${y}`;
    }
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function formatTime(iso: string): string {
  if (!iso || iso.length <= 10) return "";
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

/**
 * Memória Histórica do Projeto — linha do tempo estilo git log cruzando
 * requisitos, defeitos, lições aprendidas, decisões arquiteturais e
 * interações de agentes de IA. A timeline cresce muito num projeto maduro,
 * então os eventos são agrupados por DIA (cabeçalho colapsável) e filtráveis
 * por período (ano/mês), tipo e busca textual. Decisões e lições recentes
 * também alimentam o contexto das chamadas de IA (ver `_with_project_recap`
 * no backend).
 */
export function Memory({
  onError,
  onNavigate,
}: {
  onError: (message: string) => void;
  onNavigate: (id: string) => void;
}) {
  const [events, setEvents] = useState<TimelineEntry[]>([]);
  const [kinds, setKinds] = useState<string[]>(DEFAULT_KINDS);
  const [years, setYears] = useState<string[]>([]);
  const [year, setYear] = useState(""); // "" = todos os anos
  const [month, setMonth] = useState(""); // "" = todos os meses (1..12)
  const [search, setSearch] = useState("");
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  // recorte de período → date_from/date_to (YYYY-MM-DD, inclusivos)
  const range = useMemo(() => {
    if (!year) return { from: "", to: "" };
    if (!month) return { from: `${year}-01-01`, to: `${year}-12-31` };
    const mm = month.padStart(2, "0");
    const last = new Date(Number(year), Number(month), 0).getDate();
    return { from: `${year}-${mm}-01`, to: `${year}-${mm}-${String(last).padStart(2, "0")}` };
  }, [year, month]);

  useEffect(() => {
    api.memoryTimelineYears("").then(setYears).catch(() => {});
  }, []);

  const load = useCallback(() => {
    if (kinds.length === 0) {
      setEvents([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    // limit maior quando há recorte de período (a janela cabe no intervalo);
    // sem período, mostra os mais recentes. Lista de kinds sempre explícita:
    // o default do backend exclui `result`, então "" não seria "os marcados".
    api
      .memoryTimeline(kinds.join(","), year ? 200 : 100, range.from, range.to)
      .then(setEvents)
      .catch((e) => onError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [kinds, year, range.from, range.to, onError]);

  useEffect(() => {
    load();
  }, [load]);

  // ao recarregar, colapsa os dias além dos N mais recentes (por padrão)
  useEffect(() => {
    const days: string[] = [];
    for (const e of events) {
      const d = (e.at || "").slice(0, 10) || "—";
      if (!days.includes(d)) days.push(d);
    }
    setCollapsed(new Set(days.slice(EXPANDED_DAYS)));
  }, [events]);

  function toggleKind(k: string) {
    setKinds((old) => (old.includes(k) ? old.filter((x) => x !== k) : [...old, k]));
  }

  function toggleDay(day: string) {
    setCollapsed((old) => {
      const next = new Set(old);
      if (next.has(day)) next.delete(day);
      else next.add(day);
      return next;
    });
  }

  // filtro de busca (client-side) + agrupamento por dia; `events` já vem
  // ordenado do mais recente para o mais antigo, então a ordem dos dias
  // segue naturalmente decrescente.
  const groups = useMemo(() => {
    const q = search.trim().toLowerCase();
    const map = new Map<string, TimelineEntry[]>();
    for (const e of events) {
      if (q && !`${e.id} ${e.title} ${e.summary}`.toLowerCase().includes(q)) continue;
      const day = (e.at || "").slice(0, 10) || "—";
      const bucket = map.get(day);
      if (bucket) bucket.push(e);
      else map.set(day, [e]);
    }
    return [...map.entries()];
  }, [events, search]);

  const allDays = groups.map(([d]) => d);
  const allExpanded = allDays.every((d) => !collapsed.has(d));

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Memória do Projeto</h1>
      </div>
      <p className="subtitle">
        Requisitos, defeitos, lições aprendidas, decisões arquiteturais e
        interações de agentes de IA, em ordem cronológica — como um histórico
        git, mas conversacional. Agrupada por dia; filtre por período, tipo ou
        texto.
      </p>

      <div className="memory-filters block">
        <div className="head-controls" style={{ flexWrap: "wrap" }}>
          <label className="caption memory-filter">
            Ano
            <select value={year} onChange={(e) => { setYear(e.target.value); if (!e.target.value) setMonth(""); }}>
              <option value="">Todos</option>
              {years.map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </label>
          <label className="caption memory-filter">
            Mês
            <select value={month} onChange={(e) => setMonth(e.target.value)} disabled={!year}>
              <option value="">Todos</option>
              {MONTHS.map((m, i) => (
                <option key={m} value={String(i + 1)}>{m}</option>
              ))}
            </select>
          </label>
          <input
            className="memory-search"
            placeholder="Buscar por id, título ou resumo…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="head-controls" style={{ flexWrap: "wrap", marginTop: 8 }}>
          {ALL_KINDS.map((k) => (
            <label key={k} className="caption memory-kind-toggle">
              <input
                type="checkbox"
                checked={kinds.includes(k)}
                onChange={() => toggleKind(k)}
              />
              {KIND_LABEL[k]}
            </label>
          ))}
        </div>
      </div>

      {loading ? (
        <p className="empty">Carregando linha do tempo…</p>
      ) : groups.length === 0 ? (
        <div className="empty-state">
          <div className="empty-title">Nada por aqui ainda</div>
          <div className="empty-body">
            {events.length > 0
              ? "Nenhum evento casa com a busca/filtros atuais — ajuste o período, os tipos ou o texto."
              : "Conforme requisitos, defeitos, decisões e lições forem registrados — e a IA for usada para gerar ou revisar conteúdo — a história do projeto aparece aqui."}
          </div>
        </div>
      ) : (
        <>
          <div className="head-controls" style={{ marginBottom: 8 }}>
            <span className="caption muted">
              {groups.reduce((n, [, evs]) => n + evs.length, 0)} evento(s) ·{" "}
              {groups.length} dia(s)
            </span>
            <span className="spacer" />
            <button
              className="btn-sm"
              onClick={() => setCollapsed(allExpanded ? new Set(allDays) : new Set())}
            >
              {allExpanded ? "Recolher tudo" : "Expandir tudo"}
            </button>
          </div>
          <div className="memory-timeline">
            {groups.map(([day, dayEvents]) => {
              const isCollapsed = collapsed.has(day);
              return (
                <div key={day} className="memory-day">
                  <button
                    type="button"
                    className="memory-day-head"
                    aria-expanded={!isCollapsed}
                    onClick={() => toggleDay(day)}
                  >
                    <span className="memory-day-caret">{isCollapsed ? "▶" : "▼"}</span>
                    <span className="memory-day-date">{formatDate(day)}</span>
                    <span className="caption muted">
                      {dayEvents.length} evento{dayEvents.length === 1 ? "" : "s"}
                    </span>
                  </button>
                  {!isCollapsed &&
                    dayEvents.map((e, i) => (
                      <div key={`${e.kind}-${e.id}-${i}`} className="memory-entry">
                        <span className={`status-dot ${KIND_DOT[e.kind]} memory-dot`} />
                        <div className="memory-entry-body">
                          <div className="memory-entry-head">
                            {formatTime(e.at) && (
                              <span className="caption mono muted">{formatTime(e.at)}</span>
                            )}
                            <span className="caption muted">{KIND_LABEL[e.kind]}</span>
                            {NAVIGABLE.has(e.kind) ? (
                              <button
                                type="button"
                                className="link-chip mono link-chip-btn"
                                onClick={() => onNavigate(e.id)}
                              >
                                {e.id}
                              </button>
                            ) : (
                              <span className="mono muted">{e.id}</span>
                            )}
                          </div>
                          <div className="memory-entry-title">{e.title}</div>
                          <div className="memory-entry-summary caption">{e.summary}</div>
                        </div>
                      </div>
                    ))}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
