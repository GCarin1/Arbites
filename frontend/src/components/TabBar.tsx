import { useEffect, useRef } from "react";

/**
 * A faixa de abas canônica do sistema (change 0135).
 *
 * Antes cada tela montava o seu `map` sobre `.tab-bar`, e a faixa era um
 * `flex` sem rolagem: em 390 px as quatro abas da IA não cabiam e a última
 * era CORTADA na borda do quadro — sem barra, sem reticências, sem nenhum
 * sinal de que havia mais. A aba continuava alcançável por teclado, mas
 * invisível para quem olha.
 *
 * Aqui a faixa rola de lado quando não cabe (o sinal de que há mais é a
 * sombra de borda em CSS, ver `.tab-bar` em styles.css) e a aba ativa é
 * trazida ao campo de visão a cada troca — clicar numa aba meio escondida
 * termina com ela inteira à vista.
 */
export function TabBar<K extends string>({
  tabs,
  value,
  onChange,
  className = "",
  label,
}: {
  tabs: readonly (readonly [K, string])[];
  value: K;
  onChange: (key: K) => void;
  className?: string;
  /** Nome da faixa para quem usa leitor de tela, quando há mais de uma. */
  label?: string;
}) {
  const bar = useRef<HTMLDivElement>(null);

  // A aba ativa entra no campo de visão sozinha. `inline: "nearest"` não
  // mexe na rolagem quando ela já está inteira à vista — só corrige quando
  // falta, que é o caso que incomoda.
  useEffect(() => {
    const active = bar.current?.querySelector<HTMLElement>('[aria-selected="true"]');
    active?.scrollIntoView({ inline: "nearest", block: "nearest" });
  }, [value]);

  return (
    <div
      ref={bar}
      className={`tab-bar ${className}`.trim()}
      role="tablist"
      aria-label={label}
    >
      {tabs.map(([key, text]) => (
        <button
          key={key}
          role="tab"
          aria-selected={value === key}
          className={`tab-btn ${value === key ? "active" : ""}`}
          onClick={() => onChange(key)}
        >
          {text}
        </button>
      ))}
    </div>
  );
}
