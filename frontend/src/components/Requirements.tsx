import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import { EmptyState, NoMatches } from "./EmptyState";
import { ConfirmModal, Modal } from "./Modal";
import { DetailCard, DocBody, ReadField } from "./ReadView";
import { Story360 } from "./Story360";
import { useToast } from "./Toast";
import type { Criterion, MatrixStory, Requirement } from "../types";

// estado semântico de cobertura por story (0087) — cor + rótulo + hint
const COV_STATE: Record<
  MatrixStory["coverage_state"],
  { label: string; dot: string; hint: string }
> = {
  passing: { label: "passando", dot: "dot-col-passed", hint: "todos os CTs executados passaram" },
  failing: { label: "com falhas", dot: "dot-col-failed", hint: "algum CT com último resultado failed/blocked" },
  untested: { label: "nunca executada", dot: "dot-col-pending", hint: "tem CT vinculado, mas nenhum foi executado" },
  uncovered: { label: "sem cobertura", dot: "dot-col-blocked", hint: "nenhum CT vinculado" },
};

export function RequirementsList({
  version,
  selected,
  onSelect,
  onCreated,
  onError,
}: {
  version: number;
  selected: string | null;
  onSelect: (id: string) => void;
  onCreated: (id: string) => void;
  onError: (message: string) => void;
}) {
  const [items, setItems] = useState<Requirement[]>([]);
  const [creating, setCreating] = useState<"epic" | "story" | null>(null);

  useEffect(() => {
    api
      .requirements()
      .then(setItems)
      .catch((e) => onError(e.message));
  }, [version, onError]);

  async function create(kind: "epic" | "story", title: string, epic: string | null) {
    try {
      const created = await api.createRequirement({ kind, title, epic });
      setCreating(null);
      onCreated(created.id);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  const epics = items.filter((r) => r.kind === "epic");
  const stories = items.filter((r) => r.kind === "story");
  const orphans = stories.filter((s) => !epics.some((e) => e.id === s.epic_id));

  return (
    <div>
      <div className="list-toolbar">
        <button onClick={() => setCreating("epic")}>Novo epic</button>
        <button onClick={() => setCreating("story")}>Nova story</button>
      </div>
      {creating && (
        <NewRequirementModal
          kind={creating}
          onSubmit={(title, epic) => void create(creating, title, epic)}
          onClose={() => setCreating(null)}
        />
      )}
      {epics.map((epic) => (
        <div key={epic.id}>
          <ReqItem item={epic} selected={selected} onSelect={onSelect} />
          <div style={{ paddingLeft: 16 }}>
            {stories
              .filter((s) => s.epic_id === epic.id)
              .map((story) => (
                <ReqItem key={story.id} item={story} selected={selected} onSelect={onSelect} />
              ))}
          </div>
        </div>
      ))}
      {orphans.length > 0 && (
        <>
          <div className="dir mono" style={{ paddingTop: 8 }}>
            sem epic/
          </div>
          {orphans.map((story) => (
            <ReqItem key={story.id} item={story} selected={selected} onSelect={onSelect} />
          ))}
        </>
      )}
      {items.length === 0 && (
        <EmptyState compact icon="requirements" title="Nenhum requisito ainda">
          Epics e stories criados aparecem aqui.
        </EmptyState>
      )}
    </div>
  );
}

/**
 * Repositório de requisitos centralizado (doc §1.2) — hierarquia epic→story
 * com expandir/colapsar, drag & drop de story para outro epic (reassocia),
 * exclusão com confirmação e data de criação. Detalhe abre só por clique.
 */
export function ReqRepository({
  version,
  onOpen,
  onNavigate,
  onChanged,
  onError,
}: {
  version: number;
  onOpen: (id: string) => void;
  onNavigate: (id: string) => void;
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [items, setItems] = useState<Requirement[]>([]);
  const [creating, setCreating] = useState<"epic" | "story" | null>(null);
  const [chainOf, setChainOf] = useState<string | null>(null); // Story 360 (0086)
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [dragStory, setDragStory] = useState<string | null>(null);
  const [dropEpic, setDropEpic] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<Requirement | null>(null);
  // Cobertura por story (0068/0087/0092): reuso da matriz de rastreabilidade
  // — mesma fonte do Dashboard, sem endpoint novo. story_id → CTs + estado
  // semântico + critérios.
  const [coverage, setCoverage] = useState<Map<
    string,
    { ct: number; state: MatrixStory["coverage_state"]; critTotal: number; critCovered: number }
  > | null>(null);
  const [covFilter, setCovFilter] = useState<"all" | MatrixStory["coverage_state"]>("all");

  const load = useCallback(() => {
    api
      .requirements()
      .then(setItems)
      .catch((e) => onError(e.message));
    api
      .traceability("", "")
      .then((m) => {
        const map = new Map<
          string,
          { ct: number; state: MatrixStory["coverage_state"]; critTotal: number; critCovered: number }
        >();
        const anotar = (s: MatrixStory) =>
          map.set(s.id, {
            ct: s.ct_count,
            state: s.coverage_state,
            critTotal: s.criteria_total,
            critCovered: s.criteria_covered,
          });
        for (const epic of m.epics) for (const s of epic.stories) anotar(s);
        // Story sem epic conta igual: ela some da matriz por epic, e sem isto
        // a tela a mostrava como "sem cobertura" mesmo coberta.
        for (const s of m.orphan_stories ?? []) anotar(s);
        setCoverage(map);
      })
      .catch(() => {});
  }, [onError]);

  useEffect(() => {
    load();
  }, [load, version]);

  async function create(kind: "epic" | "story", title: string, epic: string | null) {
    try {
      const created = await api.createRequirement({ kind, title, epic });
      setCreating(null);
      onChanged();
      onOpen(created.id);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function moveStory(epicId: string | null) {
    if (!dragStory) return;
    try {
      await api.updateRequirement(dragStory, { epic: epicId });
      onChanged();
      load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setDragStory(null);
      setDropEpic(null);
    }
  }

  async function remove(item: Requirement) {
    setDeleting(null);
    try {
      await api.deleteRequirement(item.id);
      onChanged();
      load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  function toggle(id: string) {
    setCollapsed((old) => {
      const next = new Set(old);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const epics = items.filter((r) => r.kind === "epic");
  const allStories = items.filter((r) => r.kind === "story");
  // cobertura (0068/0087): estado semântico por story
  const ctsOf = (id: string) => coverage?.get(id)?.ct ?? 0;
  const critOf = (id: string) => coverage?.get(id); // {critTotal, critCovered}
  const stateOf = (id: string) => coverage?.get(id)?.state ?? "uncovered";
  const stories =
    covFilter === "all" ? allStories : allStories.filter((s) => stateOf(s.id) === covFilter);
  const orphans = stories.filter((s) => !epics.some((e) => e.id === s.epic_id));
  const coveredCount = (epicId: string) =>
    allStories.filter((s) => s.epic_id === epicId && ctsOf(s.id) > 0).length;

  const storyRow = (story: Requirement, prefix: string, isLast: boolean) => (
    <div
      key={story.id}
      className={`repo-row repo-file ${dragStory === story.id ? "dragging" : ""}`}
      draggable
      onDragStart={() => setDragStory(story.id)}
      onDragEnd={() => {
        setDragStory(null);
        setDropEpic(null);
      }}
    >
      <span className="tree-prefix">{prefix + (isLast ? "└── " : "├── ")}</span>
      <button className="repo-file-main" onClick={() => onOpen(story.id)}>
        <span className="mono muted">{story.id}</span>
        <span className="repo-file-title">{story.title}</span>
      </button>
      {coverage &&
        (() => {
          const st = stateOf(story.id);
          const n = ctsOf(story.id);
          const meta = COV_STATE[st];
          return (
            <span className={`status-dot ${meta.dot} caption`} title={meta.hint}>
              {meta.label}
              {n > 0 && st !== "uncovered" ? ` (${n} CT${n === 1 ? "" : "s"})` : ""}
            </span>
          );
        })()}
      {/* cobertura de critérios EARS (0092): só quando a story tem critérios */}
      {(() => {
        const c = critOf(story.id);
        if (!c || c.critTotal === 0) return null;
        const full = c.critCovered === c.critTotal;
        return (
          <span
            className={`status-dot ${full ? "dot-col-passed" : "dot-col-blocked"} caption`}
            title="critérios EARS cobertos por CT"
          >
            {c.critCovered}/{c.critTotal} critérios
          </span>
        );
      })()}
      <span className={`status-dot dot-${story.status} caption`}>{story.status}</span>
      <span className="caption mono muted">{story.created ?? ""}</span>
      <span className="repo-actions">
        <button className="btn-sm" onClick={() => setChainOf(story.id)} title="Story 360 — cadeia completa">
          360
        </button>
        <button className="btn-sm danger" onClick={() => setDeleting(story)}>
          Excluir
        </button>
      </span>
    </div>
  );

  // topo da árvore = epics + (pseudo-pasta "sem epic" se houver órfãs)
  const topLevel = epics.length + (orphans.length > 0 ? 1 : 0);

  return (
    <div className="repo">
      <div className="page-head">
        <h1 className="page-title">Requisitos</h1>
        <span className="spacer" />
        <div className="head-controls">
          <label className="check-inline caption">
            Cobertura
            <select value={covFilter} onChange={(e) => setCovFilter(e.target.value as typeof covFilter)}>
              <option value="all">todas</option>
              <option value="passing">passando</option>
              <option value="failing">com falhas</option>
              <option value="untested">nunca executada</option>
              <option value="uncovered">sem cobertura</option>
            </select>
          </label>
          <button onClick={() => setCreating("epic")}>Novo epic</button>
          <button className="primary" onClick={() => setCreating("story")}>
            Nova story
          </button>
        </div>
      </div>

      <div className="repo-tree card">
        {items.length === 0 ? (
          <EmptyState
            compact
            icon="requirements"
            title="Nenhum requisito ainda"
            action={{ label: "Nova story", onClick: () => setCreating("story") }}
            secondary={{ label: "Novo epic", onClick: () => setCreating("epic") }}
          >
            A story é o que os casos de teste cobrem, e o epic é a pasta dela.
            Arraste uma story para outro epic para reassociá-la.
          </EmptyState>
        ) : allStories.length > 0 && stories.length === 0 ? (
          // o filtro de cobertura escondeu tudo: criar mais story não é a
          // saída — a saída é voltar a ver as que existem (0144)
          <NoMatches what="stories" onClear={() => setCovFilter("all")} />
        ) : (
          <>
            {epics.map((epic, ei) => {
              const isCollapsed = collapsed.has(epic.id);
              const children = stories.filter((s) => s.epic_id === epic.id);
              const epicLast = ei === topLevel - 1;
              const childPrefix = epicLast ? "    " : "│   ";
              return (
                <div key={epic.id} className="repo-dir">
                  <div
                    className={`repo-row repo-folder ${dropEpic === epic.id ? "drop-target" : ""}`}
                    onDragOver={(e) => {
                      if (dragStory) {
                        e.preventDefault();
                        setDropEpic(epic.id);
                      }
                    }}
                    onDragLeave={() => setDropEpic((t) => (t === epic.id ? null : t))}
                    onDrop={() => void moveStory(epic.id)}
                  >
                    <span className="tree-prefix">{epicLast ? "└── " : "├── "}</span>
                    <button className="expand-btn" onClick={() => toggle(epic.id)}>
                      {isCollapsed ? "▸" : "▾"}
                    </button>
                    <button className="repo-file-main" onClick={() => onOpen(epic.id)}>
                      <span className="mono muted">{epic.id}</span>
                      <span className="repo-folder-name">{epic.title}</span>
                    </button>
                    <span className="caption muted">{children.length}</span>
                    {coverage && (
                      <span className="caption muted">
                        {coveredCount(epic.id)}/
                        {allStories.filter((s) => s.epic_id === epic.id).length}{" "}
                        cobertas
                      </span>
                    )}
                    <span className="caption mono muted">{epic.created ?? ""}</span>
                    <span className="repo-actions">
                      <button className="btn-sm danger" onClick={() => setDeleting(epic)}>
                        Excluir
                      </button>
                    </span>
                  </div>
                  {!isCollapsed &&
                    children.map((s, si) =>
                      storyRow(s, childPrefix, si === children.length - 1),
                    )}
                </div>
              );
            })}
            {orphans.length > 0 && (
              <>
                <div
                  className={`repo-row repo-folder ${dropEpic === "__none__" ? "drop-target" : ""}`}
                  onDragOver={(e) => {
                    if (dragStory) {
                      e.preventDefault();
                      setDropEpic("__none__");
                    }
                  }}
                  onDragLeave={() => setDropEpic((t) => (t === "__none__" ? null : t))}
                  onDrop={() => void moveStory(null)}
                >
                  <span className="tree-prefix">└── </span>
                  <span className="repo-folder-name muted">sem epic/</span>
                </div>
                {orphans.map((s, si) =>
                  storyRow(s, "    ", si === orphans.length - 1),
                )}
              </>
            )}
          </>
        )}
      </div>

      {creating && (
        <NewRequirementModal
          kind={creating}
          onSubmit={(title, epic) => void create(creating, title, epic)}
          onClose={() => setCreating(null)}
        />
      )}
      {deleting && (
        <ConfirmModal
          title={`Excluir ${deleting.kind === "epic" ? "epic" : "story"}`}
          message={
            <>
              Mover <span className="mono">{deleting.id}</span> ({deleting.title})
              para a lixeira?
              {deleting.kind === "epic" && " As stories dele ficam sem epic."}
            </>
          }
          confirmLabel="Mover para a lixeira"
          danger
          onConfirm={() => void remove(deleting)}
          onCancel={() => setDeleting(null)}
        />
      )}
      {chainOf && (
        <Story360 storyId={chainOf} onClose={() => setChainOf(null)} onNavigate={onNavigate} />
      )}
    </div>
  );
}

function ReqItem({
  item,
  selected,
  onSelect,
}: {
  item: Requirement;
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <button
      className={`list-item ${item.id === selected ? "selected" : ""}`}
      onClick={() => onSelect(item.id)}
    >
      <span className="mono muted">{item.id}</span>
      <span>{item.title}</span>
    </button>
  );
}

function NewRequirementModal({
  kind,
  onSubmit,
  onClose,
}: {
  kind: "epic" | "story";
  onSubmit: (title: string, epic: string | null) => void;
  onClose: () => void;
}) {
  const [title, setTitle] = useState("");
  const [epic, setEpic] = useState("");
  const titleRef = useRef<HTMLInputElement>(null);
  const label = kind === "epic" ? "epic" : "story";

  function submit() {
    if (!title.trim()) return;
    onSubmit(title.trim(), kind === "story" ? epic.trim() || null : null);
  }

  return (
    <Modal
      title={`Novo ${label}`}
      onClose={onClose}
      initialFocus={titleRef}
      footer={
        <>
          <button onClick={onClose}>Cancelar</button>
          <button className="primary" onClick={submit} disabled={!title.trim()}>
            Criar
          </button>
        </>
      }
    >
      <form
        className="modal-field"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <label htmlFor="new-req-title">Título</label>
        <input
          id="new-req-title"
          ref={titleRef}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={kind === "epic" ? "Ex.: Autenticação" : "Ex.: Login"}
        />
      </form>
      {kind === "story" && (
        <div className="modal-field">
          <label htmlFor="new-req-epic">Epic pai (opcional)</label>
          <input
            id="new-req-epic"
            className="mono"
            value={epic}
            onChange={(e) => setEpic(e.target.value)}
            placeholder="EP-0001 — vazio = nenhum"
          />
        </div>
      )}
    </Modal>
  );
}

export function RequirementEditor({
  id,
  onChanged,
  onDeleted,
  onNavigate,
}: {
  id: string;
  onChanged: () => void;
  onDeleted: () => void;
  /** Para os CTs que cobrem cada critério virarem link (change 0158). */
  onNavigate?: (id: string) => void;
}) {
  const [req, setReq] = useState<Requirement | null>(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const { toast } = useToast();

  const load = useCallback(() => {
    setError(null);
    return api
      .requirement(id)
      .then(setReq)
      .catch((e) => setError(e.message));
  }, [id]);

  useEffect(() => {
    setEditing(false); // sempre abre em modo leitura
    void load();
  }, [id, load]);

  if (error) return <div className="error-banner">{error}</div>;
  if (!req) return <p className="empty">Carregando {id}…</p>;

  function set<K extends keyof Requirement>(key: K, value: Requirement[K]) {
    setReq((old) => (old ? { ...old, [key]: value } : old));
  }

  async function save() {
    if (!req) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateRequirement(id, {
        title: req.title,
        status: req.status,
        epic: req.epic_id || null,
        external_key: req.external_key || null,
        confluence_url: req.confluence_url || null,
        squad: req.squad || null,
        tags: req.tags,
        body: req.body ?? "",
      });
      setReq(updated);
      setEditing(false); // após salvar, volta ao modo leitura
      toast("Requisito salvo");
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  function cancelEdit() {
    void load(); // descarta edições não salvas
    setEditing(false);
  }

  async function remove() {
    setConfirmDelete(false);
    try {
      await api.deleteRequirement(id);
      onDeleted();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="editor">
      {confirmDelete && (
        <ConfirmModal
          title="Excluir requisito"
          message={
            <>
              Mover <span className="mono">{id}</span> para a lixeira
              (<span className="mono">.arbites/trash/</span>)?
            </>
          }
          confirmLabel="Mover para a lixeira"
          danger
          onConfirm={() => void remove()}
          onCancel={() => setConfirmDelete(false)}
        />
      )}
      {!editing ? (
        <>
          <DetailCard
            id={req.id}
            title={req.title}
            status={<span className={`status-dot dot-${req.status}`}>{req.status}</span>}
            actions={
              <>
                {/* Requisito que vive no sistema oficial não se edita aqui
                    (change 0158): editar a cópia faz os dois lados
                    discordarem em silêncio, porque nada falha. */}
                <button
                  className="primary"
                  onClick={() => setEditing(true)}
                  disabled={req.owned_elsewhere}
                  title={
                    req.owned_elsewhere
                      ? "este requisito vive no sistema oficial — edite lá"
                      : undefined
                  }
                >
                  Editar
                </button>
                <button className="danger" onClick={() => setConfirmDelete(true)}>
                  Excluir
                </button>
              </>
            }
          >
          {req.owned_elsewhere ? (
            <p className="req-origem req-origem-externa">
              Este requisito <strong>vive em{" "}
              {(req.external ?? []).map((v) => v.system).join(", ")}</strong> — aqui
              ele é espelho. Editar a cópia faria os dois lados discordarem sem
              ninguém ser avisado, então a edição está fechada. Para assumi-lo
              aqui, remova o vínculo externo primeiro; a decisão fica explícita.
            </p>
          ) : (
            <p className="req-origem">
              Escrito aqui — sem vínculo com sistema externo.
            </p>
          )}
          <div className="read-grid">
            <ReadField label="Tipo" value={req.kind} />
            <ReadField
              label="Status"
              value={<span className={`status-dot dot-${req.status}`}>{req.status}</span>}
            />
            {req.kind === "story" && <ReadField label="Epic" value={req.epic_id} mono />}
            <ReadField label="Squad" value={req.squad} />
            <ReadField label="Chave externa" value={req.external_key} mono />
            {req.kind === "story" && (
              <ReadField
                label="Confluence"
                wide
                value={
                  req.confluence_url ? (
                    <a href={req.confluence_url} target="_blank" rel="noreferrer">
                      {req.confluence_url}
                    </a>
                  ) : null
                }
              />
            )}
            <ReadField
              label="Tags"
              value={(req.tags ?? []).length ? (req.tags ?? []).join(", ") : null}
            />
            <ReadField label="Arquivo" value={req.path} mono />
          </div>
          </DetailCard>
          <div className="card">
            <div className="card-head">
              <h3>Corpo</h3>
            </div>
            <DocBody text={req.body} />
          </div>
          {req.kind === "story" && (
            <CriteriaCard id={req.id} onNavigate={onNavigate} />
          )}
        </>
      ) : (
        <>
      <h2>
        <span className="mono muted">{req.id}</span>
        <span>{req.title}</span>
        <span className={`status-dot dot-${req.status} muted`}>{req.status}</span>
      </h2>
      <div className="toolbar">
        <button className="primary" onClick={() => void save()} disabled={saving}>
          {saving ? "Salvando…" : "Salvar"}
        </button>
        <button onClick={cancelEdit} disabled={saving}>
          Cancelar
        </button>
        <span className="spacer" />
        <button className="danger" onClick={() => setConfirmDelete(true)}>
          Excluir
        </button>
      </div>
      <div className="field-grid">
        <div className="field wide">
          <label>Título</label>
          <input value={req.title} onChange={(e) => set("title", e.target.value)} />
        </div>
        <div className="field">
          <label>Status</label>
          <select value={req.status} onChange={(e) => set("status", e.target.value)}>
            <option value="active">active</option>
            <option value="done">done</option>
            <option value="cancelled">cancelled</option>
          </select>
        </div>
        <div className="field">
          <label>Squad</label>
          <input
            placeholder="ex.: pagamentos"
            value={req.squad ?? ""}
            onChange={(e) => set("squad", e.target.value || null)}
          />
        </div>
        {req.kind === "story" && (
          <div className="field">
            <label>Epic</label>
            <input
              className="mono"
              placeholder="EP-0000"
              value={req.epic_id ?? ""}
              onChange={(e) => set("epic_id", e.target.value || null)}
            />
          </div>
        )}
        <div className="field">
          <label>Chave externa</label>
          <input
            className="mono"
            placeholder="PROJ-123"
            value={req.external_key ?? ""}
            onChange={(e) => set("external_key", e.target.value || null)}
          />
        </div>
        {req.kind === "story" && (
          <div className="field wide">
            <label>Confluence URL</label>
            <input
              value={req.confluence_url ?? ""}
              onChange={(e) => set("confluence_url", e.target.value || null)}
            />
          </div>
        )}
      </div>
      <div className="field wide">
        <label>
          {req.kind === "story"
            ? "Corpo (Resumo / Critérios de aceite — EARS quando fizer sentido)"
            : "Corpo (Descrição)"}
        </label>
        {req.kind === "story" && (
          <div className="ears-templates">
            <span className="caption muted">Inserir critério EARS:</span>
            {(
              [
                ["ubiquitous", "Ubíquo"],
                ["event", "Evento"],
                ["state", "Estado"],
                ["unwanted", "Proibição"],
                ["optional", "Opcional"],
              ] as const
            ).map(([form, label]) => (
              <button
                key={form}
                type="button"
                className="btn-sm"
                onClick={() => set("body", appendEarsCriterion(req.body ?? "", form))}
              >
                + {label}
              </button>
            ))}
          </div>
        )}
        <textarea
          className="raw"
          value={req.body ?? ""}
          onChange={(e) => set("body", e.target.value)}
          spellCheck={false}
        />
      </div>
        </>
      )}
    </div>
  );
}

// -------------------------------------------------- EARS (0091)

const EARS_TEMPLATE: Record<string, string> = {
  ubiquitous: "O sistema deve ",
  event: "Quando <condição>, o sistema deve ",
  state: "Enquanto <estado>, o sistema deve ",
  unwanted: "O sistema não deve ",
  optional: "Onde <recurso disponível>, o sistema pode ",
};

const FORM_LABEL: Record<string, string> = {
  ubiquitous: "ubíquo",
  event: "evento",
  state: "estado",
  unwanted: "proibição",
  optional: "opcional",
};

/** Insere `- [EARS-n]` com o próximo número, criando a seção se faltar. */
function appendEarsCriterion(body: string, form: string): string {
  const nums = [...body.matchAll(/\[EARS-(\d+)\]/g)].map((m) => Number(m[1]));
  const next = (nums.length ? Math.max(...nums) : 0) + 1;
  const line = `- [EARS-${next}] ${EARS_TEMPLATE[form]}`;
  let out = body;
  if (!/^##\s+crit[ée]rios de aceite/im.test(out)) {
    out = out.replace(/\s*$/, "") + "\n\n## Critérios de aceite\n";
  }
  return out.replace(/\s*$/, "") + "\n" + line + "\n";
}

/** Critérios EARS indexados da story, com a forma detectada por critério —
 * dá visibilidade ao lint (cinza = fora de EARS). */
/**
 * Cobertura de um critério, em uma palavra e uma cor (change 0158).
 *
 * A pergunta do time de negócio não é "quantos casos esta story tem?" — é
 * "este critério foi verificado?". São perguntas diferentes: quatro casos
 * podem cobrir o mesmo critério e deixar três descobertos, e a contagem por
 * story esconde exatamente isso.
 */
const COBERTURA: Record<string, { label: string; dot: string; hint: string }> = {
  uncovered: {
    label: "sem caso",
    dot: "dot-col-blocked",
    hint: "nenhum caso de teste cita este critério",
  },
  untested: {
    label: "nunca executado",
    dot: "dot-col-pending",
    hint: "há caso citando o critério, mas nenhum foi executado ainda",
  },
  failing: {
    label: "com falha",
    dot: "dot-col-failed",
    hint: "o último resultado de algum caso deste critério falhou ou ficou bloqueado",
  },
  passing: {
    label: "verificado",
    dot: "dot-col-passed",
    hint: "todos os casos que cobrem este critério passaram na última execução",
  },
};

function CriteriaCard({
  id,
  onNavigate,
}: {
  id: string;
  onNavigate?: (id: string) => void;
}) {
  const [crits, setCrits] = useState<Criterion[]>([]);

  useEffect(() => {
    let alive = true;
    api.requirementCriteria(id).then((c) => alive && setCrits(c)).catch(() => {});
    return () => {
      alive = false;
    };
  }, [id]);

  if (crits.length === 0) return null;

  const descobertos = crits.filter((c) => c.coverage === "uncovered").length;

  return (
    <div className="card">
      <div className="card-head">
        <h3>Critérios de aceite (EARS)</h3>
        <span className="spacer" />
        <span className="caption muted">
          {crits.length} {crits.length === 1 ? "critério" : "critérios"}
          {descobertos > 0 && (
            <>
              {" · "}
              <strong className="crit-alerta">
                {descobertos} sem caso de teste
              </strong>
            </>
          )}
        </span>
      </div>
      <div className="criteria-list">
        {crits.map((c) => {
          const cob = COBERTURA[c.coverage ?? "uncovered"];
          return (
            <div key={c.ears_id} className="criteria-row">
              <span className="mono muted">{c.ears_id}</span>
              <span
                className={`status-dot ${c.form ? "dot-col-passed" : "dot-col-blocked"} caption`}
              >
                {c.form ? FORM_LABEL[c.form] ?? c.form : "fora de EARS"}
              </span>
              <span className="criteria-text">
                {c.text}
                <span className="crit-cobertura">
                  <span className={`status-dot ${cob.dot} caption`} title={cob.hint}>
                    {cob.label}
                  </span>
                  {(c.covered_by ?? []).map((ct) => (
                    <button
                      key={ct.id}
                      type="button"
                      className="link-btn mono caption"
                      title={ct.title}
                      onClick={() => onNavigate?.(ct.id)}
                    >
                      {ct.id}
                    </button>
                  ))}
                </span>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
