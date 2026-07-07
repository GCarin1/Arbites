import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import { ConfirmModal, Modal } from "./Modal";
import { DocBody } from "./ReadView";
import type { Meeting } from "../types";

export function Meetings({ onError }: { onError: (message: string) => void }) {
  const [items, setItems] = useState<Meeting[]>([]);
  const [dateFilter, setDateFilter] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [full, setFull] = useState<Record<string, Meeting>>({});
  const [editing, setEditing] = useState<Meeting | "new" | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Meeting | null>(null);

  const load = useCallback(() => {
    const q = dateFilter ? `?date=${dateFilter}` : "";
    api
      .meetings(q)
      .then(setItems)
      .catch((e) => onError(e.message));
  }, [dateFilter, onError]);

  useEffect(() => {
    load();
  }, [load]);

  async function toggleExpand(m: Meeting) {
    setExpanded((old) => {
      const next = new Set(old);
      if (next.has(m.id)) next.delete(m.id);
      else next.add(m.id);
      return next;
    });
    if (!full[m.id]) {
      try {
        const detail = await api.meeting(m.id);
        setFull((old) => ({ ...old, [m.id]: detail }));
      } catch {
        /* silencioso */
      }
    }
  }

  async function remove(m: Meeting) {
    setConfirmDelete(null);
    try {
      await api.deleteMeeting(m.id);
      load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Reuniões</h1>
        <span className="spacer" />
        <div className="head-controls">
          <label className="caption">Data</label>
          <input type="date" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} />
          <button className="primary" onClick={() => setEditing("new")}>
            Nova reunião
          </button>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">
          <div className="empty-title">Nenhuma reunião</div>
          <div className="empty-body">
            Registre o tema, a data e o que foi falado (descrição ou transcrição).
            A IA resume, e as reuniões do dia entram na daily.
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="dense">
            <thead>
              <tr>
                <th style={{ width: 28 }} />
                <th>Reunião</th>
                <th>Data</th>
                <th>Resumo</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((m) => {
                const isOpen = expanded.has(m.id);
                const detail = full[m.id];
                return (
                  <Fragment key={m.id}>
                    <tr>
                      <td>
                        <button className="expand-btn" onClick={() => void toggleExpand(m)} aria-label="Expandir">
                          {isOpen ? "▾" : "▸"}
                        </button>
                      </td>
                      <td>
                        <span className="mono muted">{m.id}</span> {m.title}
                      </td>
                      <td className="mono">{m.date ?? "—"}</td>
                      <td>
                        <span className={`status-dot ${m.summary ? "dot-active" : "dot-draft"}`}>
                          {m.summary ? "resumida" : "sem resumo"}
                        </span>
                      </td>
                      <td>
                        <div className="step-actions">
                          <button className="btn-sm" onClick={() => setEditing(m)}>
                            Editar
                          </button>
                          <button className="btn-sm danger" onClick={() => setConfirmDelete(m)}>
                            Excluir
                          </button>
                        </div>
                      </td>
                    </tr>
                    {isOpen && (
                      <tr className="todo-desc-row">
                        <td colSpan={5}>
                          {m.summary && (
                            <div className="meeting-summary">
                              <div className="metric-label">Resumo executivo</div>
                              <DocBody text={m.summary} />
                            </div>
                          )}
                          <div className="metric-label" style={{ marginTop: 12 }}>
                            Descrição / transcrição
                          </div>
                          <DocBody text={detail?.body ?? ""} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <MeetingModal
          meeting={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            setFull({});
            load();
          }}
          onError={onError}
        />
      )}
      {confirmDelete && (
        <ConfirmModal
          title="Excluir reunião"
          message={
            <>
              Mover <span className="mono">{confirmDelete.id}</span> para a lixeira?
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

function MeetingModal({
  meeting,
  onClose,
  onSaved,
  onError,
}: {
  meeting: Meeting | null;
  onClose: () => void;
  onSaved: () => void;
  onError: (message: string) => void;
}) {
  const [title, setTitle] = useState(meeting?.title ?? "");
  const [meetDate, setMeetDate] = useState(meeting?.date ?? new Date().toISOString().slice(0, 10));
  const [body, setBody] = useState("");
  const [summary, setSummary] = useState(meeting?.summary ?? "");
  const [saving, setSaving] = useState(false);
  const [summarizing, setSummarizing] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (meeting) {
      api
        .meeting(meeting.id)
        .then((full) => setBody(full.body ?? ""))
        .catch(() => {});
    }
  }, [meeting]);

  async function save(): Promise<Meeting | null> {
    const payload = { title: title.trim(), date: meetDate || null, body, summary: summary || null };
    if (meeting) return api.updateMeeting(meeting.id, payload);
    // criar não aceita summary; cria e devolve
    return api.createMeeting({ title: title.trim(), date: meetDate || null, body });
  }

  async function onSave() {
    if (!title.trim()) return;
    setSaving(true);
    try {
      await save();
      onSaved();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
      setSaving(false);
    }
  }

  async function summarize() {
    if (!body.trim()) {
      onError("Escreva a descrição/transcrição antes de resumir.");
      return;
    }
    setSummarizing(true);
    try {
      // garante que o corpo em disco é o atual antes de resumir
      const saved = meeting
        ? await api.updateMeeting(meeting.id, { title: title.trim(), date: meetDate || null, body })
        : await api.createMeeting({ title: title.trim(), date: meetDate || null, body });
      const result = await api.summarizeMeeting(saved.id);
      const text =
        result.summary +
        (result.decisions.length ? `\n\nDecisões:\n${result.decisions.map((d) => `- ${d}`).join("\n")}` : "") +
        (result.action_items.length ? `\n\nPróximos passos:\n${result.action_items.map((a) => `- ${a}`).join("\n")}` : "");
      setSummary(text);
      // se era novo, agora existe — persiste o resumo e recarrega a lista
      await api.updateMeeting(saved.id, { summary: text });
      onError(""); // limpa erro
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setSummarizing(false);
    }
  }

  return (
    <Modal
      title={meeting ? `Editar ${meeting.id}` : "Nova reunião"}
      onClose={onClose}
      initialFocus={titleRef}
      footer={
        <>
          <button onClick={onClose} disabled={saving}>
            Cancelar
          </button>
          <button className="primary" onClick={() => void onSave()} disabled={saving || !title.trim()}>
            {saving ? "Salvando…" : "Salvar"}
          </button>
        </>
      }
    >
      <div className="field-grid">
        <div className="field col-8">
          <label htmlFor="meet-title">Tema</label>
          <input
            id="meet-title"
            ref={titleRef}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ex.: Alinhamento da regressão"
          />
        </div>
        <div className="field col-4">
          <label>Data</label>
          <input type="date" value={meetDate} onChange={(e) => setMeetDate(e.target.value)} />
        </div>
      </div>
      <div className="modal-field">
        <label>Descrição ou transcrição</label>
        <textarea
          className="raw"
          style={{ minHeight: 160 }}
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Cole aqui o que foi falado ou a transcrição da reunião."
          spellCheck={false}
        />
      </div>
      <div className="toolbar">
        <button onClick={() => void summarize()} disabled={summarizing || !body.trim()}>
          {summarizing ? "Resumindo…" : "Resumir com IA"}
        </button>
        <span className="caption muted">a IA resume; você pode editar antes de salvar</span>
      </div>
      <div className="modal-field">
        <label>Resumo executivo</label>
        <textarea
          className="raw"
          style={{ minHeight: 120 }}
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          placeholder="Gerado pela IA (ou escreva à mão)."
          spellCheck={false}
        />
      </div>
    </Modal>
  );
}
