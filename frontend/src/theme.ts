/**
 * Tema de leitura (change 0128).
 *
 * O produto é escuro e continua escuro — é a identidade dele. O que este
 * módulo acrescenta é a ESCOLHA, para quem trabalha em sala clara ou
 * projeta a tela numa reunião. Como a densidade, mora no navegador de quem
 * escolheu: é de quem lê num aparelho, não configuração do workspace.
 */

export const THEMES = ["system", "dark", "light"] as const;
export type Theme = (typeof THEMES)[number];

export const THEME_LABELS: Record<Theme, string> = {
  system: "Do sistema",
  dark: "Escuro",
  light: "Claro",
};

const KEY = "arbites.theme";

export function loadTheme(): Theme {
  try {
    const saved = localStorage.getItem(KEY);
    return (THEMES as readonly string[]).includes(saved ?? "")
      ? (saved as Theme)
      : "system";
  } catch {
    return "system";
  }
}

/** O tema efetivo: `system` consulta a preferência declarada pelo SO. */
export function resolveTheme(theme: Theme): "dark" | "light" {
  if (theme !== "system") return theme;
  try {
    return window.matchMedia("(prefers-color-scheme: light)").matches
      ? "light"
      : "dark";
  } catch {
    return "dark"; // sem matchMedia, o padrão do produto
  }
}

export function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute("data-theme", resolveTheme(theme));
}

export function saveTheme(theme: Theme): void {
  applyTheme(theme);
  try {
    localStorage.setItem(KEY, theme);
  } catch {
    /* sem storage a escolha vale só para esta sessão */
  }
}

/**
 * Lê um token do CSS. É assim que o gráfico deixa de ter cor cravada: ele
 * pergunta ao mesmo lugar de onde o resto da interface tira a sua.
 */
export function token(name: string, fallback = ""): string {
  try {
    return (
      getComputedStyle(document.documentElement).getPropertyValue(name).trim() ||
      fallback
    );
  } catch {
    return fallback;
  }
}
