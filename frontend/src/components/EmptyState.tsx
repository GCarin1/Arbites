import type { ReactNode } from "react";
import { NavIcon } from "./NavIcons";

/**
 * O estado vazio canônico (change 0144).
 *
 * O padrão é o mesmo em Jira, Linear, Trello e GitHub, e tem quatro partes
 * nesta ordem — nenhuma delas é enfeite:
 *
 * 1. MARCA VISUAL discreta. É o que separa "vazio" de "ainda carregando";
 *    sem ela, uma lista vazia e uma lista que não chegou são a mesma tela.
 * 2. TÍTULO dizendo a SITUAÇÃO, não o erro. "Nenhum caso de teste ainda".
 * 3. CORPO de uma ou duas linhas: o que mora aqui e de onde vem. É o único
 *    momento em que a pessoa tem tempo de ler o modelo do produto.
 * 4. AÇÃO que resolve o vazio. Um vazio sem saída é um beco.
 *
 * E a regra que o Arbites vinha quebrando: a altura é do CONTEÚDO. Um card
 * de 400 px com três palavras no meio não é respiro, é área morta.
 *
 * Nem todo vazio pede ação: "nenhuma tentativa de login recusada" é uma boa
 * notícia, e inventar um botão ali seria ruído. Quando existe um próximo
 * passo óbvio, ele é um botão; quando não existe, o corpo basta.
 */
export function EmptyState({
  icon = "home",
  title,
  children,
  action,
  secondary,
  compact = false,
}: {
  /** Nome de um ícone do menu — reaproveita o vocabulário visual do produto. */
  icon?: string;
  title: string;
  children?: ReactNode;
  action?: { label: string; onClick: () => void };
  secondary?: { label: string; onClick: () => void };
  /** Dentro de um card que já tem borda e respiro próprios. */
  compact?: boolean;
}) {
  return (
    <div className={`empty-state ${compact ? "empty-compact" : ""}`.trim()}>
      <span className="empty-art" aria-hidden="true">
        <NavIcon name={icon} />
      </span>
      <div className="empty-title">{title}</div>
      {children && <div className="empty-body">{children}</div>}
      {(action || secondary) && (
        <div className="empty-actions">
          {action && (
            <button className="primary" onClick={action.onClick}>
              {action.label}
            </button>
          )}
          {secondary && <button onClick={secondary.onClick}>{secondary.label}</button>}
        </div>
      )}
    </div>
  );
}

/**
 * O vazio de um FILTRO é outro vazio (change 0144).
 *
 * Tratar os dois como um só faz a pessoa criar um item que já existe, só
 * porque o filtro o escondeu. Aqui a saída é limpar o filtro, nunca criar.
 */
export function NoMatches({
  what,
  onClear,
}: {
  /** O que se procurava, no plural: "defeitos", "casos de teste". */
  what: string;
  onClear: () => void;
}) {
  return (
    <div className="empty-state empty-compact">
      <span className="empty-art" aria-hidden="true">
        <NavIcon name="problems" />
      </span>
      <div className="empty-title">Nenhum resultado com esses filtros</div>
      <div className="empty-body">
        Existem {what} no workspace — o recorte atual é que não alcança
        nenhum deles.
      </div>
      <div className="empty-actions">
        <button className="primary" onClick={onClear}>
          Limpar filtros
        </button>
      </div>
    </div>
  );
}
