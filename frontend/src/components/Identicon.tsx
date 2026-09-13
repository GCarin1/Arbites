/**
 * Identicon determinístico, desenhado no cliente.
 *
 * O avatar padrão de uma conta sem foto é uma grade 5×5 espelhada no eixo
 * vertical, com células e matiz derivadas do hash do e-mail. A mesma conta
 * recebe sempre o mesmo desenho, e duas contas diferentes recebem desenhos
 * diferentes — sem nenhuma requisição a serviço externo. Gravatar foi
 * descartado justamente por exigir mandar o hash do e-mail de cada usuário
 * para fora, contra o local-first e a promessa de zero telemetria.
 */

/** FNV-1a de 32 bits: curto, estável entre navegadores e sem dependência. */
export function hashEmail(email: string): number {
  let hash = 0x811c9dc5;
  const normalized = email.trim().toLowerCase();
  for (let i = 0; i < normalized.length; i += 1) {
    hash ^= normalized.charCodeAt(i);
    // multiplicação FNV em 32 bits sem estourar o double do JS
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash >>> 0;
}

/**
 * A semente do desenho: as 15 células da metade esquerda (3 colunas × 5
 * linhas, espelhadas para as outras duas) e o matiz. Exportada separada do
 * componente porque é ela que carrega a promessa de determinismo.
 */
export function identiconSeed(email: string): { cells: boolean[]; hue: number } {
  const hash = hashEmail(email);
  const cells: boolean[] = [];
  for (let i = 0; i < 15; i += 1) {
    // cada célula lê um bit próprio do hash, re-embaralhado a cada volta
    const bit = (hash >>> (i % 32)) ^ (hash >>> ((i * 7 + 3) % 32));
    cells.push((bit & 1) === 1);
  }
  return { cells, hue: hash % 360 };
}

export function Identicon({
  email,
  size = 28,
  title,
}: {
  email: string;
  size?: number;
  title?: string;
}) {
  const { cells, hue } = identiconSeed(email);
  const color = `hsl(${hue} 58% 45%)`;
  const background = `hsl(${hue} 34% 92%)`;
  const squares = [];
  for (let column = 0; column < 5; column += 1) {
    // colunas 3 e 4 espelham 1 e 0: é o espelhamento que faz o desenho
    // parecer um rosto em vez de ruído.
    const source = column < 3 ? column : 4 - column;
    for (let row = 0; row < 5; row += 1) {
      if (!cells[source * 5 + row]) continue;
      squares.push(
        <rect key={`${column}-${row}`} x={column} y={row} width={1} height={1} />,
      );
    }
  }
  return (
    <svg
      className="identicon"
      viewBox="0 0 5 5"
      width={size}
      height={size}
      role="img"
      aria-label={title ?? `Avatar de ${email}`}
      shapeRendering="crispEdges"
    >
      <rect x={0} y={0} width={5} height={5} fill={background} />
      <g fill={color}>{squares}</g>
    </svg>
  );
}
