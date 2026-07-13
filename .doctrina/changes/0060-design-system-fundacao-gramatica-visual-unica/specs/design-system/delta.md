# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

Note: capability nova; o spec skeleton (Status draft, Implementation
planned) já existe via `doctrina spec new design-system`. Esta é a 1ª das 3
slices — quando implementada e aplicada, detalha a fundação e avança a
Implementation da capability de `planned` para `partial`.

---

Adiciona/detalha os requisitos de FUNDAÇÃO (componentes canônicos +
hierarquia + CTA):

### Ubiquitous

- The system shall definir `.btn-primary` e `.btn-secondary` como as ÚNICAS
  classes de botão, com cor, altura (`--h-control`) e raio (`--r-control`)
  fixos; toda tela usa uma das duas, sem botão com estilo ad-hoc.
- The system shall definir uma classe de input única (altura `--h-control`,
  estados focus/disabled consistentes) reutilizada em todos os formulários.
- The system shall definir um `.card` canônico (padding e borda únicos) e
  consolidar as variações atuais (`.chart-card`, `.todo-card`) sobre ele.
- The system shall definir o badge de status como um componente único
  (`status-dot` + rótulo), com a mesma linguagem de cor/forma em todas as
  telas.
- The system shall aplicar hierarquia visual: título (peso forte) vs
  subtítulo (peso leve), card principal maior que secundário, espaçamento
  entre blocos (`--s3`/`--s4`) e ausência de bordas duplicadas entre
  contêiner e conteúdo.

### Unwanted-behavior (must-not)

- The system shall not renderizar mais de uma ação de destaque por bloco;
  ações secundárias usam `.btn-secondary` (discretas).

### Acceptance criteria (a acrescentar / provar)

1. [unverified] Uma varredura das telas mostra botões/inputs/cards/badges
   usando exclusivamente as classes canônicas (sem estilo inline ad-hoc para
   esses tipos) — verified by `frontend` (revisão + build) e um teste de
   presença de classe onde couber.
2. [unverified] Cada bloco de tela tem no máximo um CTA de destaque; os
   demais são secundários — verified by revisão visual documentada.

(Substitui/expande os critérios #1 e #2 placeholder do spec.)
