/**
 * Densidade de leitura (change 0126).
 *
 * A mesma tela serve a duas perguntas opostas — "quantos casos há neste
 * ciclo" e "o que diz este caso". A densidade é a resposta de quem está
 * lendo, e por isso mora no navegador de quem escolheu: é preferência de
 * uma pessoa num aparelho, não configuração do workspace.
 */

export const DENSITIES = ["compact", "default", "comfortable"] as const;
export type Density = (typeof DENSITIES)[number];

export const DENSITY_LABELS: Record<Density, string> = {
  compact: "Compacta",
  default: "Padrão",
  comfortable: "Confortável",
};

const KEY = "arbites.density";

export function loadDensity(): Density {
  try {
    const saved = localStorage.getItem(KEY);
    return (DENSITIES as readonly string[]).includes(saved ?? "")
      ? (saved as Density)
      : "default";
  } catch {
    return "default"; // navegador sem storage não é motivo para quebrar
  }
}

/** Escreve no elemento raiz: o CSS inteiro lê daí, sem componente saber. */
export function applyDensity(density: Density): void {
  if (density === "default") document.documentElement.removeAttribute("data-density");
  else document.documentElement.setAttribute("data-density", density);
}

export function saveDensity(density: Density): void {
  applyDensity(density);
  try {
    localStorage.setItem(KEY, density);
  } catch {
    /* sem storage a escolha vale só para esta sessão */
  }
}
