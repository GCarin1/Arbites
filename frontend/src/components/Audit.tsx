import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { AuditFinding, AuditHistoryEntry, AuditReport } from "../types";

const SEVERITY_DOT: Record<string, string> = {
  bad: "dot-col-failed",
  warn: "dot-col-blocked",
  info: "dot-col-pending",
};

const SEVERITY_LABEL: Record<string, string> = {
  bad: "crítico",
  warn: "atenção",
  info: "info",
};

const CATEGORY_LABEL: Record<string, string> = {
  indexing: "Indexação",
  coverage: "Cobertura",
  defects: "Defeitos",
  automation: "Automação",
};

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

/**
 * Agente Auditor — consolida sinais já existentes no índice (warnings de
 * indexação, stories sem CT, defeitos esquecidos, automação quebrada) num
 * snapshot datado. Sem daemon: roda sob demanda ou "lazy" quando a última
 * rodada passa de `audit.auto_interval_hours` (default 24h).
 */
export function Audit({ onError }: { onError: (message: string) => void }) {
  const [report, setReport] = useState<AuditReport | null>(null);
  const [history, setHistory] = useState<AuditHistoryEntry[]>([]);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadHistory = useCallback(() => {
    api
      .auditHistory()
      .then(setHistory)
      .catch((e) => onError(e instanceof Error ? e.message : String(e)));
  }, [onError]);

  useEffect(() => {
    setLoading(true);
    api
      .auditLatest()
      .then((r) => {
        setReport(r);
        loadHistory();
      })
      .catch((e) => onError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runNow() {
    setRunning(true);
    try {
      const r = await api.runAudit();
      setReport(r);
      loadHistory();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  async function openRun(id: string) {
    try {
      const r = await api.audit(id);
      setReport(r);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  const grouped = new Map<string, AuditFinding[]>();
  for (const f of report?.findings ?? []) {
    const list = grouped.get(f.category) ?? [];
    list.push(f);
    grouped.set(f.category, list);
  }

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Agente Auditor</h1>
        <span className="spacer" />
        <div className="head-controls">
          <button className="primary" onClick={() => void runNow()} disabled={running}>
            {running ? "Auditando…" : "Auditar agora"}
          </button>
        </div>
      </div>

      {loading ? (
        <p className="empty">Carregando auditoria…</p>
      ) : !report ? (
        <p className="empty">Sem dados.</p>
      ) : (
        <>
          <div className="audit-summary">
            <span className="caption muted">
              Última rodada: {formatDate(report.ran_at)} ·{" "}
              {report.trigger === "auto" ? "automática" : "manual"}
            </span>
            <span className="spacer" />
            {(["bad", "warn", "info"] as const).map((sev) => (
              <span key={sev} className={`audit-badge audit-badge-${sev}`}>
                <span className={`status-dot ${SEVERITY_DOT[sev]}`} />
                {report.by_severity[sev] ?? 0} {SEVERITY_LABEL[sev]}
              </span>
            ))}
          </div>

          {report.findings.length === 0 ? (
            <div className="empty-state">
              <div className="empty-title">Tudo em dia</div>
              <div className="empty-body">
                Nenhum achado nesta rodada — sem warnings de indexação,
                stories descobertas, defeitos esquecidos ou automação
                quebrada.
              </div>
            </div>
          ) : (
            [...grouped.entries()].map(([category, items]) => (
              <div key={category} className="audit-category">
                <h2 className="audit-category-title">
                  {CATEGORY_LABEL[category] ?? category}
                </h2>
                <div className="table-wrap">
                  <table className="dense">
                    <thead>
                      <tr>
                        <th></th>
                        <th>Referência</th>
                        <th>Mensagem</th>
                        <th>Código</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((f, i) => (
                        <tr key={i}>
                          <td>
                            <span className={`status-dot ${SEVERITY_DOT[f.severity]}`} />
                          </td>
                          <td className="mono">{f.ref ?? "—"}</td>
                          <td>{f.message}</td>
                          <td className="mono muted">{f.code}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))
          )}

          {history.length > 1 && (
            <div className="audit-history">
              <h2 className="audit-category-title">Histórico</h2>
              <div className="table-wrap">
                <table className="dense">
                  <thead>
                    <tr>
                      <th>Rodada</th>
                      <th>Quando</th>
                      <th>Gatilho</th>
                      <th>Achados</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((h) => (
                      <tr
                        key={h.id}
                        className={h.id === report.id ? "row-active" : "row-clickable"}
                        onClick={() => void openRun(h.id)}
                      >
                        <td className="mono">{h.id}</td>
                        <td className="caption muted">{formatDate(h.ran_at)}</td>
                        <td className="caption muted">{h.trigger}</td>
                        <td>{h.total}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
