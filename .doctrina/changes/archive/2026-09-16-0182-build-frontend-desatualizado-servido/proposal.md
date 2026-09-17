# Change 0182-build-frontend-desatualizado-servido — build do frontend desatualizado e servido em silencio apos um git pull

- **Status:** applied
- **Applied:** 2026-09-16
- **Date:** 2026-09-16
- **Owner:** Gcarini
- **Lane:** product (uncertain; signals: build)
- **Affects specs:** workspace-core

## Why

build do frontend desatualizado e servido em silencio apos um git pull

## What

- `backend/arbites/build_front.py` (novo): compara a data do conteúdo de
  `frontend/dist` com a de `src`, `index.html`, `package.json` e
  `vite.config.ts`, ignorando `node_modules` e ocultos. Devolve estado, o
  comando com o caminho desta instalação, e o aviso pronto.
- `__main__.py serve`: imprime o alerta ANTES do uvicorn subir, onde a pessoa
  já está olhando. Distingue "não há build" de "o build está velho".
- `api.py`: `_dist_do_frontend()` vira um lugar só (o gate precisa olhar
  exatamente a pasta que o mount serve) e o aviso entra em
  `_avisos_compostos`, que alimenta o sino e a aba Problemas.

## Scope boundaries

- Não reconstrói sozinho: rodar `npm` a partir do processo do servidor seria
  executar um build no arranque de quem só queria subir a aplicação, e
  falharia sem Node instalado. Avisar é o que cabe aqui.
- `dist` continua fora do git: versioná-lo encheria o histórico de bundle
  minificado e criaria conflito em todo merge.
- Data de arquivo não é ordem de commit — um `pull` pode deixar o fonte com
  data nova sem nada ter mudado. Por isso AVISO, nunca recusa: errar para o
  lado de avisar à toa custa uma linha; errar para o outro custa a tarde de
  quem está depurando a tela errada.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] Cenário real simulado: `dist` envelhecido e `python -m arbites serve` —
      o alerta sai como a PRIMEIRA linha do terminal, antes do uvicorn.
- [x] O caminho do container conferido: o Dockerfile copia só
      `frontend/dist`, sem `src` ao lado, e nesse caso nada é afirmado.

## Open questions

Nenhuma.
