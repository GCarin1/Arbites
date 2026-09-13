# Spec Delta — capability: admin

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/admin/spec.md`

---

```ops
append-requirement ubiquitous: The system shall oferecer ao administrador um interruptor por modulo do produto — a tela mais os caminhos de API que so ela usa — separado dos interruptores de superficie perigosa e apresentado como controle de estado, nao como botao de acao.
append-requirement state: While um modulo esta desligado, the system shall recusar com 403 todos os caminhos de API desse modulo, omitir o item do menu e nao montar a tela quando alguem chega por link direto, apresentando no lugar o aviso de que o administrador desligou o modulo.
append-requirement unwanted: The system shall not oferecer interruptor para o nucleo do produto — requisitos, test cases, execucoes, dashboard, defeitos, afazeres, auditoria, problemas, perfil e a propria administracao —, para que ninguem se tranque para fora do painel.
append-criterion [unverified] Desligar um modulo recusa 403 em leitura e escrita de todos os caminhos dele e mantem o nucleo respondendo 200; religar devolve o acesso sem reiniciar o processo — verified by `backend/tests/test_authorization.py`.
append-criterion [unverified] Com o modulo de IA desligado, o item some do menu, o link direto nao monta a tela e a chamada ao provider responde 403 na mesma volta — verified by `frontend/src/App.tsx` + `backend/arbites/api.py`.
append-criterion [unverified] Papeis viewer e editor recebem 403 ao ligar ou desligar qualquer interruptor e em toda rota de liberar, recusar, desativar e reativar cadastro — verified by `backend/tests/test_authorization.py`.
bump-version minor
```
