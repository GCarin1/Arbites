# Spec Delta — capability: executions

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/executions/spec.md`

---

A change 0111 pôs período no ciclo e a ADR 0013 fixou o vocabulário —
planejado, em andamento, fechado. As duas coisas pararam no cabeçalho do
ciclo aberto e não chegaram à lista, que é onde a pergunta aparece primeiro.

O resultado são duas lacunas na mesma tela:

- **O prazo não aparece.** Descobrir qual ciclo está atrasado exige abrir um
  por um. Uma data que ninguém vê de fora não responde "estamos no prazo?",
  que foi a pergunta que justificou criá-la.
- **O estado aparece cru.** A lista mostra `draft`, enquanto o cabeçalho do
  mesmo ciclo mostra "planejado". A ADR 0013 aceitou manter `draft` no disco
  justamente porque o nome de exibição resolveria — e ele só foi aplicado
  num dos dois lugares.

A lista já recebe `starts_on` e `ends_on` do backend: o `GET /executions`
faz `SELECT *` e o índice guarda as duas colunas desde a 0111. Não falta
dado, falta exibi-lo.

```ops
bump-version patch
append-requirement ubiquitous: The system shall exibir na lista de ciclos o prazo de cada um e a situação dele — no prazo, termina hoje ou em atraso —, e o estado no vocabulário do ciclo, o mesmo que o cabeçalho usa.
append-criterion [unverified] A lista de ciclos devolve o período de cada um, e um ciclo com prazo vencido é distinguível de um no prazo sem abrir nenhum dos dois — verified by `backend/tests/test_execution_cycle.py`.
```
