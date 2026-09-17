import { useId, useMemo } from "react";
import type { CiFatia } from "../types";

/**
 * Gráfico de pizza de uma divisão (change 0176).
 *
 * Série responde "está piorando?"; divisão responde "de que é feito o
 * período". São perguntas diferentes e nenhuma substitui a outra — por isso
 * a pizza existe ao lado da linha, não no lugar dela.
 *
 * A cor NÃO carrega o significado sozinha: cada fatia aparece na legenda com
 * rótulo e número. Quem não distingue as cores lê a mesma informação, e o
 * mesmo vale para quem imprime em preto e branco.
 */

const RAIO = 16;
const CENTRO = 18;

/** Papéis fixos primeiro (verde para sucesso, vermelho para falha, a escala
 *  de gravidade do axe), e uma sequência neutra para o que não tem papel. */
const PAPEIS: Record<string, string> = {
  success: "var(--success)",
  passed: "var(--success)",
  failure: "var(--danger)",
  failed: "var(--danger)",
  blocked: "var(--warning)",
  cancelled: "var(--text-muted)",
  timed_out: "var(--warning)",
  skipped: "var(--text-muted)",
  critical: "var(--danger)",
  serious: "#f0883e",
  moderate: "var(--warning)",
  minor: "#58a6ff",
  unknown: "var(--text-muted)",
};
const NEUTRAS = ["#388bfd", "#a371f7", "#3fb950", "#f0883e", "#db61a2", "#1f6feb"];

function cor(rotulo: string, indice: number): string {
  return PAPEIS[rotulo] ?? NEUTRAS[indice % NEUTRAS.length];
}

function arco(inicio: number, fim: number): string {
  // Uma fatia que cobre o círculo inteiro não pode ser um arco: início e fim
  // coincidem e o caminho some. Vira dois semicírculos.
  if (fim - inicio >= 1) {
    return (
      `M${CENTRO},${CENTRO - RAIO} A${RAIO},${RAIO} 0 1 1 ${CENTRO},${CENTRO + RAIO}` +
      ` A${RAIO},${RAIO} 0 1 1 ${CENTRO},${CENTRO - RAIO}Z`
    );
  }
  const ponto = (t: number) => {
    const ang = 2 * Math.PI * t - Math.PI / 2;
    return [CENTRO + RAIO * Math.cos(ang), CENTRO + RAIO * Math.sin(ang)];
  };
  const [x1, y1] = ponto(inicio);
  const [x2, y2] = ponto(fim);
  const grande = fim - inicio > 0.5 ? 1 : 0;
  return `M${CENTRO},${CENTRO} L${x1},${y1} A${RAIO},${RAIO} 0 ${grande} 1 ${x2},${y2} Z`;
}

export function Pizza({
  titulo,
  pergunta,
  fatias,
  rotulos = {},
  vazio = "sem dado no período",
  rodape,
}: {
  titulo: string;
  /** A pergunta que o bloco responde, para o gráfico não virar enfeite. */
  pergunta?: string;
  fatias: CiFatia[];
  /** Tradução do rótulo técnico para o que se lê na tela. */
  rotulos?: Record<string, string>;
  vazio?: string;
  /** O que ficou FORA da fatia. Sair da conta não é sair da tela: um total
      que não bate com o card ao lado, sem explicação, parece defeito. */
  rodape?: string;
}) {
  const id = useId();
  const total = useMemo(() => fatias.reduce((s, f) => s + f.value, 0), [fatias]);
  const arcos = useMemo(() => {
    let acumulado = 0;
    return fatias.map((f) => {
      const inicio = acumulado;
      acumulado += total ? f.value / total : 0;
      return { fatia: f, d: arco(inicio, acumulado) };
    });
  }, [fatias, total]);

  if (!fatias.length || !total) {
    return (
      <div className="obs-pizza">
        <h4>{titulo}</h4>
        <p className="obs-sem-ponto">{vazio}</p>
        {rodape && <p className="caption muted">{rodape}</p>}
      </div>
    );
  }
  return (
    <div className="obs-pizza">
      <h4 id={`${id}-t`}>{titulo}</h4>
      {pergunta && <p className="obs-pizza-pergunta">{pergunta}</p>}
      <div className="obs-pizza-corpo">
        <svg viewBox="0 0 36 36" role="img" aria-labelledby={`${id}-t`}>
          {arcos.map(({ fatia, d }, i) => (
            <path key={fatia.label} d={d} fill={cor(fatia.label, i)}>
              <title>{`${rotulos[fatia.label] ?? fatia.label}: ${fatia.value} (${fatia.pct}%)`}</title>
            </path>
          ))}
        </svg>
        <ul className="obs-pizza-legenda">
          {fatias.map((f, i) => (
            <li key={f.label}>
              <span className="obs-bolinha" style={{ background: cor(f.label, i) }} />
              <span className="obs-pizza-rotulo">{rotulos[f.label] ?? f.label}</span>
              <span className="obs-pizza-valor">
                {f.value} <span className="muted">({f.pct}%)</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
      {rodape && <p className="caption muted obs-pizza-rodape">{rodape}</p>}
    </div>
  );
}
