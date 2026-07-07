import type { ReactNode } from "react";

/**
 * Card de detalhes do modo leitura — agrupa os metadados com um cabeçalho que
 * carrega id/título, status e as ações (Editar/Excluir). Elimina a sensação de
 * campos flutuantes sobre o fundo (padrão Jira/GitHub Issues).
 */
export function DetailCard({
  id,
  title,
  status,
  actions,
  children,
}: {
  id: string;
  title: string;
  status?: ReactNode;
  actions: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="detail-card">
      <div className="detail-card-head">
        <span className="detail-title">
          <span className="mono muted">{id}</span>
          <span>{title}</span>
        </span>
        {status}
        <span className="spacer" />
        <div className="detail-actions">{actions}</div>
      </div>
      <div className="detail-card-body">{children}</div>
    </div>
  );
}

/** Campo rótulo/valor no modo leitura. */
export function ReadField({
  label,
  value,
  mono = false,
  wide = false,
}: {
  label: string;
  value: ReactNode;
  mono?: boolean;
  wide?: boolean;
}) {
  const empty = value === null || value === undefined || value === "";
  return (
    <div className={`read-field ${wide ? "wide" : ""}`}>
      <span className="read-label">{label}</span>
      <span className={`read-value ${empty ? "empty" : ""} ${mono ? "mono" : ""}`}>
        {empty ? "—" : value}
      </span>
    </div>
  );
}

/**
 * Render leve de markdown (sem dependência externa, só nós de texto):
 * cabeçalhos `#…`, linhas e parágrafos em branco. Suficiente para o modo
 * leitura de corpos de CT/requisito (Objetivo / Passos / Resultado esperado).
 */
const MENTION_RE = /@([A-Z]{1,6}-\d+)/g;

/** Renderiza uma linha, transformando menções `@ID` em links clicáveis. */
function renderLine(line: string, onMention: (id: string) => void): ReactNode {
  const parts: ReactNode[] = [];
  let last = 0;
  let key = 0;
  for (const m of line.matchAll(MENTION_RE)) {
    const start = m.index ?? 0;
    if (start > last) parts.push(line.slice(last, start));
    const id = m[1];
    parts.push(
      <button
        key={`m${key++}`}
        type="button"
        className="mention-link"
        onClick={() => onMention(id)}
        title={`Ir para ${id}`}
      >
        @{id}
      </button>,
    );
    last = start + m[0].length;
  }
  if (last < line.length) parts.push(line.slice(last));
  return parts.length ? parts : line;
}

export function DocBody({
  text,
  onMention,
}: {
  text: string | null | undefined;
  onMention?: (id: string) => void;
}) {
  const content = (text ?? "").replace(/\r\n/g, "\n").trimEnd();
  if (!content.trim()) {
    return <div className="doc-body empty">Sem conteúdo. Clique em Editar para preencher.</div>;
  }
  const lines = content.split("\n");
  return (
    <div className="doc-body">
      {lines.map((line, i) => {
        const heading = /^(#{1,6})\s+(.*)$/.exec(line);
        if (heading) {
          return (
            <p key={i} className="doc-h">
              {heading[2]}
            </p>
          );
        }
        if (line.trim() === "") {
          return <div key={i} className="doc-gap" />;
        }
        return (
          <p key={i} className="doc-line">
            {onMention ? renderLine(line, onMention) : line}
          </p>
        );
      })}
    </div>
  );
}
