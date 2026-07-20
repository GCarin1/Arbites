import { useEffect, useState } from "react";
import { api } from "../api";
import { Modal } from "./Modal";
import type { StoryChain } from "../types";

// dot semântico do último resultado do CT
function resultDot(status: string | null | undefined): string {
  if (!status) return "dot-col-pending";
  if (status === "passed") return "dot-col-passed";
  if (status === "failed") return "dot-col-failed";
  return "dot-col-blocked"; // blocked/retest/outros
}

function fmt(iso: string | null): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString([], {
      day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

/**
 * Story 360 (0086) — a cadeia completa de uma story numa visão só:
 * Epic → Story → CTs (status de documento + último resultado + evidências +
 * execuções) → Defeitos. Só leitura; cada nó navega para a tela do item
 * (fechando o modal antes). Responde "essa história foi validada? qual
 * evidência comprova?".
 */
export function Story360({
  storyId,
  onClose,
  onNavigate,
}: {
  storyId: string;
  onClose: () => void;
  onNavigate: (id: string) => void;
}) {
  const [chain, setChain] = useState<StoryChain | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .requirementChain(storyId)
      .then((c) => alive && setChain(c))
      .catch((e) => alive && setError(e instanceof Error ? e.message : String(e)));
    return () => {
      alive = false;
    };
  }, [storyId]);

  function go(id: string) {
    onClose();
    onNavigate(id);
  }

  const s = chain?.summary;

  return (
    <Modal title={`Story 360 — ${storyId}`} onClose={onClose}>
      {error ? (
        <p className="field-error">{error}</p>
      ) : !chain ? (
        <p className="empty">Montando a cadeia…</p>
      ) : (
        <div className="s360">
          {/* Epic → Story no topo */}
          {chain.epic && (
            <button type="button" className="s360-node s360-epic" onClick={() => go(chain.epic!.id)}>
              <span className="mono muted">{chain.epic.id}</span>
              <span className="s360-title">{chain.epic.title}</span>
              <span className={`status-dot dot-${chain.epic.status} caption`}>
                {chain.epic.status}
              </span>
            </button>
          )}
          <div className="s360-node s360-story">
            <span className="mono muted">{chain.story.id}</span>
            <span className="s360-title">{chain.story.title}</span>
            <span className={`status-dot dot-${chain.story.status} caption`}>
              {chain.story.status}
            </span>
          </div>

          {/* resumo da cobertura semântica */}
          {s && (
            <div className="s360-summary">
              <span className="status-dot dot-col-passed caption">{s.passing} passando</span>
              <span className="status-dot dot-col-failed caption">{s.failing} com falha</span>
              <span className="status-dot dot-col-pending caption">{s.untested} não executados</span>
              <span className="spacer" />
              <span className="caption muted">
                {s.executions} execuç{s.executions === 1 ? "ão" : "ões"} · {s.evidences} evidência
                {s.evidences === 1 ? "" : "s"} · {s.defects} defeito{s.defects === 1 ? "" : "s"}
              </span>
            </div>
          )}

          {/* CTs da story, cada um com último resultado + execuções */}
          <h4 className="section-title">Casos de teste</h4>
          {chain.testcases.length === 0 ? (
            <p className="caption muted">Nenhum caso de teste vinculado a esta story.</p>
          ) : (
            chain.testcases.map((ct) => (
              <div key={ct.id} className="s360-ct">
                <button type="button" className="s360-node" onClick={() => go(ct.id)}>
                  <span className={`status-dot ${resultDot(ct.last_result?.status)}`} />
                  <span className="mono muted">{ct.id}</span>
                  <span className="s360-title">{ct.title}</span>
                  <span className="spacer" />
                  {ct.evidence_count > 0 && (
                    <span className="caption muted">
                      {ct.evidence_count} evidência{ct.evidence_count === 1 ? "" : "s"}
                    </span>
                  )}
                  <span className="caption">
                    {ct.last_result
                      ? `${ct.last_result.status} · ${fmt(ct.last_result.executed_at)}`
                      : "nunca executado"}
                  </span>
                </button>
                {ct.executions.length > 0 && (
                  <div className="s360-runs">
                    {ct.executions.map((e) => (
                      <button
                        key={`${ct.id}-${e.execution_id}`}
                        type="button"
                        className="s360-run"
                        onClick={() => go(e.execution_id)}
                      >
                        <span className={`status-dot ${resultDot(e.status)}`} />
                        <span className="mono">{e.execution_id}</span>
                        <span className="caption muted">{e.execution_name}</span>
                        <span className="spacer" />
                        <span className="caption mono muted">{fmt(e.executed_at)}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}

          {/* Defeitos vinculados */}
          {chain.defects.length > 0 && (
            <>
              <h4 className="section-title">Defeitos</h4>
              {chain.defects.map((d) => (
                <button key={d.id} type="button" className="s360-node" onClick={() => go(d.id)}>
                  <span
                    className={`status-dot ${
                      d.status === "closed" ? "dot-col-passed" : "dot-col-failed"
                    }`}
                  />
                  <span className="mono muted">{d.id}</span>
                  <span className="s360-title">{d.title}</span>
                  <span className="spacer" />
                  <span className="caption muted">
                    {d.severity ?? "—"} · {d.status}
                  </span>
                </button>
              ))}
            </>
          )}
        </div>
      )}
    </Modal>
  );
}
