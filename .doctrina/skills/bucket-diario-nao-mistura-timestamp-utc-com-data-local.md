---
name: bucket-diario-nao-mistura-timestamp-utc-com-data-local
description: Agregações "por dia" que juntam campos carimbados em UTC (datetime.now(timezone.utc)) com campos carimbados em data local (date.today()) perdem/deslocam dados silenciosamente para fusos horário atrás de UTC — sem erro, sem log, só o número errado. Normalize tudo pra data LOCAL antes de bucketar.
when: Ao escrever/revisar uma agregação "por dia" (heatmap, tendência diária, relatório de atividade) que combina MAIS DE UM campo de data/timestamp vindos de fontes diferentes do índice.
---

# Skill — bucket-diario-nao-mistura-timestamp-utc-com-data-local

## When to use this skill

- Vai escrever (ou revisar) uma função que agrega eventos "por dia" a partir
  de VÁRIAS tabelas/colunas de data do índice.
- Um teste que compara `day["algum_campo"]` com um valor esperado falha só
  em certos horários do dia, ou só pra alguém num fuso diferente do seu.

## Causa raiz

Este projeto tem DOIS padrões de carimbo de data coexistindo:
1. **UTC-aware**: `datetime.now(timezone.utc).isoformat()` — usado em eventos
   de execução (`result_events.at`, `executions.created_at`). Formato:
   `"2026-07-12T01:18:36+00:00"`.
2. **Data local, sem hora**: `date.today().isoformat()` — usado em campos
   "carimbo de criação" (`defects.opened_at`, `testcases.created`,
   `requirements.created`). Formato: `"2026-07-11"`.

Uma agregação que faz `substr(campo, 1, 10)` em AMBOS e bucketa pela mesma
chave "dia" está comparando a DATA UTC com a DATA LOCAL como se fossem a
mesma coisa. Num fuso atrás de UTC (Brasil, UTC-3): qualquer evento UTC-
carimbado a partir de ~21h local já pertence ao dia UTC SEGUINTE. Se a janela
da consulta é "até hoje LOCAL", esse evento cai FORA da janela — e some do
resultado. **Sem exceção, sem warning — só um número menor do que deveria.**

## Procedure

1. **Identifique a origem de cada campo de data usado na agregação**: é
   `datetime.now(timezone.utc)` (tem `T`, hora e `+00:00`) ou `date.today()`
   (só `YYYY-MM-DD`)? Campos de fontes diferentes quase sempre têm origem
   diferente neste projeto — não assuma que são compatíveis.
2. **Normalize os UTC-aware para data LOCAL antes de bucketar**:
   `datetime.fromisoformat(iso).astimezone().date().isoformat()`. Uma função
   utilitária (`_local_date`) que também é identidade para uma data local pura
   evita ter dois caminhos de código.
3. **Faça isso linha a linha em Python**, não tente resolver com `substr()`
   no SQLite — SQLite não conhece o fuso horário do processo.
4. **Teste sem depender do relógio real.** Um teste de integração que usa
   `datetime.now()` só reproduz o bug em certas horas do dia (como aconteceu
   aqui — passava de dia, falhava à noite). Escreva também um teste
   determinístico da função de conversão (`_local_date("2026-07-12T01:18:36
   +00:00") == datetime.fromisoformat(...).astimezone().date().isoformat()`)
   que falha/passa igual não importa quando o CI rodar.
5. **Verifique TODAS as consultas da mesma função** (ex.: um "anos com
   atividade" ao lado de um "dias com atividade") — o mesmo bug costuma se
   repetir em consultas irmãs que reusam os mesmos campos.

## Anti-patterns

- `substr(timestamp_utc, 1, 10)` tratado como "a data" sem conversão de fuso.
- Testar só com o relógio real, num único horário — mascara bugs que só
  aparecem em parte do dia (ou do ano, na virada UTC×local).
- "Funciona na minha máquina" sem checar o fuso horário local do
  desenvolvedor vs. UTC — o bug é invisível pra quem está em UTC ou fusos à
  frente dele.

## Related material

- `backend/arbites/metrics.py` — `_local_date`, `activity_heatmap`,
  `_activity_years`.
- `backend/tests/test_activity_heatmap.py` —
  `test_local_date_converts_utc_iso_consistently_with_python`.
- `backend/arbites/executions.py` — `_now()` (UTC); confronto com
  `date.today()` usado em `create_defect`/`create_testcase`.
