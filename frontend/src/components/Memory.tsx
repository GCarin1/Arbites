import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { TimelineEntry } from "../types";

const KIND_LABEL: Record<string, string> = {
  requirement: "Requisito",
  defect: "Defeito",
  lesson: "Lição aprendida",
  decision: "Decisão",
  agent: "Agente de IA",
};

const KIND_DOT: Record<string, string> = {
  requirement: "dot-col-in_progress",
  defect: "dot-col-failed",
  lesson: "dot-col-blocked",
  decision: "dot-col-passed",
  agent: "dot-col-pending",
};

const ALL_KINDS = ["requirement", "defect", "lesson", "decision", "agent"];
const NAVIGABLE = new Set(["requirement", "defect", "decision"]);

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

/**
 * Memória Histórica do Projeto — linha do tempo estilo git log cruzando
 * requisitos, defeitos, lições aprendidas, decisões arquiteturais e
 * interações de agentes de IA. Decisões e lições recentes também são
 * injetadas no contexto das chamadas de IA que geram conteúdo (ver
 * `_with_project_recap` no backend) — a IA "lembra" do projeto conforme
 * ele cresce, não só o que está escrito na tela.
 */
export function Memory({
  onError,
  onNavigate,
}: {
  onError: (message: string) => void;
  onNavigate: (id: string) => void;
}) {
  const [events, setEvents] = useState<TimelineEntry[]>([]);
  const [kinds, setKinds] = useState<string[]>(ALL_KINDS);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    api
      .memoryTimeline(kinds.length === ALL_KINDS.length ? "" : kinds.join(","), 100)
      .then(setEvents)
      .catch((e) => onError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [kinds, onError]);

  useEffect(() => {
    load();
  }, [load]);

  function toggleKind(k: string) {
    setKinds((old) => (old.includes(k) ? old.filter((x) => x !== k) : [...old, k]));
  }

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Memória do Projeto</h1>
      </div>
      <div className="head-controls" style={{ marginBottom: 12, flexWrap: "wrap" }}>
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
      <p className="muted caption" style={{ marginBottom: 16 }}>
        Requisitos, defeitos, lições aprendidas, decisões arquiteturais e
        interações de agentes de IA, em ordem cronológica — como um
        histórico git, mas conversacional.
      </p>

      {loading ? (
        <p className="empty">Carregando linha do tempo…</p>
      ) : events.length === 0 ? (
        <div className="empty-state">
          <div className="empty-title">Nada por aqui ainda</div>
          <div className="empty-body">
            Conforme requisitos, defeitos, decisões e lições forem
            registrados — e a IA for usada para gerar ou revisar conteúdo —
            a história do projeto aparece aqui.
          </div>
        </div>
      ) : (
        <div className="memory-timeline">
          {events.map((e, i) => (
            <div key={`${e.kind}-${e.id}-${i}`} className="memory-entry">
              <span className={`status-dot ${KIND_DOT[e.kind]} memory-dot`} />
              <div className="memory-entry-body">
                <div className="memory-entry-head">
                  <span className="caption mono muted">{formatDate(e.at)}</span>
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
      )}
    </div>
  );
}
