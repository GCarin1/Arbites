import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import { MentionTextarea, SingleRefInput } from "./Autocomplete";
import { ConfirmModal, Modal } from "./Modal";
import { useToast } from "./Toast";
import type { Defect } from "../types";

const STATUSES: Defect["status"][] = ["open", "fixed", "closed"];
const SEVERITIES = ["critical", "high", "medium", "low"];
// mesmo mapa de cor por severidade do painel de Dashboard (DefectsPanel).
const SEV_DOT: Record<string, string> = {
  critical: "dot-col-failed",
  high: "dot-col-failed",
  medium: "dot-col-blocked",
  low: "dot-col-pending",
};

function ageDays(openedAt: string | null): number | null {
  if (!openedAt) return null;
  const opened = new Date(openedAt).getTime();
  if (Number.isNaN(opened)) return null;
  return Math.max(0, Math.floor((Date.now() - opened) / 86400000));
}

/**
 * Gerenciamento de defeitos (doc §1.1/§1.5) — antes só dava pra criar um
 * defeito a partir de um resultado de execução; aqui é a lista completa,
 * com criação avulsa, edição, vínculo a CT/execução e exclusão.
 */
export function Defects({
  onError,
  onNavigate,
  openId,
  onOpened,
}: {
  onError: (message: string) => void;
  onNavigate: (id: string) => void;
  openId?: string | null;
  onOpened?: () => void;
}) {
  const [items, setItems] = useState<Defect[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [lessonOnly, setLessonOnly] = useState(false);
  const [editing, setEditing] = useState<Defect | "new" | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Defect | null>(null);

  const load = useCallback(() => {
    const params = new URLSearchParams();
    if (statusFilter) params.set("status", statusFilter);
    if (lessonOnly) params.set("has_lesson", "true");
    const q = params.toString() ? `?${params}` : "";
    api
      .defects(q)
      .then(setItems)
      .catch((e) => onError(e.message));
  }, [statusFilter, lessonOnly, onError]);

  useEffect(() => {
    load();
  }, [load]);

  // navegação por @DF-XXXX (menções/links) abre direto no editor
  useEffect(() => {
    if (!openId) return;
    api
      .defect(openId)
      .then((d) => {
        setEditing(d);
        onOpened?.();
      })
      .catch((e) => {
        onError(e instanceof Error ? e.message : String(e));
        onOpened?.();
      });
  }, [openId, onError, onOpened]);

  async function remove(defect: Defect) {
    setConfirmDelete(null);
    try {
      await api.deleteDefect(defect.id);
      load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function quickStatus(defect: Defect, status: string) {
    try {
      await api.updateDefect(defect.id, { status });
      load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  const visible = severityFilter
    ? items.filter((d) => d.severity === severityFilter)
    : items;

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Defeitos</h1>
        <span className="spacer" />
        <div className="head-controls">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">Todos os status</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
            <option value="">Toda severidade</option>
            {SEVERITIES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <label className="caption" style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <input
              type="checkbox"
              checked={lessonOnly}
              onChange={(e) => setLessonOnly(e.target.checked)}
            />
            Só com lição aprendida
          </label>
          <button className="primary" onClick={() => setEditing("new")}>
            Novo defeito
          </button>
        </div>
      </div>

      {visible.length === 0 ? (
        <div className="empty-state">
          <div className="empty-title">Nenhum defeito</div>
          <div className="empty-body">
            Registre defeitos aqui, ou crie um a partir de um resultado
            "failed" numa execução — os dois caminhos levam ao mesmo lugar.
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="dense">
            <thead>
              <tr>
                <th>ID</th>
                <th>Título</th>
                <th>Severidade</th>
                <th>Status</th>
                <th>CT</th>
                <th>Execução</th>
                <th>Chave externa</th>
                <th>Aberto há</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {visible.map((d) => {
                const age = ageDays(d.opened_at);
                return (
                  <tr key={d.id}>
                    <td className="mono">{d.id}</td>
                    <td>
                      {d.title}
                      {(d.root_cause || d.fix || d.prevention) && (
                        <span
                          className="status-dot dot-col-in_progress caption"
                          title="Tem lição aprendida (causa/correção/prevenção)"
                          style={{ marginLeft: 6 }}
                        >
                          lição
                        </span>
                      )}
                    </td>
                    <td>
                      <span
                        className={`status-dot ${SEV_DOT[d.severity ?? ""] ?? "dot-col-pending"} caption`}
                      >
                        {d.severity ?? "—"}
                      </span>
                    </td>
                    <td>
                      <select
                        className="status-select"
                        value={d.status}
                        onChange={(e) => void quickStatus(d, e.target.value)}
                        aria-label="Status"
                      >
                        {STATUSES.map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      {d.testcase_id ? (
                        <button
                          type="button"
                          className="link-chip mono link-chip-btn"
                          onClick={() => onNavigate(d.testcase_id!)}
                        >
                          {d.testcase_id}
                        </button>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                    <td>
                      {d.execution_id ? (
                        <button
                          type="button"
                          className="link-chip mono link-chip-btn"
                          onClick={() => onNavigate(d.execution_id!)}
                        >
                          {d.execution_id}
                        </button>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                    <td className="mono muted">{d.external_key || "—"}</td>
                    <td className="caption mono">{age !== null ? `${age}d` : "—"}</td>
                    <td className="repo-actions">
                      <button className="btn-sm" onClick={() => setEditing(d)}>
                        Editar
                      </button>
                      <button className="btn-sm danger" onClick={() => setConfirmDelete(d)}>
                        Excluir
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <DefectModal
          defect={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
          onError={onError}
        />
      )}
      {confirmDelete && (
        <ConfirmModal
          title="Excluir defeito"
          message={
            <>
              Mover <span className="mono">{confirmDelete.id}</span> (
              {confirmDelete.title}) para a lixeira?
            </>
          }
          confirmLabel="Mover para a lixeira"
          danger
          onConfirm={() => void remove(confirmDelete)}
          onCancel={() => setConfirmDelete(null)}
        />
      )}
    </div>
  );
}

function DefectModal({
  defect,
  onClose,
  onSaved,
  onError,
}: {
  defect: Defect | null;
  onClose: () => void;
  onSaved: () => void;
  onError: (message: string) => void;
}) {
  const [title, setTitle] = useState(defect?.title ?? "");
  const [status, setStatus] = useState(defect?.status ?? "open");
  const [severity, setSeverity] = useState(defect?.severity ?? "medium");
  const [testcase, setTestcase] = useState(defect?.testcase_id ?? "");
  const [execution, setExecution] = useState(defect?.execution_id ?? "");
  const [externalKey, setExternalKey] = useState(defect?.external_key ?? "");
  const [body, setBody] = useState(defect?.body ?? "");
  const [rootCause, setRootCause] = useState(defect?.root_cause ?? "");
  const [fix, setFix] = useState(defect?.fix ?? "");
  const [prevention, setPrevention] = useState(defect?.prevention ?? "");
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (defect && defect.body === undefined) {
      api
        .defect(defect.id)
        .then((full) => setBody(full.body ?? ""))
        .catch(() => {});
    }
  }, [defect]);

  async function save() {
    if (!title.trim()) return;
    setSaving(true);
    const payload = {
      title: title.trim(),
      status,
      severity,
      testcase: testcase.trim() || null,
      execution: execution.trim() || null,
      external_key: externalKey.trim() || null,
      body,
      root_cause: rootCause.trim() || null,
      fix: fix.trim() || null,
      prevention: prevention.trim() || null,
    };
    try {
      if (defect) await api.updateDefect(defect.id, payload);
      else await api.createDefect(payload);
      toast("Defeito salvo");
      onSaved();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
      setSaving(false);
    }
  }

  return (
    <Modal
      title={defect ? `Editar ${defect.id}` : "Novo defeito"}
      onClose={onClose}
      dirty={dirty && !saving}
      initialFocus={titleRef}
      footer={
        <>
          <button onClick={onClose} disabled={saving}>
            Cancelar
          </button>
          <button className="primary" onClick={() => void save()} disabled={saving || !title.trim()}>
            {saving ? "Salvando…" : "Salvar"}
          </button>
        </>
      }
    >
      <div className="modal-form" onInput={() => setDirty(true)}>
      <div className="modal-field">
        <label htmlFor="defect-title">Título</label>
        <input
          id="defect-title"
          ref={titleRef}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Ex.: Botão de login não responde"
        />
      </div>
      <div className="field-grid">
        <div className="field col-3">
          <label>Status</label>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="field col-3">
          <label>Severidade</label>
          <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
            {SEVERITIES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="field col-6">
          <label>Chave externa (opcional)</label>
          <input
            className="mono"
            value={externalKey}
            onChange={(e) => setExternalKey(e.target.value)}
            placeholder="PROJ-123"
          />
        </div>
        <div className="field col-6">
          <label>Caso de teste vinculado (opcional)</label>
          <SingleRefInput
            value={testcase}
            onChange={setTestcase}
            kinds="testcase"
            placeholder="CT-0001 — digite para sugerir"
          />
        </div>
        <div className="field col-6">
          <label>Execução vinculada (opcional)</label>
          <SingleRefInput
            value={execution}
            onChange={setExecution}
            kinds="execution"
            placeholder="EXEC-0001 — digite para sugerir"
          />
        </div>
      </div>
      <div className="modal-field">
        <label>Descrição — digite @ para referenciar um card</label>
        <MentionTextarea
          value={body}
          onChange={setBody}
          placeholder="Passos para reproduzir, evidência, contexto…"
        />
      </div>

      <h4 className="section-title">Lição aprendida (opcional)</h4>
      <p className="caption muted" style={{ marginTop: -4, marginBottom: 8 }}>
        Preenchido, a IA passa a considerar isto ao gerar casos de teste para
        áreas relacionadas — evita repetir o mesmo bug.
      </p>
      <div className="modal-field">
        <label htmlFor="defect-root-cause">Causa raiz</label>
        <input
          id="defect-root-cause"
          value={rootCause}
          onChange={(e) => setRootCause(e.target.value)}
          placeholder="Ex.: falta validação de CPF"
        />
      </div>
      <div className="modal-field">
        <label htmlFor="defect-fix">Correção</label>
        <input
          id="defect-fix"
          value={fix}
          onChange={(e) => setFix(e.target.value)}
          placeholder="Ex.: campo obrigatório"
        />
      </div>
      <div className="modal-field">
        <label htmlFor="defect-prevention">Prevenção</label>
        <input
          id="defect-prevention"
          value={prevention}
          onChange={(e) => setPrevention(e.target.value)}
          placeholder="Ex.: sempre testar CPF vazio"
        />
      </div>
      </div>
    </Modal>
  );
}
