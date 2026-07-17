---
name: subprocess-python-windows-forca-pythonioencoding
description: Ao consumir stdout de um subprocess PYTHON como UTF-8 no Windows, defina PYTHONIOENCODING=utf-8 no env do processo — sem isso o filho emite no encoding do console (cp1252) e acentos viram mojibake ("Cenário" → "Cen�rio"), quebrando silenciosamente qualquer parse do stream.
when: O agente cria/depura um subprocess cujo executável é Python (behave, pytest, scripts) e decodifica o stdout como UTF-8 — especialmente se um parser de stream "não casa nada" só no Windows ou o log mostra � em acentos.
---

# Skill — subprocess-python-windows-forca-pythonioencoding

## When to use this skill

- O agente lê `proc.stdout` de um subprocess Python e decodifica com
  `utf-8` (mesmo com `errors="replace"`).
- Um regex/parser sobre o stream funciona no Linux/Mac e "não casa nada" no
  Windows; ou o log ao vivo exibe `�` onde havia acento.

## Procedure

1. No `env` do subprocess Python, defina `env["PYTHONIOENCODING"] = "utf-8"`
   — força o stdout/stderr do FILHO a emitir UTF-8, independente do code
   page do console do Windows (cp1252/cp850).
2. Mantenha `errors="replace"` na decodificação como rede de segurança —
   mas trate `�` no stream como SINTOMA (encoding errado na origem),
   não como normal.
3. Ao escrever um parser de stream, teste com conteúdo ACENTUADO no
   Windows — foi exatamente o parse de "Cenário:" (PT) que revelou o bug:
   o regex tinha o "á" correto e o stream trazia `Cen�rio`.
4. Para subprocess NÃO-Python, verifique como o programa decide o encoding
   de saída (muitos respeitam o console; alguns têm flag própria) — a
   variável só resolve filhos Python.

## Anti-patterns

- "Consertar" o parser aceitando `Cen.rio` (regex com curinga no acento) —
  esconde o mojibake que continua corrompendo o log visível ao usuário.
- Decodificar com `cp1252` fixo — quebra em consoles configurados para
  UTF-8 e em outros SOs.
- Ignorar porque "os testes passam" — os fixtures em EN não exercitam
  acento; o bug só aparece com dados PT reais.

## Related material

- `backend/arbites/runner.py` — `env["PYTHONIOENCODING"] = "utf-8"` no
  `_execute` (mudança 0076; o mojibake também afetava o terminal ao vivo
  da UI desde o M3, mascarado até o parser de progresso precisar casar
  "Cenário:").
- [[progresso-ao-vivo-fonte-oficial-reconcilia]] — o parser best-effort que
  expôs o problema.
