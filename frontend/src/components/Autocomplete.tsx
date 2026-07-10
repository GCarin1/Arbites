import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { api } from "../api";
import type { SearchResult } from "../types";

/** Busca debounced de entidades (CT/requisito/execução/defeito/todo). */
function useSuggestions(query: string | null, kinds = ""): SearchResult[] {
  const [results, setResults] = useState<SearchResult[]>([]);
  // normaliza: "@CT-0001" ou "!@" viram "CT-0001"/"" — o '@' é gatilho, não filtro
  const term = (query ?? "").replace(/^[@!\s]+/, "").trim();
  useEffect(() => {
    if (term === "") {
      setResults([]);
      return;
    }
    let alive = true;
    const timer = setTimeout(() => {
      api
        .search(term, 8, kinds)
        .then((r) => alive && setResults(r.results))
        .catch(() => {});
    }, 120);
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [term, kinds]);
  return results;
}

function SuggestionBox({
  results,
  active,
  onPick,
  onHover,
}: {
  results: SearchResult[];
  active: number;
  onPick: (r: SearchResult) => void;
  onHover: (i: number) => void;
}) {
  return (
    <div className="ac-box">
      {results.map((r, i) => (
        <button
          key={`${r.kind}-${r.id}`}
          type="button"
          className={`ac-item ${i === active ? "active" : ""}`}
          onMouseDown={(e) => {
            e.preventDefault();
            onPick(r);
          }}
          onMouseEnter={() => onHover(i)}
        >
          <span className="mono">{r.id}</span>
          <span className="ac-title">{r.title ?? "—"}</span>
          <span className="ac-kind">{r.kind}</span>
        </button>
      ))}
    </div>
  );
}

/** Retorna true se a tecla foi tratada pela navegação da lista. */
function navKey(
  e: KeyboardEvent,
  results: SearchResult[],
  active: number,
  setActive: (i: number) => void,
  pick: (r: SearchResult) => void,
  close: () => void,
): boolean {
  if (results.length === 0) return false;
  if (e.key === "ArrowDown") {
    e.preventDefault();
    setActive((active + 1) % results.length);
    return true;
  }
  if (e.key === "ArrowUp") {
    e.preventDefault();
    setActive((active - 1 + results.length) % results.length);
    return true;
  }
  if (e.key === "Enter" || e.key === "Tab") {
    e.preventDefault();
    pick(results[active] ?? results[0]);
    return true;
  }
  if (e.key === "Escape") {
    e.preventDefault();
    close();
    return true;
  }
  return false;
}

// ------------------------------------------------------------- LinksInput

/** Campo de links (IDs separados por vírgula) com autocomplete por token. */
export function LinksInput({
  value,
  onChange,
  id,
}: {
  value: string;
  onChange: (v: string) => void;
  id?: string;
}) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const token = (value.split(",").pop() ?? "").trim();
  const results = useSuggestions(open ? token : null);

  function accept(r: SearchResult) {
    const parts = value.split(",");
    parts[parts.length - 1] = ` ${r.id}`;
    onChange(parts.join(",").replace(/^\s+/, "") + ", ");
    setActive(0);
    setOpen(true);
  }

  return (
    <div className="ac-wrap">
      <input
        id={id}
        className="mono"
        value={value}
        autoComplete="off"
        placeholder="CT-0001, EXEC-0002 — digite para sugerir"
        onChange={(e) => {
          onChange(e.target.value);
          setOpen(true);
          setActive(0);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={(e) => navKey(e, results, active, setActive, accept, () => setOpen(false))}
      />
      {open && results.length > 0 && (
        <SuggestionBox results={results} active={active} onPick={accept} onHover={setActive} />
      )}
    </div>
  );
}

// ---------------------------------------------------------- SingleRefInput

/**
 * Campo de referência a UM item existente: o usuário digita id ou título e o
 * autocomplete sugere; escolher grava o id. Substitui `<select>`/campo de id
 * cru em qualquer lugar onde se referencia um card (story, defeito, etc.).
 */
export function SingleRefInput({
  value,
  onChange,
  kinds = "",
  id,
  placeholder,
  onEnterNoMatch,
}: {
  value: string;
  onChange: (v: string) => void;
  kinds?: string;
  id?: string;
  placeholder?: string;
  onEnterNoMatch?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const results = useSuggestions(open ? value : null, kinds);

  function accept(r: SearchResult) {
    onChange(r.id);
    setOpen(false);
    setActive(0);
  }

  return (
    <div className="ac-wrap">
      <input
        id={id}
        className="mono"
        value={value}
        autoComplete="off"
        placeholder={placeholder ?? "digite id ou título…"}
        onChange={(e) => {
          onChange(e.target.value);
          setOpen(true);
          setActive(0);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={(e) => {
          const handled = navKey(e, results, active, setActive, accept, () =>
            setOpen(false),
          );
          if (!handled && e.key === "Enter" && onEnterNoMatch) {
            e.preventDefault();
            onEnterNoMatch();
          }
        }}
      />
      {open && results.length > 0 && (
        <SuggestionBox results={results} active={active} onPick={accept} onHover={setActive} />
      )}
    </div>
  );
}

// --------------------------------------------------------- MentionTextarea

/** Textarea com menções `@` a documentos (autocomplete que filtra ao digitar). */
export function MentionTextarea({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const [mention, setMention] = useState<{ query: string; start: number } | null>(null);
  const [active, setActive] = useState(0);
  const results = useSuggestions(mention?.query ?? null);

  function detect() {
    const el = ref.current;
    if (!el) return;
    const upto = value.slice(0, el.selectionStart);
    const m = /(^|\s)@([\w-]*)$/.exec(upto);
    if (m) {
      setMention({ query: m[2], start: el.selectionStart - m[2].length - 1 });
      setActive(0);
    } else {
      setMention(null);
    }
  }

  function accept(r: SearchResult) {
    const el = ref.current;
    if (!el || !mention) return;
    const before = value.slice(0, mention.start);
    const after = value.slice(el.selectionStart);
    const insert = `@${r.id} `;
    onChange(before + insert + after);
    setMention(null);
    const caret = (before + insert).length;
    requestAnimationFrame(() => {
      el.focus();
      el.selectionStart = el.selectionEnd = caret;
    });
  }

  return (
    <div className="ac-wrap">
      <textarea
        ref={ref}
        className="raw"
        style={{ minHeight: 140 }}
        value={value}
        placeholder={placeholder}
        spellCheck={false}
        onChange={(e) => onChange(e.target.value)}
        onKeyUp={detect}
        onClick={detect}
        onKeyDown={(e) => {
          if (mention) navKey(e, results, active, setActive, accept, () => setMention(null));
        }}
        onBlur={() => setTimeout(() => setMention(null), 150)}
      />
      {mention && results.length > 0 && (
        <SuggestionBox results={results} active={active} onPick={accept} onHover={setActive} />
      )}
    </div>
  );
}
