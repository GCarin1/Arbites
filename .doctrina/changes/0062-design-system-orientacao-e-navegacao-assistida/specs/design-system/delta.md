# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

Note: 3ª das 3 slices (depende da fundação 0060). Quando implementada,
detalha os requisitos de orientação & navegação, prova o critério #4 do spec
e — sendo a última slice — avança a Implementation da capability para
`implemented`/`verified`.

---

Adiciona/detalha os requisitos de ORIENTAÇÃO & NAVEGAÇÃO:

### Ubiquitous

- The system shall exibir breadcrumbs nas áreas profundas (repositório de
  CTs em pastas, detalhe de execução, editores) mostrando o caminho até o
  item atual, cada nível clicável.
- The system shall manter o contexto visível: título da seção atual e rota
  destacada no menu em toda navegação.
- The system shall oferecer uma paleta de busca/comandos global (atalho de
  teclado, ex. Ctrl+K) que encontra qualquer artefato via `GET /search` e
  navega até ele de qualquer tela, além de ações rápidas (criar CT,
  execução, requisito).
- The system shall tornar clicável toda referência a artefato exibida em
  cards/tabelas (padrão de navegação por menção já existente em
  Todos/Decisions, estendido às demais telas).

### State-driven

- While a viewport é larga (monitor grande), the system shall limitar a
  largura útil de conteúdo de leitura/formulário e usar painéis
  laterais/colapsáveis, em vez de esticar blocos.

### Acceptance criteria (a acrescentar / provar)

4. [unverified] De qualquer tela, Ctrl+K encontra e navega até um CT por ID
   ou título; áreas profundas mostram breadcrumbs clicáveis; conteúdo de
   leitura tem largura limitada em viewport larga — verified by build +
   revisão visual documentada.

(Detalha o critério #4 placeholder do spec.)
