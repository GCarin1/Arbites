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
export function DocBody({ text }: { text: string | null | undefined }) {
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
            {line}
          </p>
        );
      })}
    </div>
  );
}
