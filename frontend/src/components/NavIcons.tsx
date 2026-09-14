/**
 * Ícones da navegação (change 0129).
 *
 * Desenhados aqui, com traço de 1.5 em grade de 16: são doze, e uma
 * biblioteca inteira para doze desenhos cobra mais do que entrega. Todos
 * herdam `currentColor`, então acompanham o estado do item e os dois temas
 * sem nenhuma regra extra.
 */

const PATHS: Record<string, string> = {
  // casa — a landing do dia
  home: "M2 6.5 8 2l6 4.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6.5Z M6.5 14V9.5h3V14",
  // documento com linhas — requisito
  requirements: "M4 1.5h5L12 4.5V14a.5.5 0 0 1-.5.5h-7A.5.5 0 0 1 4 14V2a.5.5 0 0 1 .5-.5Z M9 1.5V5h3 M6 8h4 M6 11h4",
  // prancheta com visto — caso de teste
  testcases: "M6 2.5H4.5a1 1 0 0 0-1 1V13a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V3.5a1 1 0 0 0-1-1H10 M6 2.5a2 2 0 1 1 4 0 M6 9l1.5 1.5L10.5 7.5",
  // play — execução
  executions: "M8 14A6 6 0 1 0 8 2a6 6 0 0 0 0 12Z M6.75 5.75 10.5 8l-3.75 2.25Z",
  // barras com eixo — dashboard, que é RETRATO
  dashboard: "M2 13.5h12 M4.5 11V6.5 M8 11V3.5 M11.5 11V8.5",
  // linha no tempo com o ponto do pico — observabilidade, que é SÉRIE.
  // Deliberadamente diferente das barras: as duas telas respondem perguntas
  // diferentes (ADR 0016), e ícone igual apagaria a distinção no menu.
  observability: "M1.5 12 5 8.5 7.5 11 11.5 4.5 M11.5 4.5a1.25 1.25 0 1 0 0 .01Z M14.5 7.5 12.4 5.4",
  // triângulo de alerta — defeito
  defects: "M8 2.5 14.5 13.5H1.5L8 2.5Z M8 6.5v3 M8 11.5v.5",
  // lista com vistos — afazeres
  todos: "M6 4.5h7 M6 8h7 M6 11.5h7 M2.5 4.5l1 1 1.5-2 M2.5 8l1 1 1.5-2 M2.5 11.5l1 1 1.5-2",
  // relógio com histórico — auditoria
  audit: "M8 14A6 6 0 1 0 8 2a6 6 0 0 0 0 12Z M8 5v3.25L10 9.5",
  // faísca — IA
  ia: "M8 2.5 9.25 6.25 13 7.5 9.25 8.75 8 12.5 6.75 8.75 3 7.5 6.75 6.25Z M12.5 2.5v2 M11.5 3.5h2",
  // bandeira — problemas do índice
  problems: "M4 14.5V2 M4 3h7l-1.5 2.5L11 8H4",
  // engrenagem — administração
  admin: "M8 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z M13 8a5 5 0 0 0-.1-1l1.3-1-1.5-2.6-1.6.6a5 5 0 0 0-1.7-1L9.2 1.5H6.8L6.6 3a5 5 0 0 0-1.7 1l-1.6-.6L1.8 6l1.3 1a5 5 0 0 0 0 2l-1.3 1 1.5 2.6 1.6-.6a5 5 0 0 0 1.7 1l.2 1.5h2.4l.2-1.5a5 5 0 0 0 1.7-1l1.6.6 1.5-2.6-1.3-1c.07-.33.1-.66.1-1Z",
  // as congeladas (ADR 0012) — presentes, sem investimento
  decisions: "M4.5 6a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z M4.5 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z M11.5 6a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z M4.5 6v4 M11.5 6c0 2.5-2 3-4 4",
  memory: "M3 3.5A1.5 1.5 0 0 1 4.5 2H13v10.5H4.5A1.5 1.5 0 0 0 3 14V3.5Z M13 12.5H4.5",
  daily: "M3 4.5h10a.5.5 0 0 1 .5.5v8a.5.5 0 0 1-.5.5H3a.5.5 0 0 1-.5-.5V5a.5.5 0 0 1 .5-.5Z M5.5 2.5v3 M10.5 2.5v3 M2.5 7.5h11",
  meetings: "M6 7.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z M2.5 13.5c0-2 1.6-3.5 3.5-3.5s3.5 1.5 3.5 3.5 M11 4.2a2 2 0 0 1 0 3.6 M12.2 10.4c1.3.5 2.3 1.7 2.3 3.1",
  automation: "M8.5 2 4 9h3.5L7 14l4.5-7H8L8.5 2Z",
  migration: "M8 2.5v7 M5 7l3 3 3-3 M3 12.5h10",
  profile: "M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z M2.5 14c0-3 2.5-4.5 5.5-4.5s5.5 1.5 5.5 4.5",
  // setas em ciclo — reindexar
  reindex: "M13.5 8a5.5 5.5 0 0 1-9.4 3.9 M2.5 8a5.5 5.5 0 0 1 9.4-3.9 M12 2v2.5H9.5 M4 14v-2.5h2.5",
};

export function NavIcon({ name }: { name: string }) {
  const d = PATHS[name];
  // Ícone faltando aparece como um traço neutro, não como um vazio. Um vazio
  // invisível foi exatamente como a Observabilidade ficou sem ícone desde a
  // change 0155 sem ninguém notar: nada quebrava, só sumia.
  if (!d) {
    return (
      <svg
        className="nav-icon"
        viewBox="0 0 16 16"
        width="16"
        height="16"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        aria-hidden="true"
        focusable="false"
      >
        <path d="M5 8h6" />
      </svg>
    );
  }
  return (
    <svg
      className="nav-icon"
      viewBox="0 0 16 16"
      width="16"
      height="16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {d.split(" M").map((parte, i) => (
        <path key={i} d={i === 0 ? parte : `M${parte}`} />
      ))}
    </svg>
  );
}
