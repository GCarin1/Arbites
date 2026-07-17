import { useEffect, useState } from "react";
import { api } from "../api";
import { ConfirmModal, Modal } from "./Modal";
import { DocBody } from "./ReadView";
import { useToast } from "./Toast";
import type { Defect, GeneratedTestcase, TestCase, TreeNode } from "../types";

type DragState =
  | { kind: "ct"; id: string }
  | { kind: "folder"; path: string; ctCount: number };

/** true se `destPath` for a própria `srcPath` ou algum descendente dela. */
function isDescendantOrSelf(destPath: string, srcPath: string): boolean {
  return destPath === srcPath || destPath.startsWith(`${srcPath}/`);
}

/**
 * Repositório de test cases (doc §1.1) — árvore de pastas centralizada no
 * conteúdo, com expandir/colapsar, drag & drop de CTs entre pastas, criação e
 * exclusão de pastas. O detalhe abre só por clique (App troca p/ editor).
 */
export function TcRepository({
  root,
  onOpen,
  onChanged,
  onError,
  onNew,
  extraActions,
}: {
  root: TreeNode;
  onOpen: (id: string) => void;
  onChanged: () => void;
  onError: (message: string) => void;
  onNew: () => void;
  extraActions?: React.ReactNode;
}) {
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [drag, setDrag] = useState<DragState | null>(null);
  const [dropTarget, setDropTarget] = useState<string | null>(null);
  const [creatingFolder, setCreatingFolder] = useState<string | null>(null); // pasta pai
  const [deletingFolder, setDeletingFolder] = useState<TreeNode | null>(null);
  const [deletingCt, setDeletingCt] = useState<{ id: string; title: string } | null>(null);
  const [importing, setImporting] = useState(false);
  const [pendingFolderMove, setPendingFolderMove] = useState<{
    srcPath: string;
    destPath: string;
    ctCount: number;
  } | null>(null);

  // Filtros combinados (0064): busca fixa + status/prioridade/tipo/tag. O
  // filtro roda no SERVIDOR (GET /testcases, os mesmos params da API) e a
  // árvore só exibe os IDs que casaram — uma fonte só, sem reimplementar a
  // lógica de filtro no cliente.
  const [q, setQ] = useState("");
  const [fStatus, setFStatus] = useState("");
  const [fPriority, setFPriority] = useState("");
  const [fType, setFType] = useState("");
  const [fTag, setFTag] = useState("");
  const [matchIds, setMatchIds] = useState<Set<string> | null>(null); // null = sem filtro
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filterActive = !!(q.trim() || fStatus || fPriority || fType || fTag.trim());
  useEffect(() => {
    if (!filterActive) {
      setMatchIds(null);
      return;
    }
    let alive = true;
    const timer = setTimeout(() => {
      const params = new URLSearchParams();
      if (q.trim()) params.set("q", q.trim());
      if (fStatus) params.set("status", fStatus);
      if (fPriority) params.set("priority", fPriority);
      if (fType) params.set("type", fType);
      if (fTag.trim()) params.set("tag", fTag.trim().replace(/^@/, ""));
      api
        .testcases(`?${params.toString()}`)
        .then((rows) => alive && setMatchIds(new Set(rows.map((r) => r.id))))
        .catch((e) => onError(e instanceof Error ? e.message : String(e)));
    }, 150);
    return () => {
      alive = false;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, fStatus, fPriority, fType, fTag, filterActive]);

  function toggle(path: string) {
    setCollapsed((old) => {
      const next = new Set(old);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }

  // caminho relativo a testcases/ (a API de pastas/move usa esse formato)
  function relFolder(path: string): string {
    return path.replace(/^testcases\/?/, "");
  }

  async function moveTo(destFolderPath: string) {
    const d = drag;
    setDrag(null);
    setDropTarget(null);
    if (!d) return;
    if (d.kind === "ct") {
      try {
        await api.moveTestcase(d.id, relFolder(destFolderPath));
        onChanged();
      } catch (e) {
        onError(e instanceof Error ? e.message : String(e));
      }
      return;
    }
    // pasta: soltar nela mesma ou numa descendente é inválido — ignora.
    if (isDescendantOrSelf(destFolderPath, d.path)) return;
    if (d.ctCount > 0) {
      // contém CTs: confirma antes de arrastar tudo junto.
      setPendingFolderMove({ srcPath: d.path, destPath: destFolderPath, ctCount: d.ctCount });
      return;
    }
    await doMoveFolder(d.path, destFolderPath);
  }

  async function doMoveFolder(srcPath: string, destPath: string) {
    try {
      await api.moveTcFolder(relFolder(srcPath), relFolder(destPath));
      onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function createFolder(parent: string, name: string) {
    const path = relFolder(parent) ? `${relFolder(parent)}/${name}` : name;
    try {
      await api.createTcFolder(path);
      setCreatingFolder(null);
      onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function deleteFolder(node: TreeNode) {
    setDeletingFolder(null);
    try {
      await api.deleteTcFolder(relFolder(node.path));
      onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function deleteCt(id: string) {
    setDeletingCt(null);
    try {
      await api.deleteTestcase(id);
      onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  function countAll(node: TreeNode): number {
    return node.files.length + node.dirs.reduce((acc, d) => acc + countAll(d), 0);
  }

  // contagem visível por pasta: com filtro ativo, quantos itens casaram
  function countMatching(node: TreeNode): number {
    if (!matchIds) return countAll(node);
    return (
      node.files.filter((f) => f.id && matchIds.has(f.id)).length +
      node.dirs.reduce((acc, d) => acc + countMatching(d), 0)
    );
  }

  // Renderiza os filhos de um nó (dirs, depois files) com conectores box-drawing.
  // `prefix` = string dos ancestrais ("│   "/"    "); cada filho recebe ├──/└──.
  function renderChildren(node: TreeNode, prefix: string): React.ReactNode[] {
    // com filtro ativo: só pastas com match e só arquivos que casaram
    const dirs = matchIds ? node.dirs.filter((d) => countMatching(d) > 0) : node.dirs;
    const files = matchIds
      ? node.files.filter((f) => f.id && matchIds.has(f.id))
      : node.files;
    const kids: { key: string; render: (branch: string, childPrefix: string) => React.ReactNode }[] = [
      ...dirs.map((d) => ({
        key: d.path,
        render: (branch: string, childPrefix: string) => {
          const isCollapsed = collapsed.has(d.path);
          return (
            <div key={d.path} className="repo-dir">
              <div
                className={`repo-row repo-folder ${dropTarget === d.path ? "drop-target" : ""} ${
                  drag?.kind === "folder" && drag.path === d.path ? "dragging" : ""
                }`}
                draggable
                onDragStart={(e) => {
                  e.stopPropagation();
                  setDrag({ kind: "folder", path: d.path, ctCount: countAll(d) });
                }}
                onDragEnd={() => {
                  setDrag(null);
                  setDropTarget(null);
                }}
                onDragOver={(e) => {
                  if (!drag) return;
                  // não permite soltar uma pasta dentro dela mesma ou de uma descendente
                  if (drag.kind === "folder" && isDescendantOrSelf(d.path, drag.path)) return;
                  e.preventDefault();
                  setDropTarget(d.path);
                }}
                onDragLeave={() => setDropTarget((t) => (t === d.path ? null : t))}
                onDrop={() => void moveTo(d.path)}
              >
                <span className="tree-prefix">{prefix + branch}</span>
                <button className="expand-btn" onClick={() => toggle(d.path)}>
                  {isCollapsed ? "▸" : "▾"}
                </button>
                <span className="repo-folder-name" onClick={() => toggle(d.path)}>
                  📁 {d.name}/
                </span>
                <span className="caption muted">
                  {matchIds ? `${countMatching(d)}/${countAll(d)}` : countAll(d)}
                </span>
                <span className="spacer" style={{ flex: 1 }} />
                <span className="repo-actions">
                  <button className="btn-sm" onClick={() => setCreatingFolder(d.path)}>
                    + pasta
                  </button>
                  <button className="btn-sm danger" onClick={() => setDeletingFolder(d)}>
                    Excluir
                  </button>
                </span>
              </div>
              {!isCollapsed && renderChildren(d, childPrefix)}
            </div>
          );
        },
      })),
      ...files.map((f) => ({
        key: f.path,
        render: (branch: string) => (
          <div
            key={f.path}
            className={`repo-row repo-file ${
              drag?.kind === "ct" && drag.id === f.id ? "dragging" : ""
            } ${selectedId === f.id ? "selected" : ""}`}
            draggable={!!f.id}
            onDragStart={(e) => {
              e.stopPropagation();
              if (f.id) setDrag({ kind: "ct", id: f.id });
            }}
            onDragEnd={() => {
              setDrag(null);
              setDropTarget(null);
            }}
          >
            <span className="tree-prefix">{prefix + branch}</span>
            <button
              className="repo-file-main"
              onClick={() => f.id && setSelectedId(f.id)}
              onDoubleClick={() => f.id && onOpen(f.id)}
              disabled={!f.id}
              title={`${f.path} — clique: detalhes · duplo clique: editor`}
            >
              <span className="mono muted">{f.id ?? "?"}</span>
              <span className="repo-file-title">{f.title}</span>
            </button>
            {f.status && (
              <span className={`status-dot dot-${f.status} caption`}>{f.status}</span>
            )}
            <span className="caption mono muted">{f.created ?? ""}</span>
            <span className="repo-actions">
              {f.id && (
                <button
                  className="btn-sm danger"
                  onClick={() => setDeletingCt({ id: f.id!, title: f.title })}
                >
                  Excluir
                </button>
              )}
            </span>
          </div>
        ),
      })),
    ];
    return kids.map((kid, i) => {
      const isLast = i === kids.length - 1;
      return kid.render(isLast ? "└── " : "├── ", prefix + (isLast ? "    " : "│   "));
    });
  }

  const empty = root.dirs.length === 0 && root.files.length === 0;

  return (
    <div className="repo">
      <div className="page-head">
        <h1 className="page-title">Test cases</h1>
        <span className="spacer" />
        <div className="head-controls">
          {extraActions}
          <button onClick={() => setImporting(true)}>Importar com IA</button>
          <button onClick={() => setCreatingFolder(root.path)}>Nova pasta</button>
          <button className="primary" onClick={onNew}>
            Novo test case
          </button>
        </div>
      </div>

      <div className="tc-filter-bar block">
        <input
          className="tc-filter-q"
          placeholder="Buscar por ID ou título…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select value={fStatus} onChange={(e) => setFStatus(e.target.value)} aria-label="Status">
          <option value="">Status</option>
          {["draft", "ready", "deprecated"].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select value={fPriority} onChange={(e) => setFPriority(e.target.value)} aria-label="Prioridade">
          <option value="">Prioridade</option>
          {["low", "medium", "high", "critical"].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select value={fType} onChange={(e) => setFType(e.target.value)} aria-label="Tipo">
          <option value="">Tipo</option>
          {["manual", "automated", "hybrid"].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <input
          className="tc-filter-tag"
          placeholder="tag"
          value={fTag}
          onChange={(e) => setFTag(e.target.value)}
        />
        {filterActive && (
          <button
            className="btn-sm"
            onClick={() => {
              setQ(""); setFStatus(""); setFPriority(""); setFType(""); setFTag("");
            }}
          >
            Limpar
          </button>
        )}
        {matchIds && (
          <span className="caption muted">{matchIds.size} resultado{matchIds.size === 1 ? "" : "s"}</span>
        )}
      </div>

      <div className="repo-layout">
      <div
        className={`repo-tree card ${dropTarget === root.path ? "drop-target" : ""}`}
        onDragOver={(e) => {
          // soltar no "vazio" = mover para a raiz
          if (drag && e.target === e.currentTarget) {
            e.preventDefault();
            setDropTarget(root.path);
          }
        }}
        onDrop={(e) => {
          if (e.target === e.currentTarget) void moveTo(root.path);
        }}
      >
        {empty ? (
          <div className="empty-state" style={{ border: "none" }}>
            <div className="empty-title">Repositório vazio</div>
            <div className="empty-body">
              Crie pastas para organizar e test cases em formato BDD
              (Given / When / Then). Arraste CTs entre pastas.
            </div>
          </div>
        ) : matchIds && matchIds.size === 0 ? (
          <div className="empty-state" style={{ border: "none" }}>
            <div className="empty-title">Nenhum caso de teste casa com o filtro</div>
            <div className="empty-body">
              Ajuste a busca ou limpe os filtros para ver a árvore completa.
            </div>
          </div>
        ) : (
          renderChildren(root, "")
        )}
      </div>
      {selectedId && (
        <TcDetailPanel
          id={selectedId}
          onClose={() => setSelectedId(null)}
          onOpenEditor={() => onOpen(selectedId)}
          onChanged={onChanged}
          onError={onError}
        />
      )}
      </div>

      {importing && (
        <AiImportModal
          onClose={() => setImporting(false)}
          onChanged={onChanged}
          onError={onError}
        />
      )}
      {creatingFolder !== null && (
        <NewFolderModal
          parent={creatingFolder === root.path ? "" : relFolder(creatingFolder)}
          onCreate={(name) => void createFolder(creatingFolder, name)}
          onClose={() => setCreatingFolder(null)}
        />
      )}
      {deletingFolder && (
        <ConfirmModal
          title="Excluir pasta"
          message={
            <>
              Excluir a pasta <span className="mono">{deletingFolder.name}/</span> e{" "}
              <strong>{countAll(deletingFolder)}</strong> item(ns) dentro dela? Tudo
              vai para a lixeira (<span className="mono">.arbites/trash/</span>).
            </>
          }
          confirmLabel="Excluir pasta"
          danger
          onConfirm={() => void deleteFolder(deletingFolder)}
          onCancel={() => setDeletingFolder(null)}
        />
      )}
      {deletingCt && (
        <ConfirmModal
          title="Excluir test case"
          message={
            <>
              Mover <span className="mono">{deletingCt.id}</span> ({deletingCt.title})
              para a lixeira?
            </>
          }
          confirmLabel="Mover para a lixeira"
          danger
          onConfirm={() => void deleteCt(deletingCt.id)}
          onCancel={() => setDeletingCt(null)}
        />
      )}
      {pendingFolderMove && (
        <ConfirmModal
          title="Mover pasta"
          message={
            <>
              A pasta{" "}
              <span className="mono">
                {pendingFolderMove.srcPath.split("/").pop()}/
              </span>{" "}
              contém <strong>{pendingFolderMove.ctCount}</strong> caso
              {pendingFolderMove.ctCount === 1 ? "" : "s"} de teste, que{" "}
              {pendingFolderMove.ctCount === 1 ? "será movido" : "serão movidos"} junto.
              Continuar?
            </>
          }
          confirmLabel="Mover pasta e casos de teste"
          onConfirm={() => {
            const p = pendingFolderMove;
            setPendingFolderMove(null);
            void doMoveFolder(p.srcPath, p.destPath);
          }}
          onCancel={() => setPendingFolderMove(null)}
        />
      )}
    </div>
  );
}

/**
 * Painel lateral de detalhes do CT (0064): consulta e ações rápidas sem sair
 * da árvore — o editor completo continua a um clique ("Abrir editor").
 */
function TcDetailPanel({
  id,
  onClose,
  onOpenEditor,
  onChanged,
  onError,
}: {
  id: string;
  onClose: () => void;
  onOpenEditor: () => void;
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [tc, setTc] = useState<TestCase | null>(null);
  const [defects, setDefects] = useState<Defect[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    let alive = true;
    setTc(null);
    api
      .testcase(id)
      .then((t) => alive && setTc(t))
      .catch((e) => onError(e instanceof Error ? e.message : String(e)));
    api
      .defects(`?testcase=${encodeURIComponent(id)}`)
      .then((d) => alive && setDefects(d))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [id, onError]);

  async function quickStatus(status: string) {
    try {
      const updated = await api.updateTestcase(id, { status });
      setTc(updated);
      toast("Status atualizado");
      onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="tc-panel card">
      <div className="card-head">
        <span className="mono">{id}</span>
        <span className="spacer" />
        <button className="btn-sm" onClick={() => {
          void navigator.clipboard?.writeText(id);
          toast("ID copiado", "info");
        }}>
          Copiar ID
        </button>
        <button className="modal-close" onClick={onClose} aria-label="Fechar painel">
          ×
        </button>
      </div>
      {!tc ? (
        <p className="caption muted"><span className="spinner" /> carregando…</p>
      ) : (
        <>
          <div className="tc-panel-title">{tc.title}</div>
          <div className="tc-panel-grid">
            <span className="caption muted">Status</span>
            <select
              value={tc.status}
              onChange={(e) => void quickStatus(e.target.value)}
              aria-label="Mudar status"
            >
              {["draft", "ready", "deprecated"].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <span className="caption muted">Tipo</span>
            <span>{tc.type}{tc.automation_target ? ` · ${tc.automation_target}` : ""}</span>
            <span className="caption muted">Prioridade</span>
            <span>{tc.priority}</span>
            <span className="caption muted">Story</span>
            <span className="mono">{tc.story_id ?? "—"}</span>
            <span className="caption muted">Squad</span>
            <span>{tc.squad_effective ?? "—"}</span>
            {(tc.tags ?? []).length > 0 && (
              <>
                <span className="caption muted">Tags</span>
                <span>{(tc.tags ?? []).map((t) => `#${t}`).join(" ")}</span>
              </>
            )}
          </div>
          {defects.length > 0 && (
            <div className="tc-panel-defects">
              <span className="caption muted">Defeitos vinculados</span>
              {defects.map((d) => (
                <div key={d.id} className="exec-item">
                  <span className="mono">{d.id}</span>
                  <span className="exec-item-msg">{d.title}</span>
                  <span className={`status-dot ${d.status === "open" ? "dot-col-failed" : "dot-col-passed"} caption`}>
                    {d.status}
                  </span>
                </div>
              ))}
            </div>
          )}
          <div className="toolbar" style={{ marginTop: 12 }}>
            <button className="primary" onClick={onOpenEditor}>
              Abrir editor
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function NewFolderModal({
  parent,
  onCreate,
  onClose,
}: {
  parent: string;
  onCreate: (name: string) => void;
  onClose: () => void;
}) {
  const [name, setName] = useState("");
  return (
    <Modal
      title={parent ? `Nova pasta em ${parent}/` : "Nova pasta"}
      onClose={onClose}
      footer={
        <>
          <button onClick={onClose}>Cancelar</button>
          <button
            className="primary"
            onClick={() => name.trim() && onCreate(name.trim())}
            disabled={!name.trim()}
          >
            Criar pasta
          </button>
        </>
      }
    >
      <div className="modal-field">
        <label htmlFor="folder-name">Nome da pasta</label>
        <input
          id="folder-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="ex.: frontend/login (aninhamento com /)"
          onKeyDown={(e) => {
            if (e.key === "Enter" && name.trim()) onCreate(name.trim());
          }}
        />
      </div>
    </Modal>
  );
}

// ------------------------------------------- importação via IA (doc §1.1)

function AiImportModal({
  onClose,
  onChanged,
  onError,
}: {
  onClose: () => void;
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [folder, setFolder] = useState("");
  const [items, setItems] = useState<GeneratedTestcase[] | null>(null);

  async function upload() {
    if (!file) return;
    setBusy(true);
    try {
      const data = await api.aiImportFile(file);
      setFolder(data.folder);
      setItems(data.testcases);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function accept(item: GeneratedTestcase) {
    try {
      await api.createTestcase({ title: item.title, folder, body: item.body });
      setItems((old) => (old ?? []).filter((i) => i !== item));
      onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <Modal
      title="Importar test cases com IA"
      onClose={onClose}
      footer={<button onClick={onClose}>Fechar</button>}
    >
      <p className="modal-text muted">
        Envie um .txt, .md ou .xml com casos de teste em formato livre. A IA
        identifica cada caso, sugere uma pasta e converte para BDD — nada é
        gravado sem você aceitar.
      </p>
      <div className="modal-field">
        <label>Arquivo</label>
        <input
          type="file"
          accept=".txt,.md,.xml"
          disabled={busy}
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <div className="toolbar" style={{ marginTop: 8 }}>
          <button className="primary" disabled={!file || busy} onClick={() => void upload()}>
            {busy ? "Processando com a IA…" : "Enviar"}
          </button>
          {file && !busy && <span className="muted caption">{file.name}</span>}
        </div>
        {busy && (
          <span className="muted caption">
            Modelos locais de raciocínio podem levar alguns minutos.
          </span>
        )}
      </div>

      {items && (
        <>
          <div className="modal-field">
            <label>Pasta de destino (sugerida pela IA)</label>
            <input
              className="mono"
              value={folder}
              onChange={(e) => setFolder(e.target.value)}
            />
          </div>
          {items.length === 0 ? (
            <p className="muted">
              Todos os itens foram aceitos ou nenhum caso foi identificado.
            </p>
          ) : (
            items.map((item, i) => (
              <div key={i} className="card" style={{ background: "var(--bg)", marginBottom: 8 }}>
                <div className="card-head" style={{ marginBottom: 8 }}>
                  <strong>{item.title}</strong>
                </div>
                <DocBody text={item.body} />
                <div className="toolbar">
                  <button className="primary" onClick={() => void accept(item)}>
                    Aceitar (criar CT)
                  </button>
                  <button onClick={() => setItems((old) => (old ?? []).filter((x) => x !== item))}>
                    Rejeitar
                  </button>
                </div>
              </div>
            ))
          )}
        </>
      )}
    </Modal>
  );
}
