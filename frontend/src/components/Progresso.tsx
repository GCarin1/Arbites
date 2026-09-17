/**
 * Barra de progresso e esqueleto de carregamento (change 0193).
 *
 * ## Por que existe
 *
 * Exportar 30 dias de painel em PDF leva alguns segundos, e a tela não dizia
 * nada: o clique não mudava nada visível, e quem clicou não sabe se o pedido
 * saiu, se está indo, ou se o botão não funcionou. A reação natural é clicar
 * de novo — que é o pior desfecho, porque agora são dois PDFs sendo gerados.
 *
 * ## A regra das duas barras
 *
 * Quando o servidor manda `Content-Length`, dá para dizer QUANTO falta, e a
 * barra é determinada. Quando não manda — e ele não manda quando o arquivo é
 * gerado em fluxo —, inventar uma porcentagem seria mentir; a barra vira
 * indeterminada e diz apenas "está indo". Uma barra que anda sozinha até 90%
 * e para é pior que nenhuma: ela promete um número que não existe.
 */

export function Progresso({
  valor,
  rotulo,
}: {
  /** 0 a 1 quando o tamanho é conhecido; `null` para "está indo, sem saber
      quanto falta" — nunca uma porcentagem inventada. */
  valor: number | null;
  rotulo: string;
}) {
  const pct = valor === null ? null : Math.min(100, Math.round(valor * 100));
  return (
    <div className="progresso" role="status" aria-live="polite">
      <div
        className={`progresso-trilho${pct === null ? " indeterminado" : ""}`}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct ?? undefined}
        aria-label={rotulo}
      >
        <div
          className="progresso-barra"
          style={pct === null ? undefined : { width: `${pct}%` }}
        />
      </div>
      <span className="caption muted">
        {rotulo}
        {pct !== null && ` · ${pct}%`}
      </span>
    </div>
  );
}

/**
 * O esqueleto do que vai aparecer, no lugar de uma frase solta.
 *
 * "Carregando…" centralizado numa tela em branco não diz o que vem depois.
 * O esqueleto diz — e, quando o dado chega, nada salta de posição.
 */
export function Esqueleto({ linhas = 3, titulo }: {
  linhas?: number;
  titulo?: string;
}) {
  return (
    <div className="esqueleto" role="status" aria-live="polite">
      <span className="sr-only">{titulo ?? "Carregando"}</span>
      {Array.from({ length: linhas }, (_, i) => (
        <div key={i} className="esqueleto-linha" aria-hidden="true" />
      ))}
    </div>
  );
}
