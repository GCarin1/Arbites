# Spec — audit

**Capability:** audit
**Status:** active
**Implementation:** verified
**Realizes:** n/a — capability nova (Agente Auditor), fora do escopo do intake original; surgiu de uma sessão de brainstorm sobre memória/contexto para IA
**Last updated:** 2026-07-20
**Version:** 0.2.0

## Purpose

Consolida sinais de qualidade que já existem no índice — warnings de
indexação, stories sem CT, defeitos abertos há muito tempo, automações
quebradas — num snapshot datado e persistido, sem exigir que alguém vasculhe
manualmente várias telas. Não é um daemon: cada rodada é um retrato pontual,
disparado sob demanda ou "lazy" (reaproveita a última rodada se ainda estiver
fresca, dispara uma nova se estiver velha). O objetivo é dar ao time (e à IA)
um checklist de saúde recorrente sem esconder nada atrás de um número — cada
achado cita categoria, severidade e a referência exata do que precisa de
atenção.

## Requirements (EARS)

### Ubiquitous

- The system shall expor `POST /audit/run` que roda uma auditoria
  imediatamente (`trigger: manual`), persiste o resultado como Markdown com
  frontmatter em `audits/AUD-NNNN.md` e devolve o relatório completo.
- The system shall consolidar 5 categorias de achados por rodada: `indexing`
  (warnings já existentes na tabela de indexação), `coverage` (stories sem
  nenhum caso de teste vinculado), `spec` (cobertura no nível critério EARS↔CT
  — critério sem CT vinculado = `uncovered_criterion`/warn; CT ready ou
  automated de story COM critérios que não declara qual cobre =
  `unlinked_testcase`/info), `defects` (defeitos abertos há mais de
  `audit.defect_aging_days` dias, default 14) e `automation` (repositórios de
  automação quebrados há mais de `audit.broken_automation_days` dias,
  default 3). O check de automação usa o mesmo `ci_monitoring.name_pattern`
  configurado que o relatório de automação — um padrão customizado não pode
  cegar o auditor silenciosamente.
- The system shall atribuir a cada achado uma severidade (`bad`, `warn` ou
  `info`), uma categoria, um código, uma mensagem legível e uma referência
  (`ref`) ao ID do artefato relacionado quando existir, e devolver os
  achados ordenados pior-primeiro (`bad` → `warn` → `info`).
- The system shall distinguir, entre os defeitos esquecidos, os que têm
  causa raiz registrada (`aging_defect`, severidade `warn`) dos que não têm
  nenhuma lição registrada (`forgotten_defect`); qualquer defeito aberto há
  2× o limiar configurado vira severidade `bad`.
- The system shall expor `GET /audit/history` (com `limit`, default 20,
  máx. 200) listando rodadas passadas — id, data, gatilho e totais por
  severidade/categoria — mais recente primeiro.
- The system shall expor `GET /audit/{id}` com o detalhe completo de uma
  rodada específica, incluindo a lista de achados.
- The system shall aceitar os limiares (`defect_aging_days`,
  `broken_automation_days`) e o intervalo de auto-execução
  (`auto_interval_hours`, default 24) configuráveis em `arbites.yaml`
  (`audit.*`), com defaults genéricos aplicados quando ausentes.

- The system shall apresentar na aba Auditoria um subtitle de propósito, um
  parágrafo curto do que o auditor consolida e quando roda, e a legenda das
  severidades (bad/warn/info com status-dot) — um usuário novo entende a
  aba sem sair dela.

### Event-driven

- When `GET /audit/latest` é chamado e não existe nenhuma rodada anterior,
  ou a mais recente passou de `audit.auto_interval_hours`, the system shall
  disparar uma nova rodada (`trigger: auto`) e devolver o resultado fresco.
- When `GET /audit/latest` é chamado e a rodada mais recente ainda está
  dentro do intervalo configurado, the system shall devolver essa rodada sem
  reprocessar.

### State-driven

- While não há nenhum achado numa rodada, the system shall devolver
  `total: 0` e uma lista de achados vazia — nunca omitir a rodada em si
  (o snapshot "tudo em dia" também fica registrado no histórico).

### Unwanted-behavior (must-not)

- The system shall not rodar como processo em background/daemon contínuo —
  toda rodada é síncrona, disparada por uma chamada HTTP (manual ou lazy).
- The system shall not tratar a ausência de `opened`/data no defeito como
  "não esquecido"; defeitos sem data de abertura são simplesmente ignorados
  pelo check de aging (sem dado, sem achado, nunca um falso positivo).
- The system shall not referenciar nenhuma empresa/organização/projeto
  específico nos códigos, mensagens ou defaults desta capability.
- The system shall not derrubar a auditoria por dado sujo editado
  externamente (workspace é editável fora do Arbites, ADR 0001) — um
  `created_at` sem fuso horário no check de automação vira "tempo
  desconhecido" no achado, nunca um erro 500.

### Optional

- Where `audit.defect_aging_days` ou `audit.broken_automation_days` são
  omitidos em `arbites.yaml`, the system may aplicar os defaults genéricos
  (14 e 3 dias, respectivamente).

## Acceptance criteria

1. [verified] `POST /audit/run` consolida warnings de indexação, stories
   sem CT, defeitos esquecidos (com/sem causa raiz) e automações quebradas
   num único relatório ordenado pior-primeiro, e persiste como
   `audits/AUD-NNNN.md` — verified by `backend/tests/test_audit.py`.
2. [verified] Defeitos abertos há mais que o limiar configurado (default
   14d) viram achado; abaixo do limiar não geram achado; sem causa raiz viram
   `forgotten_defect`, com causa raiz viram `aging_defect`, e o dobro do
   limiar sobe a severidade para `bad` — verified by
   `backend/tests/test_audit.py`.
3. [verified] `GET /audit/latest` dispara uma rodada nova (`trigger: auto`)
   quando não há histórico ou a última passou do intervalo configurado, e
   reaproveita a rodada existente quando ainda está fresca — verified by
   `backend/tests/test_audit.py`.
4. [verified] `GET /audit/history` lista rodadas passadas mais recente
   primeiro, e `GET /audit/{id}` devolve o detalhe completo (incluindo os
   achados) de uma rodada específica — verified by
   `backend/tests/test_audit.py`.
5. [verified] Os limiares de aging de defeito e de automação quebrada, e o
   intervalo de auto-execução, são configuráveis em `arbites.yaml`
   (`audit.*`) — verified by `backend/tests/test_audit.py`.
6. [verified] O check de automação quebrada respeita um
   `ci_monitoring.name_pattern` customizado, e um `created_at` sem fuso
   (editado externamente) não derruba a rodada — vira "tempo desconhecido"
   no achado — verified by `backend/tests/test_audit.py`.

7. [verified] A aba exibe subtitle, propósito, legenda de severidades e
   empty state instrutivo — verified by build + revisão visual
   (`frontend/src/components/Audit.tsx`).

8. [verified] A categoria `spec` acusa critério EARS sem CT vinculado
   (`uncovered_criterion`/warn) e CT ready/automated de story com critérios
   sem vínculo (`unlinked_testcase`/info) — verified by
   `backend/tests/test_audit.py` (`test_audit_spec_coverage_criteria`).

## Maturity

**MVP (committed):**

- 5 categorias de achado (indexação/cobertura/spec/defeitos/automação),
  severidade explícita, ordenação pior-primeiro, persistência como Markdown
  em `audits/`, execução sob demanda ou lazy (sem daemon), histórico de
  rodadas, limiares configuráveis.

**Future (aspirational, not committed):**

- Notificação proativa (ex.: e-mail/webhook) quando uma rodada encontra
  achados `bad` novos.
- Checks adicionais (ex.: CTs sem execução há N sprints).

## Out of scope for this spec

- Execução em background contínuo (daemon/scheduler real) — fora de escopo
  enquanto Arbites for local-first e não "sempre ligado".
- Notificações externas (e-mail, Slack, etc.).
