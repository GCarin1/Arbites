# Spec Delta — capability: ai-assist

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ai-assist/spec.md`

---

Área de IA como workspace de assistente — requisitos a acrescentar (todos
[unverified] até implementar):

### Ubiquitous

- The system shall abrir a área de IA na visão de TRABALHO (gerar, revisar,
  casos negativos, context pack); a configuração de providers é seção
  secundária, não a primeira coisa da tela.
- The system shall exibir o contexto ativo que acompanhará o próximo pedido
  de IA: memória do perfil (ativa ou não), recap de decisões+lições
  recentes (capability `project-memory`) e lições por similaridade quando
  aplicável.
- The system shall exibir o histórico de interações de IA na própria área
  (o que foi gerado/revisado, quando, sobre qual artefato), reutilizando os
  eventos de agente da capability `project-memory`
  (`GET /memory/timeline?kinds=agent`) — sem endpoint novo.
- The system shall oferecer, em cada função sem entrada preenchida, um
  exemplo de uso clicável que demonstra o formato esperado.

### Event-driven

- When a IA devolve um preview, the system shall apresentar explicitamente
  O QUE será criado/alterado (lista/diff item a item) antes do aceite — o
  aceite continua sendo a única escrita em disco.

### Acceptance criteria (a acrescentar)

11. [unverified] A tela abre na visão de trabalho com a config recolhida; o
    contexto ativo (perfil/recap/lições) é visível antes de gerar —
    verified by revisão visual documentada.
12. [unverified] O histórico de interações lista os agent_events existentes
    e cada preview mostra o que será criado antes do aceite — verified by
    build + revisão visual documentada (endpoint já coberto por
    `backend/tests/test_project_memory.py`).

### Maturity → MVP (acrescentar)

- Workspace de assistente: visão de trabalho primeiro, contexto ativo
  visível, histórico de interações, exemplos de uso, preview explícito
  antes do aceite.
