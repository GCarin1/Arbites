import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { ConfirmModal, Modal } from "./Modal";
import { OverflowMenu } from "./OverflowMenu";
import { useToast } from "./Toast";
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
export function Audit({
  onError,
  isAdmin,
}: {
  onError: (message: string) => void;
  // A UI segue o servidor, que já recusa com 403 (0151): sem isto, a opção
  // aparece para quem não pode e só falha quando clica.
  isAdmin: boolean;
}) {
  const [report, setReport] = useState<AuditReport | null>(null);
  const [history, setHistory] = useState<AuditHistoryEntry[]>([]);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [excluindo, setExcluindo] = useState<AuditHistoryEntry | null>(null);
  const [limpando, setLimpando] = useState(false);
  const { toast } = useToast();

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

  /** Exclui UMA rodada. Se for a que está aberta, volta para a mais recente
      — senão a tela fica mostrando um relatório que não existe mais. */
  async function excluirRodada(alvo: AuditHistoryEntry) {
    setExcluindo(null);
    try {
      await api.deleteAudit(alvo.id);
      toast(`${alvo.id} movida para a lixeira`);
      const restante = await api.auditHistory();
      setHistory(restante);
      if (report?.id === alvo.id) {
        if (restante.length > 0) await openRun(restante[0].id);
        else setReport(null);
      }
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  /** Limpeza em lote: a rodada automática enche o histórico sozinha, e
      excluir de uma em uma não dá conta disso. */
  async function limparAnteriores(before: string) {
    setLimpando(false);
    try {
      const r = await api.deleteAuditsBefore(before);
      toast(
        r.count === 0
          ? "Nenhuma rodada anterior a essa data"
          : `${r.count} rodada${r.count === 1 ? "" : "s"} para a lixeira`,
      );
      const restante = await api.auditHistory();
      setHistory(restante);
      if (report && r.removed.includes(report.id)) {
        if (restante.length > 0) await openRun(restante[0].id);
        else setReport(null);
      }
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
          {isAdmin && history.length > 1 && (
            <button onClick={() => setLimpando(true)}>Limpar antigas</button>
          )}
          <button className="primary" onClick={() => void runNow()} disabled={running}>
            {running ? "Auditando…" : "Auditar agora"}
          </button>
        </div>
      </div>
      <p className="subtitle block">
        Verificação automática de pendências do workspace: consolida problemas
        de indexação, stories sem caso de teste, defeitos abertos há muito
        tempo e automações quebradas. Roda quando você clica em "Auditar
        agora" — ou sozinha, no máximo uma vez a cada 24h ao abrir esta aba.
      </p>
      <div className="audit-legend caption muted block">
        <span className="status-dot dot-col-failed">bad — precisa de ação</span>
        <span className="status-dot dot-col-blocked">warn — vale atenção</span>
        <span className="status-dot dot-col-pending">info — contexto</span>
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
                Nenhuma pendência nesta rodada. Se algo surgir — uma story
                ficar sem caso de teste, um defeito envelhecer sem causa
                raiz, uma automação quebrar — o achado aparece aqui com a
                severidade e a referência do item.
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
                <table className="dense stack-narrow">
                  <thead>
                    <tr>
                      <th>Rodada</th>
                      <th>Quando</th>
                      <th>Gatilho</th>
                      <th>Achados</th>
                      {isAdmin && <th />}
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((h) => (
                      <tr
                        key={h.id}
                        className={h.id === report.id ? "row-active" : "row-clickable"}
                        onClick={() => void openRun(h.id)}
                      >
                        <td className="mono" data-label="Rodada">{h.id}</td>
                        <td className="caption muted" data-label="Quando">
                          {formatDate(h.ran_at)}
                        </td>
                        <td className="caption muted" data-label="Gatilho">
                          {h.trigger}
                        </td>
                        <td data-label="Achados">{h.total}</td>
                        {isAdmin && (
                          // o clique na linha ABRE a rodada; o que apaga não
                          // pode morar a um erro de mira disso (0131)
                          <td data-label="" onClick={(e) => e.stopPropagation()}>
                            <OverflowMenu label={`Ações de ${h.id}`}>
                              {(fechar) => (
                                <button
                                  className="danger"
                                  onClick={() => {
                                    fechar();
                                    setExcluindo(h);
                                  }}
                                >
                                  Excluir rodada
                                </button>
                              )}
                            </OverflowMenu>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {excluindo && (
        <ConfirmModal
          danger
          title="Excluir rodada de auditoria"
          message={
            <>
              Mover <span className="mono">{excluindo.id}</span> (
              {formatDate(excluindo.ran_at)}) para a lixeira? A rodada é um
              retrato do estado de qualidade naquele momento — de lá ela pode
              ser restaurada.
            </>
          }
          confirmLabel="Excluir rodada"
          onConfirm={() => void excluirRodada(excluindo)}
          onCancel={() => setExcluindo(null)}
        />
      )}

      {limpando && (
        <LimparAntigas
          onCancel={() => setLimpando(false)}
          onConfirm={(before) => void limparAnteriores(before)}
        />
      )}
    </div>
  );
}

/**
 * Limpeza em lote por data (change 0151).
 *
 * A rodada automática (uma a cada 24h ao abrir a aba) enche o histórico
 * sozinha; excluir de uma em uma não dá conta. A data é EXCLUSIVA: a rodada
 * exatamente dessa data não é levada — é o corte menos surpreendente.
 */
function LimparAntigas({
  onCancel,
  onConfirm,
}: {
  onCancel: () => void;
  onConfirm: (before: string) => void;
}) {
  // default: 30 dias atrás — sugestão, não decisão; a pessoa muda a data
  const trintaDias = new Date(Date.now() - 30 * 24 * 3600 * 1000)
    .toISOString()
    .slice(0, 10);
  const [data, setData] = useState(trintaDias);

  return (
    <Modal
      title="Limpar rodadas antigas"
      onClose={onCancel}
      footer={
        <>
          <button onClick={onCancel}>Cancelar</button>
          <button
            className="danger"
            disabled={!data}
            onClick={() => onConfirm(`${data}T00:00:00+00:00`)}
          >
            Mover para a lixeira
          </button>
        </>
      }
    >
      <p className="modal-text">
        Move para a lixeira todas as rodadas <strong>anteriores</strong> à data
        escolhida. A rodada exatamente dessa data fica.
      </p>
      <div className="modal-field">
        <label htmlFor="audit-antes">Anterior a</label>
        <input
          id="audit-antes"
          type="date"
          value={data}
          onChange={(e) => setData(e.target.value)}
        />
      </div>
    </Modal>
  );
}
