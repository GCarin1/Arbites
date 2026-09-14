# Change 0167-arbites-yaml-gerado-mostrava — arbites.yaml gerado mostrava cinco blocos enquanto o produto le onze, e o env de exemplo nao cobria o uso fora do container

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** workspace-core

## Why

arbites.yaml gerado mostrava cinco blocos enquanto o produto le onze, e o env de exemplo nao cobria o uso fora do container

## What

O `arbites.yaml` que nasce na primeira execução mostrava **cinco** blocos.
O produto lê **onze**. Os seis invisíveis:

`squads`, `audit`, `requirements` (termos vagos do lint EARS),
`metric_thresholds` (o semáforo do dashboard), `health_score` (os pesos da
nota) e `ci_monitoring`.

Todos funcionam, todos estão no código, e ninguém descobria: **configuração
que não aparece no arquivo é configuração que não existe**. A pessoa teria de
ler o fonte para saber que pode ajustar o semáforo das métricas.

E o arquivo era um `yaml.safe_dump` do dicionário — cinco chaves, zero linhas
de explicação. Agora nasce de um **template comentado**: cada bloco diz o que
faz, qual é o default e traz um exemplo comentado da forma esperada.

Duas coisas que o próprio arquivo passa a dizer, porque são a confusão mais
provável de quem configura:

- **segredo não entra ali** — o YAML fica DENTRO do workspace, que é
  versionável e feito para ser compartilhado (ADR 0008); chave e token vão
  para o cofre do SO ou para o `.env`;
- **mudar `ARBITES_ADMIN_PASSWORD` não redefine a senha de uma conta que já
  existe** — está no `.env.example`, porque é exatamente onde a pessoa vai
  procurar quando não conseguir entrar.

Template e dicionário são dois lugares dizendo a mesma coisa, e dois lugares
divergem sozinhos. Um teste compara os dois a cada execução da suíte, e outro
enumera as chaves realmente lidas no código e exige que apareçam no arquivo.

## Scope boundaries

- Não altera workspace existente: `ensure` só escreve quando o arquivo não
  existe, e isso continua valendo.
- Não muda o comportamento de nenhum bloco — só os torna visíveis.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] O arquivo gerado traz os onze blocos que o código consulta.
- [x] Ele nasce comentado e avisa que segredo não entra nele.
- [x] Ele carrega como a configuração padrão (template == default).
- [x] `ensure` não sobrescreve um arquivo existente.
- [x] O `.env.example` cobre o uso fora do container e o token do GitHub.

## Open questions

**Um defeito adjacente, NÃO corrigido aqui e que vale decidir:** o bloco
`github:` de um `automation_target` não existe no modelo Pydantic que a tela
grava (`AutomationTargetIn`). Salvar os targets pela interface reescreve
`automation_targets` com `model_dump`, e o bloco escrito à mão **é apagado em
silêncio**.

Hoje, configurar à mão e usar a tela são incompatíveis, e nada avisa. A
correção certa é a tela preservar o que não conhece em vez de reescrever o
bloco inteiro — mesmo princípio do vínculo externo da change 0145. Fica para
change própria porque muda comportamento de escrita, não documentação.

<!-- List unresolved decisions. Empty if none. -->
