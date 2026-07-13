# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

Note: 2ª das 3 slices (depende da fundação 0060). Quando implementada,
detalha os requisitos de estados & feedback e prova o critério #3 do spec.

---

Adiciona/detalha os requisitos de ESTADOS & FEEDBACK:

### Ubiquitous

- The system shall confirmar visualmente toda persistência bem-sucedida
  (feedback "salvo" transitório — toast ou inline), em vez de salvar em
  silêncio.
- The system shall usar um indicador de carregamento único e consistente
  (spinner/skeleton canônico) em toda busca/carga de dados.
- The system shall exibir falhas PERTO da ação que falhou, com mensagem
  acionável — o banner global é fallback, não o canal primário.
- The system shall usar o padrão `.empty-state` (título + instrução útil de
  como sair do vazio) em toda lista/painel vazio.
- The system shall sinalizar formulários/modais com alterações não salvas
  (dirty) e pedir confirmação ao descartar.

### Unwanted-behavior (must-not)

- The system shall not exibir blocos de explicação longos onde a interface
  já é autoexplicativa — ajuda contextual = 1 linha de apoio e/ou tooltip.

### Acceptance criteria (a acrescentar / provar)

3. [unverified] Os 5 estados (salvo/carregando/falhou/vazio/dirty) têm
   representação canônica reutilizada nas telas principais; fechar um modal
   dirty pede confirmação — verified by build + revisão visual documentada
   (e teste de componente onde couber).

(Detalha o critério #3 placeholder do spec.)
