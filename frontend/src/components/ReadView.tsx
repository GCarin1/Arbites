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
      {/* `read-empty`, não `empty`: a classe global de ESTADO vazio traz
          `padding: 48px 24px; text-align: center`, e o campo herdava isso —
          o travessão ficava centralizado num bloco de 117px (change 0131). */}
      <span className={`read-value ${empty ? "read-empty" : ""} ${mono ? "mono" : ""}`}>
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

/**
 * Tokenizador inline: `**negrito**`, `` `código` `` e menções `@ID`.
 *
 * Antes daqui só as menções eram reconhecidas, e um corpo vindo de fora —
 * a análise que a automação escreve em Markdown (change 0155) — chegava com
 * os asteriscos na cara do leitor. Marcação crua na tela não é "quase certo":
 * é a ferramenta dizendo que não leu o que recebeu.
 */
const INLINE_RE = /(\*\*[^*]+\*\*|`[^`]+`|@[A-Z]{1,6}-\d+)/g;

function renderLine(line: string, onMention?: (id: string) => void): ReactNode {
  const partes: ReactNode[] = [];
  let chave = 0;
  for (const pedaco of line.split(INLINE_RE)) {
    if (!pedaco) continue;
    if (pedaco.startsWith("**") && pedaco.endsWith("**") && pedaco.length > 4) {
      partes.push(<strong key={`n${chave++}`}>{pedaco.slice(2, -2)}</strong>);
      continue;
    }
    if (pedaco.startsWith("`") && pedaco.endsWith("`") && pedaco.length > 2) {
      partes.push(
        <code key={`c${chave++}`} className="mono">
          {pedaco.slice(1, -1)}
        </code>,
      );
      continue;
    }
    const mencao = /^@([A-Z]{1,6}-\d+)$/.exec(pedaco);
    if (mencao && onMention) {
      const id = mencao[1];
      partes.push(
        <button
          key={`m${chave++}`}
          type="button"
          className="mention-link"
          onClick={() => onMention(id)}
          title={`Ir para ${id}`}
        >
          @{id}
        </button>,
      );
      continue;
    }
    partes.push(pedaco);
  }
  return partes.length ? partes : line;
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
        const item = /^\s*[-*]\s+(.*)$/.exec(line);
        if (item) {
          return (
            <p key={i} className="doc-line doc-item">
              {renderLine(item[1], onMention)}
            </p>
          );
        }
        return (
          <p key={i} className="doc-line">
            {renderLine(line, onMention)}
          </p>
        );
      })}
    </div>
  );
}
