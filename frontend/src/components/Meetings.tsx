import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import { ConfirmModal, Modal } from "./Modal";
import { DocBody } from "./ReadView";
import { useToast } from "./Toast";
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
  const [dirty, setDirty] = useState(false);
  // 0097: action items → afazeres
  const [converted, setConverted] = useState<{ id: string; title: string; status: string }[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [aiItems, setAiItems] = useState<string[]>([]);
  const [aiEnabled, setAiEnabled] = useState(false);
  const [working, setWorking] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (meeting) {
      api
        .meeting(meeting.id)
        .then((full) => setBody(full.body ?? ""))
        .catch(() => {});
      api
        .meetingActionItems(meeting.id)
        .then((r) => setConverted(r.converted))
        .catch(() => {});
    }
  }, [meeting]);

  useEffect(() => {
    api
      .aiProviders()
      .then((info) => setAiEnabled(!!info.default_provider))
      .catch(() => setAiEnabled(false));
  }, []);

  // extração determinística ao vivo (linhas `- [ ]`), reflete o textarea sem
  // depender de salvar nem de IA — a aba funciona 100% sem provider.
  const alreadyTitles = new Set(converted.map((c) => c.title));
  const deterministic = Array.from(
    new Set(
      body
        .split("\n")
        .map((l) => /^\s*[-*]\s*\[\s*\]\s+(.+?)\s*$/.exec(l)?.[1]?.trim())
        .filter((x): x is string => !!x),
    ),
  );
  const previewItems = Array.from(new Set([...deterministic, ...aiItems])).filter(
    (t) => !alreadyTitles.has(t),
  );

  function toggleSel(item: string) {
    setSelected((old) => {
      const next = new Set(old);
      if (next.has(item)) next.delete(item);
      else next.add(item);
      return next;
    });
  }

  async function generateWithAi() {
    if (!meeting) return;
    setWorking(true);
    try {
      await api.updateMeeting(meeting.id, { body }); // sincroniza o corpo
      const r = await api.generateMeetingActionItems(meeting.id);
      setAiItems(r.action_items);
      setSelected(new Set([...selected, ...r.action_items]));
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(false);
    }
  }

  async function acceptSelected() {
    if (!meeting || selected.size === 0) return;
    setWorking(true);
    try {
      const r = await api.acceptMeetingActionItems(meeting.id, [...selected]);
      setConverted(r.converted);
      setSelected(new Set());
      setAiItems([]);
      toast(`${r.created.length} afazer(es) criado(s)`);
      onSaved();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(false);
    }
  }

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
      toast("Reunião salva");
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
      dirty={dirty && !saving}
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
      <div className="modal-form" onInput={() => setDirty(true)}>
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
      {meeting ? (
        <div className="modal-field action-items">
          <div className="toolbar">
            <label style={{ margin: 0 }}>Action items</label>
            <span className="spacer" />
            {aiEnabled && (
              <button onClick={() => void generateWithAi()} disabled={working || !body.trim()}>
                {working ? "…" : "Sugerir com IA"}
              </button>
            )}
            <button
              className="primary"
              onClick={() => void acceptSelected()}
              disabled={working || selected.size === 0}
            >
              Criar afazeres ({selected.size})
            </button>
          </div>
          {previewItems.length === 0 ? (
            <p className="caption muted">
              Escreva itens como <span className="mono">- [ ] fazer X</span> na
              descrição — eles aparecem aqui para virar afazeres.
            </p>
          ) : (
            <ul className="ai-preview-list">
              {previewItems.map((item) => (
                <li key={item}>
                  <label className="check-inline">
                    <input
                      type="checkbox"
                      checked={selected.has(item)}
                      onChange={() => toggleSel(item)}
                    />
                    <span>{item}</span>
                  </label>
                </li>
              ))}
            </ul>
          )}
          {converted.length > 0 && (
            <div className="converted-items">
              <span className="caption muted">Já convertidos:</span>
              <ul className="ai-preview-list">
                {converted.map((c) => (
                  <li key={c.id} className="caption">
                    <span className="mono muted">{c.id}</span> {c.title}{" "}
                    <span className={`status-dot dot-${c.status} caption`}>{c.status}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <p className="caption muted">
          Salve a reunião para extrair action items em afazeres.
        </p>
      )}
      </div>
    </Modal>
  );
}
