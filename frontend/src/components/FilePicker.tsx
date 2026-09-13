import { useId, useRef, useState } from "react";

/**
 * Escolher arquivo com a mesma cara de qualquer outro botão do sistema
 * (change 0138).
 *
 * O `input[type=file]` nativo desenha "Escolher arquivo | Nenhum arquivo
 * escolhido" com a fonte, a altura e a cor do sistema operacional — num
 * celular ele aparece cru no meio de um formulário nosso, sem relação
 * nenhuma com o resto da tela, e o nome do arquivo escolhido some atrás de
 * reticências que não dá para ler. O perfil já resolvia isso escondendo o
 * input e clicando nele por um botão de verdade; aqui esse padrão vira
 * componente e passa a valer em toda parte.
 *
 * O input continua existindo e continua sendo o que recebe o arquivo — só
 * não é ele que aparece.
 */
export function FilePicker({
  onPick,
  accept,
  disabled,
  label = "Escolher arquivo",
  showName = true,
  className = "",
}: {
  onPick: (files: FileList | null) => void;
  accept?: string;
  disabled?: boolean;
  /** Texto do botão — diga o que o arquivo É, não "procurar". */
  label?: string;
  /** Mostrar o nome do escolhido ao lado (desligue quando o dono já mostra). */
  showName?: boolean;
  className?: string;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [name, setName] = useState<string | null>(null);
  const id = useId();

  return (
    <span className={`file-picker ${className}`.trim()}>
      <input
        ref={input}
        id={id}
        type="file"
        accept={accept}
        disabled={disabled}
        className="sr-only"
        onChange={(e) => {
          setName(e.target.files?.[0]?.name ?? null);
          onPick(e.target.files);
          // permite reescolher o MESMO arquivo: sem isto o segundo `change`
          // não dispara e o envio parece não responder
          e.target.value = "";
        }}
      />
      <button
        type="button"
        disabled={disabled}
        onClick={() => input.current?.click()}
      >
        {label}
      </button>
      {showName && name && (
        <span className="caption muted file-picker-name" title={name}>
          {name}
        </span>
      )}
    </span>
  );
}
