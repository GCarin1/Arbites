import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import { MentionTextarea, SingleRefInput } from "./Autocomplete";
import { ConfirmModal, Modal } from "./Modal";
import { DocBody } from "./ReadView";
import { useToast } from "./Toast";
import type { Decision } from "../types";

const STATUSES: Decision["status"][] = ["proposed", "accepted", "superseded"];
const STATUS_DOT: Record<string, string> = {
  proposed: "dot-col-in_progress",
  accepted: "dot-col-passed",
  superseded: "dot-col-pending",
};

/**
 * Decisões arquiteturais do TIME DE QA sobre o projeto sob teste — parte da
 * "Memória Histórica" (doc de ideias): ponteiro + metadados, mesmo espírito
 * de defeitos. Não é o sistema de ADR do próprio Doctrina.
 */
export function Decisions({
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
  const [items, setItems] = useState<Decision[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [editing, setEditing] = useState<Decision | "new" | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Decision | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [bodies, setBodies] = useState<Record<string, string>>({});

  const load = useCallback(() => {
    const q = statusFilter ? `?status=${statusFilter}` : "";
    api
      .decisions(q)
      .then(setItems)
      .catch((e) => onError(e.message));
  }, [statusFilter, onError]);

  useEffect(() => {
    load();
  }, [load]);

  // navegação por @DEC-XXXX (menções/links) abre direto no editor
  useEffect(() => {
    if (!openId) return;
    api
      .decision(openId)
      .then((d) => {
        setEditing(d);
        onOpened?.();
      })
      .catch((e) => {
        onError(e instanceof Error ? e.message : String(e));
        onOpened?.();
      });
  }, [openId, onError, onOpened]);

  async function toggleExpand(d: Decision) {
    setExpanded((old) => {
      const next = new Set(old);
      if (next.has(d.id)) next.delete(d.id);
      else next.add(d.id);
      return next;
    });
    if (!bodies[d.id]) {
      try {
        const full = await api.decision(d.id);
        setBodies((old) => ({ ...old, [d.id]: full.body ?? "" }));
      } catch {
        /* silencioso */
      }
    }
  }

  async function remove(decision: Decision) {
    setConfirmDelete(null);
    try {
      await api.deleteDecision(decision.id);
      load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function quickStatus(decision: Decision, status: string) {
    try {
      await api.updateDecision(decision.id, { status });
      load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Decisões</h1>
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
          <button className="primary" onClick={() => setEditing("new")}>
            Nova decisão
          </button>
        </div>
      </div>

      <p className="subtitle block">
        O porquê das escolhas do projeto sob teste — cada decisão registra
        contexto, o que foi decidido e as consequências. Meses depois, o time
        (e a IA, que recebe as decisões aceitas como contexto) ainda sabe o
        motivo.
      </p>

      {items.length === 0 ? (
        <div className="empty-state">
          <div className="empty-title">Nenhuma decisão registrada</div>
          <div className="empty-body">
            Exemplo: "Usar máscara de dados anonimizados nos testes de
            pagamento — contexto: dados reais são sensíveis; decisão: gerar
            massa sintética; consequência: cadastros de teste não validam em
            produção". Clique em "Nova decisão" para registrar a primeira.
          </div>
        </div>
      ) : (
        <div className="todo-cards">
          {items.map((d) => {
            const isOpen = expanded.has(d.id);
            return (
              <div key={d.id} className="todo-card">
                <div className="todo-card-head">
                  <span className="mono muted">{d.id}</span>
                  <span className="spacer" style={{ flex: 1 }} />
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
                </div>

                <button className="todo-card-title" onClick={() => void toggleExpand(d)} title={d.title}>
                  <span className={`status-dot ${STATUS_DOT[d.status]}`} /> {d.title}
                </button>

                <div className="todo-card-meta">
                  {d.created && <span className="caption mono muted">{d.created}</span>}
                  {d.squad && <span className="caption muted">{d.squad}</span>}
                  {d.tags.map((t) => (
                    <span key={t} className="caption muted">
                      #{t}
                    </span>
                  ))}
                  {d.supersedes && (
                    <button
                      type="button"
                      className="link-chip mono link-chip-btn"
                      onClick={() => onNavigate(d.supersedes!)}
                      title="Substitui esta decisão"
                    >
                      substitui {d.supersedes}
                    </button>
                  )}
                </div>

                {isOpen && (
                  <div className="todo-card-body">
                    {bodies[d.id]?.trim() ? (
                      <DocBody text={bodies[d.id]} onMention={onNavigate} />
                    ) : (
                      <p className="muted caption">Sem conteúdo. Use Editar para adicionar.</p>
                    )}
                  </div>
                )}

                <div className="todo-card-actions">
                  <button className="expand-btn" onClick={() => void toggleExpand(d)} title="Contexto/decisão/consequências">
                    {isOpen ? "▾" : "▸"}
                  </button>
                  <span className="spacer" style={{ flex: 1 }} />
                  <button className="btn-sm" onClick={() => setEditing(d)}>
                    Editar
                  </button>
                  <button className="btn-sm danger" onClick={() => setConfirmDelete(d)}>
                    Excluir
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {editing && (
        <DecisionModal
          decision={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            setBodies({});
            load();
          }}
          onError={onError}
        />
      )}
      {confirmDelete && (
        <ConfirmModal
          title="Excluir decisão"
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

function DecisionModal({
  decision,
  onClose,
  onSaved,
  onError,
}: {
  decision: Decision | null;
  onClose: () => void;
  onSaved: () => void;
  onError: (message: string) => void;
}) {
  const [title, setTitle] = useState(decision?.title ?? "");
  const [status, setStatus] = useState<string>(decision?.status ?? "proposed");
  const [squad, setSquad] = useState(decision?.squad ?? "");
  const [tags, setTags] = useState((decision?.tags ?? []).join(", "));
  const [supersedes, setSupersedes] = useState(decision?.supersedes ?? "");
  const [body, setBody] = useState(decision?.body ?? "");
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (decision && decision.body === undefined) {
      api
        .decision(decision.id)
        .then((full) => setBody(full.body ?? ""))
        .catch(() => {});
    }
  }, [decision]);

  async function save() {
    if (!title.trim()) return;
    setSaving(true);
    const payload = {
      title: title.trim(),
      status,
      squad: squad.trim() || null,
      tags: tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
      supersedes: supersedes.trim() || null,
      body,
    };
    try {
      if (decision) await api.updateDecision(decision.id, payload);
      else await api.createDecision(payload);
      toast("Decisão salva");
      onSaved();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
      setSaving(false);
    }
  }

  return (
    <Modal
      title={decision ? `Editar ${decision.id}` : "Nova decisão"}
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
        <label htmlFor="decision-title">Título</label>
        <input
          id="decision-title"
          ref={titleRef}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Ex.: Estratégia de dados de teste para pagamentos"
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
          <label>Squad (opcional)</label>
          <input value={squad} onChange={(e) => setSquad(e.target.value)} placeholder="pagamentos" />
        </div>
        <div className="field col-6">
          <label>Tags (vírgula, opcional)</label>
          <input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="dados-de-teste, ci" />
        </div>
        <div className="field wide">
          <label>Substitui (opcional)</label>
          <SingleRefInput
            value={supersedes}
            onChange={setSupersedes}
            kinds="decision"
            placeholder="DEC-0001 — digite para sugerir"
          />
        </div>
      </div>
      <div className="modal-field">
        <label>Contexto, decisão e consequências — digite @ para referenciar um card</label>
        <MentionTextarea
          value={body}
          onChange={setBody}
          placeholder="## Contexto&#10;&#10;...&#10;&#10;## Decisão&#10;&#10;...&#10;&#10;## Consequências&#10;&#10;..."
        />
      </div>
      </div>
    </Modal>
  );
}
