# Spec — home

**Capability:** home
**Status:** active
**Implementation:** planned — entrega na change 0080 (backlog da varredura de 2026-07-19)
**Realizes:** n/a — capability nova (landing de orientação diária), fora do intake original; nasceu da varredura de melhorias de usabilidade
**Last updated:** 2026-07-19
**Version:** 0.1.0

## Purpose

Tela "Hoje" — a landing do Arbites. O app hoje abre direto em Test cases
(uma lista fria); esta capability dá ao QA uma visão de chegada do dia:
runs de automação ativos, últimas execuções, defeitos abertos, afazeres do
dia, daily pendente e problemas do workspace — tudo composto de endpoints
que já existem, sem cálculo novo. Orientação em 5 segundos, com atalho para
cada área.

## Requirements (EARS)

### Ubiquitous

- The system shall exibir uma aba "Hoje" como primeira do menu e aba
  default ao abrir o app, compondo: runs ativos (`GET /runs/active`),
  últimas executions, defeitos abertos, afazeres do dia (`GET /todos`),
  status da daily do dia e contagem de problemas — exclusivamente de
  endpoints existentes.
- The system shall oferecer, em cada card da tela Hoje, navegação direta
  para a aba correspondente (mesmo `onNavigate`/troca de aba dos demais
  componentes).

### State-driven

- While o workspace está vazio (sem requisitos/CTs), the system shall
  exibir na tela Hoje um empty state de primeiro uso apontando o próximo
  passo (criar epic → story → CT), em vez de cards vazios.

### Unwanted-behavior (must-not)

- The system shall not introduzir endpoint agregador novo no backend para
  esta tela — a composição é do frontend, sobre APIs existentes.
- The system shall not bloquear a renderização da tela por falha de UMA
  fonte (cada card falha isolado, sem derrubar a página).

## Acceptance criteria

1. [unverified] O app abre na aba Hoje com os cards compostos de endpoints
   existentes e navegação para cada área — verified by build + revisão
   visual (`frontend/src/components/Home.tsx`).
2. [unverified] Workspace vazio mostra o empty state de primeiro uso; falha
   de uma fonte não derruba a tela — verified by build + revisão visual.

## Maturity

**MVP (committed):**

- Aba Hoje default com cards de runs ativos, últimas executions, defeitos
  abertos, afazeres do dia, daily pendente e problemas; navegação por card;
  empty state de primeiro uso.

**Future (aspirational, not committed):**

- Card configurável (usuário escolhe quais blocos aparecem).

## Out of scope for this spec

- Métricas/gráficos (ver `reporting` — a tela Hoje não duplica o dashboard).
- Qualquer agregação nova de backend.
