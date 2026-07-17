import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { SearchResult } from "../types";

export interface QuickAction {
  id: string;
  label: string;
  hint?: string;
  run: () => void;
}

/**
 * Paleta de comandos global (design-system 0062): Ctrl/Cmd+K de qualquer
 * tela. Busca qualquer artefato via `GET /search` (mesmo endpoint do
 * autocomplete) e navega até ele, mais ações rápidas (novo CT, nova
 * execução…). Sem backend novo.
 */
export function CommandPalette({
  onClose,
  onNavigate,
  actions,
}: {
  onClose: () => void;
  onNavigate: (id: string) => void;
  actions: QuickAction[];
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // busca debounced; query vazia mostra as ações rápidas
  const term = query.replace(/^[@!\s]+/, "").trim();
  useEffect(() => {
    if (term === "") {
      setResults([]);
      return;
    }
    let alive = true;
    const timer = setTimeout(() => {
      api
        .search(term, 12)
        .then((r) => alive && setResults(r.results))
        .catch(() => {});
    }, 120);
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [term]);

  // itens visíveis: com texto → resultados de busca; sem texto → ações
  const matchingActions =
    term === ""
      ? actions
      : actions.filter((a) => a.label.toLowerCase().includes(term.toLowerCase()));
  const items: (
    | { kind: "result"; result: SearchResult }
    | { kind: "action"; action: QuickAction }
  )[] = [
    ...matchingActions.map((action) => ({ kind: "action" as const, action })),
    ...results.map((result) => ({ kind: "result" as const, result })),
  ];

  useEffect(() => {
    setActive(0);
  }, [query]);

  function choose(i: number) {
    const item = items[i];
    if (!item) return;
    if (item.kind === "result") onNavigate(item.result.id);
    else item.action.run();
    onClose();
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, items.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      choose(active);
    } else if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    }
  }

  return (
    <div
      className="cmdk-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="cmdk" role="dialog" aria-modal="true" aria-label="Busca global">
        <input
          ref={inputRef}
          className="cmdk-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Buscar CT, requisito, execução, defeito, decisão… ou uma ação"
          autoComplete="off"
        />
        <div className="cmdk-list">
          {items.length === 0 ? (
            <div className="cmdk-empty">
              {term === "" ? "Digite para buscar." : "Nada encontrado."}
            </div>
          ) : (
            items.map((item, i) =>
              item.kind === "result" ? (
                <button
                  key={`r-${item.result.kind}-${item.result.id}`}
                  type="button"
                  className={`cmdk-item ${i === active ? "active" : ""}`}
                  onMouseEnter={() => setActive(i)}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    choose(i);
                  }}
                >
                  <span className="mono">{item.result.id}</span>
                  <span className="cmdk-item-title">{item.result.title ?? "—"}</span>
                  <span className="cmdk-item-kind">{item.result.kind}</span>
                </button>
              ) : (
                <button
                  key={`a-${item.action.id}`}
                  type="button"
                  className={`cmdk-item ${i === active ? "active" : ""}`}
                  onMouseEnter={() => setActive(i)}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    choose(i);
                  }}
                >
                  <span className="cmdk-item-action">↳</span>
                  <span className="cmdk-item-title">{item.action.label}</span>
                  <span className="cmdk-item-kind">{item.action.hint ?? "ação"}</span>
                </button>
              ),
            )
          )}
        </div>
        <div className="cmdk-footer caption muted">
          <span>↑↓ navegar</span>
          <span>↵ abrir</span>
          <span>Esc fechar</span>
        </div>
      </div>
    </div>
  );
}
