import { useState } from "react";
import { api } from "../api";
import { ConfirmModal, Modal } from "./Modal";
import type { TreeNode } from "../types";

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
  const [dragId, setDragId] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<string | null>(null);
  const [creatingFolder, setCreatingFolder] = useState<string | null>(null); // pasta pai
  const [deletingFolder, setDeletingFolder] = useState<TreeNode | null>(null);
  const [deletingCt, setDeletingCt] = useState<{ id: string; title: string } | null>(null);

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

  async function moveTo(folderPath: string) {
    if (!dragId) return;
    try {
      await api.moveTestcase(dragId, relFolder(folderPath));
      onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setDragId(null);
      setDropTarget(null);
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

  function renderDir(node: TreeNode, depth: number, isRoot = false) {
    const isCollapsed = collapsed.has(node.path);
    const isDrop = dropTarget === node.path;
    return (
      <div key={node.path} className="repo-dir">
        {!isRoot && (
          <div
            className={`repo-row repo-folder ${isDrop ? "drop-target" : ""}`}
            style={{ paddingLeft: depth * 20 }}
            onDragOver={(e) => {
              if (dragId) {
                e.preventDefault();
                setDropTarget(node.path);
              }
            }}
            onDragLeave={() => setDropTarget((t) => (t === node.path ? null : t))}
            onDrop={() => void moveTo(node.path)}
          >
            <button className="expand-btn" onClick={() => toggle(node.path)}>
              {isCollapsed ? "▸" : "▾"}
            </button>
            <span className="repo-folder-name" onClick={() => toggle(node.path)}>
              📁 {node.name}/
            </span>
            <span className="caption muted">{countAll(node)}</span>
            <span className="spacer" style={{ flex: 1 }} />
            <span className="repo-actions">
              <button className="btn-sm" onClick={() => setCreatingFolder(node.path)}>
                + pasta
              </button>
              <button className="btn-sm danger" onClick={() => setDeletingFolder(node)}>
                Excluir
              </button>
            </span>
          </div>
        )}
        {(!isCollapsed || isRoot) && (
          <>
            {node.dirs.map((d) => renderDir(d, depth + 1))}
            {node.files.map((f) => (
              <div
                key={f.path}
                className={`repo-row repo-file ${dragId === f.id ? "dragging" : ""}`}
                style={{ paddingLeft: (depth + 1) * 20 }}
                draggable={!!f.id}
                onDragStart={() => f.id && setDragId(f.id)}
                onDragEnd={() => {
                  setDragId(null);
                  setDropTarget(null);
                }}
              >
                <button
                  className="repo-file-main"
                  onClick={() => f.id && onOpen(f.id)}
                  disabled={!f.id}
                  title={f.path}
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
            ))}
          </>
        )}
      </div>
    );
  }

  const empty = root.dirs.length === 0 && root.files.length === 0;

  return (
    <div className="repo">
      <div className="page-head">
        <h1 className="page-title">Test cases</h1>
        <span className="spacer" />
        <div className="head-controls">
          {extraActions}
          <button onClick={() => setCreatingFolder(root.path)}>Nova pasta</button>
          <button className="primary" onClick={onNew}>
            Novo test case
          </button>
        </div>
      </div>

      <div
        className={`repo-tree card ${dropTarget === root.path ? "drop-target" : ""}`}
        onDragOver={(e) => {
          // soltar no "vazio" = mover para a raiz
          if (dragId && e.target === e.currentTarget) {
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
        ) : (
          renderDir(root, 0, true)
        )}
      </div>

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
