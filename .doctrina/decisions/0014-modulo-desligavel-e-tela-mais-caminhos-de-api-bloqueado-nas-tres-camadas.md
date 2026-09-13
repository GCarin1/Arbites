# ADR 0014 — Modulo desligavel e tela mais caminhos de API, bloqueado nas tres camadas

- **Status:** accepted
- **Date:** 2026-09-13
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** `backend/arbites/auth.py`, `backend/arbites/api.py`, `frontend/src/App.tsx`
- **Landed:** 2026-09-13 — `backend/arbites/auth.py`, `backend/arbites/api.py`, `frontend/src/App.tsx`, `backend/tests/test_authorization.py`

## Context

O painel de administracao ja tinha interruptores, mas eles governam
SUPERFICIE PERIGOSA — a capacidade tecnica de rodar subprocess, ler o
filesystem, abrir o `.env` de um projeto-alvo, chamar um provider de IA,
importar XML. Sao cinco, e cada um existe para reduzir o raio de estrago de
uma instancia exposta.

O que faltava era outra coisa: desligar uma FEATURE do produto. Uma
instalacao que nao usa Decisoes, Memoria, Daily ou Reunioes carrega esses
itens no menu para sempre, e o dono da instancia nao tem como tira-los.

Pior, o efeito do interruptor existente parava no meio do caminho. Desligado,
ele bloqueava a API e escondia o item do menu em tres dos cinco casos — mas
NENHUMA rota do cliente era bloqueada. Quem tivesse o link `#/ia` na mao
abria a tela normalmente, com os botoes todos la, e so descobria que a
feature estava desligada quando a primeira chamada voltava 403. Um
interruptor que deixa a tela abrir nao desligou nada; ele so escondeu o
caminho mais curto.

## Decision

Um **modulo** e uma tela do produto mais os caminhos de API que so ela usa.
Modulos sao desligaveis por interruptor, e o interruptor vale nas TRES
camadas, nesta ordem de autoridade:

1. **Backend** — o modulo entra na tabela `_GOVERNED`. Desligado, todo
   metodo em qualquer caminho dele responde 403. Esta e a UNICA camada que
   vale como seguranca; as outras duas sao sobre nao oferecer caminho morto.
2. **Rota do cliente** — `isReachable(aba)` passa a decidir o RENDER, nao so
   o menu. Deep link para modulo desligado nao monta a tela: mostra que o
   administrador desligou e devolve para a tela inicial.
3. **Menu** — o item nao aparece, como ja era.

Modulo e interruptor de superficie compartilham a mesma tabela `switches`, a
mesma rota `PUT /admin/switches/{name}` e o mesmo default (ausente = ligado,
para nao mudar o comportamento de quem ja instalou). O que os separa e um
campo `kind`, que a UI usa para agrupar: "Modulos do produto" e "Superficies
perigosas" sao listas diferentes porque respondem a perguntas diferentes.

**Limite de escopo:** o nucleo nao e desligavel. Requisitos, test cases,
execucoes, dashboard, defeitos, afazeres, auditoria, problemas, perfil e a
propria administracao nao tem interruptor — sem eles nao sobra produto, e um
interruptor que permite se trancar para fora do painel e uma armadilha.

## Alternatives considered

1. **Reaproveitar os interruptores de superficie como se fossem de modulo.**
   Recusado: `local_runner` e "rodar subprocess", nao "a tela de Automacao".
   Um admin que desliga o subprocess ainda quer configurar alvos e ver o
   historico. Juntar as duas perguntas num interruptor so torna as duas
   respostas erradas.
2. **Bloquear so no cliente, escondendo do menu e da rota.** Recusado: e
   maquiagem. A API continua respondendo, e qualquer cliente que nao seja o
   nosso usa a feature normalmente. Interruptor que nao muda o servidor nao
   e interruptor, e interface.
3. **Bloquear so no backend e deixar a tela abrir e falhar.** Recusado: e o
   que ja acontecia. A pessoa preenche um formulario para descobrir no envio
   que a feature nao existe mais nesta instancia.
4. **Desinstalar o modulo (build sem a tela).** Recusado: obriga a rebuildar
   para mudar de ideia, e o produto e local-first — ligar de volta tem que
   valer na hora, sem reiniciar processo, como ja vale para superficie.

## Consequences

**Positive**

- Desligar significa a mesma coisa nas tres camadas: quem desliga nao
  precisa saber qual delas estava faltando.
- O menu de uma instalacao passa a refletir o que ela usa.
- Um modulo novo nasce desligavel: basta a entrada no registro, e as tres
  camadas leem dali.

**Negative**

- Uma tela que hospeda mais de uma coisa some inteira com o modulo. O
  Context Pack mora na tela de IA e nao precisa de provider nenhum, mas vai
  junto quando o modulo de IA e desligado — o preco de o modulo ser a TELA e
  nao o botao.
- Dois registros parecidos (`SWITCHES` e `MODULES`) convidam a por a coisa
  no lugar errado. O criterio e unico: governa CAPACIDADE tecnica, e
  superficie; governa uma TELA, e modulo.

**Neutral**

- O estado continua no banco de contas (ADR 0011), nao no `arbites.yaml`:
  quem liga e desliga e o administrador da instancia pela UI, e a mudanca
  precisa valer sem reiniciar.
