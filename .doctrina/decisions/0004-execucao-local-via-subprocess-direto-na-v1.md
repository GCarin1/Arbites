# ADR 0004 — Execucao local via subprocess direto na v1

- **Status:** accepted
- **Date:** 2026-07-03
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** n/a — decisão de design do intake; nenhuma implementação ainda (landará com o M3)
- **Landed:** —

## Context

A automação roda na mesma máquina que o Arbites (plataforma local,
single-user). Um agente de execução separado adicionaria deploy, protocolo
e ciclo de vida próprios — exatamente o tipo de escopo que matou o
Probatio.

## Decision

Runs locais usam `subprocess` da stdlib (`asyncio.create_subprocess_exec`)
direto do backend, com lock e fila FIFO por target, timeout configurável e
streaming de stdout via SSE. Agente separado só será considerado quando
houver execução remota própria.

## Alternatives considered

1. Agente de execução separado (daemon/worker) — rejeitado:
   overengineering para plataforma local; complexidade sem benefício na
   v1.

## Consequences

**Positive**

- Zero infraestrutura adicional; um processo sobe tudo.

**Negative**

- Execução compete por recursos com o backend; mitigado por uma execução
  por target e timeout.

**Neutral**

- O contrato de coleta (JSON do Behave + evidências) independe de onde o
  processo roda, preservando o caminho para um agente futuro.
