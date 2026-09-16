# Spec — ci-automation

**Capability:** ci-automation
**Status:** deprecated
**Implementation:** verified — congelada pela ADR 0012: continua funcionando e no gate, fora do escopo ativo
**Realizes:** SC6
**Last updated:** 2026-09-16
**Version:** 0.9.1

## Purpose

Dispara e acompanha runs no GitHub Actions (workflow_dispatch), coletando o
artifact com Cucumber JSON ao término para popular a execution com o mesmo
parser do run local. Design assume a restrição real da API do GitHub: logs
completos de job só existem após o término; ao vivo há apenas status de
workflow/jobs/steps do workflow.

## Requirements (EARS)

### Ubiquitous

- The system shall expor `POST /runs/ci`, `GET /runs/ci/{exec_id}/status`,
  `POST /runs/ci/{exec_id}/collect`, `GET/PUT /settings/github/token`.
- The system shall disparar via
  `POST /repos/{repo}/actions/workflows/{workflow}/dispatches` com `ref` e
  `inputs` (ex.: tags), criando execution `origin: github_actions` com
  objeto `ci {workflow_run_id, run_url, commit_sha, artifact_id}`.
- The system shall correlacionar o run buscando o run mais recente do
  workflow criado após o dispatch (janela de 30 s, filtro
  `event: workflow_dispatch`), pois a API não retorna o run id.
- The system shall armazenar o PAT fine-grained (escopo mínimo
  `actions:read+write` no repo do target) exclusivamente via `keyring` no
  cofre do SO.
- The system shall reutilizar na coleta o mesmo parser de Cucumber JSON do
  run local, movendo evidências do artifact para `evidences/`.
- The system shall documentar um `tests.yml` de exemplo: o workflow deve
  aceitar `workflow_dispatch` com input de tags e publicar JSON +
  screenshots como artifact.

- The system shall aceitar em `POST /runs/ci` os parâmetros opcionais
  `feature`, `environment (dev|cer|prd)`, `browser` e `source_repo`,
  repassando-os como inputs do workflow_dispatch quando informados.
- The system shall aceitar a credencial de CI pela variavel de ambiente do processo onde o cofre do sistema operacional nao existe, com precedencia sobre o cofre, sem nunca devolver o valor nem grava-lo no workspace.
- The system shall oferecer na tela de configuração do alvo os campos de repositório, workflow e branch do GitHub, e preservá-los em toda gravação — nenhuma configuração feita à mão no `arbites.yaml` pode ser descartada por um salvamento pela tela.
- The system shall permitir declarar e remover as origens da observabilidade pela própria tela, gravando-as no `arbites.yaml`, sem exigir que o operador edite o arquivo à mão.
- The system shall exportar o painel de observabilidade do período escolhido em PDF com os gráficos desenhados, em CSV com uma linha por medida, e em Markdown legível sem leitor especial.
- The system shall aceitar no manifesto do artifact um bloco `labels` de chave livre declarando o que aquela execução validou — componente, ambiente, camada — e continuar aceitando manifestos da versão anterior.
- The system shall registrar achados estruturados por execução com regra, gravidade, critério da WCAG, quantidade de elementos e página, lendo nativamente o JSON do axe-core publicado como anexo, sem exigir que o pipeline o reescreva.
- The system shall responder a saúde recortada por repositório de origem e por rótulo declarado, além da divisão do período por resultado de execução e de cenário.
- The system shall exibir a divisão do período em gráfico de pizza — execuções por resultado e cenários por resultado — ao lado das séries, porque divisão e tendência são perguntas diferentes.
- The system shall separar a observabilidade em Painel, Acessibilidade e Configuração, mantendo fora do painel diário o que se preenche uma vez.
- The system shall exibir a saúde recortada por repositório e por rótulo declarado, do pior para o melhor.
- The system shall derivar a marca d'água da ingestão apenas dos documentos de execução, ignorando os anexos gravados ao lado — um anexo nunca pode responder "este run já foi ingerido".

### Event-driven

- When um run CI está em andamento, the system shall fazer polling a cada
  10 s em `/actions/runs/{id}` e `/actions/runs/{id}/jobs`, exibindo a
  timeline dos steps do workflow (`queued → in_progress → completed`).
- When o workflow completa, the system shall baixar o artifact configurado
  (`artifact_name`), extrair o Cucumber JSON, parsear e popular
  `results[]`.
- When a API do GitHub retorna rate limit, the system shall aplicar
  backoff no polling.
- When alguem tenta guardar a credencial numa instancia sem cofre, the system shall recusar explicando a saida, em vez de aceitar em silencio ou falhar depois.
- When o disparo é pedido para um alvo sem repositório e workflow, the system shall recusá-lo nomeando a tela onde se configura, em vez de citar apenas a chave do arquivo de configuração.

### State-driven

- While o job está em andamento, the system shall exibir apenas o status
  dos steps do workflow (não dos steps Gherkin — indisponíveis ao vivo).
- While a instancia nao tem cofre de credenciais do sistema operacional, the system shall responder que nao ha credencial em vez de falhar, mantendo a aplicacao inteira utilizavel.
- While nenhuma origem está declarada, the system shall dizer isso na tela de observabilidade junto do campo que a declara, em vez de apenas informar que nenhuma execução chegou.

### Unwanted-behavior (must-not)

- The system shall not gravar o PAT em YAML, no índice ou em logs.
- The system shall not retornar o valor do token em
  `GET /settings/github/token` (status apenas).
- The system shall not gravar um bloco `github` pela metade; repositório sem workflow (ou o contrário) é descartado, porque um bloco incompleto faz o disparo acusar falta de configuração com o bloco aparentemente presente no arquivo.
- The system shall not gravar `workflow` ou `artifact` vazios como valor; ausentes significam "todos", e a chave vazia faria a ingestão procurar um nome que nunca existe.
- The system shall not depender de captura de tela para exportar os gráficos; a série é desenhada no próprio arquivo, porque exportar não pode exigir um navegador aberto.
- The system shall not afirmar melhora ou piora de um sinal sem direção declarada na exportação, pela mesma razão que não afirma na tela — a semântica é de quem instala.
- The system shall not oferecer como recorte um rótulo com um único valor ou com valores demais; um valor não divide nada e um por execução é identificador, não dimensão.
- The system shall not deixar a cor de uma fatia carregar sozinha o significado; rótulo, valor e porcentagem acompanham cada fatia na legenda.

### Optional

- Where um self-hosted runner local é usado (alternativa registrada em
  ADR), the system may coletar pelo mesmo mecanismo de artifact sem
  mudança de design.

## Acceptance criteria

1. [verified] Disparo pela UI cria execution `github_actions` e
   correlaciona o run id — verified by `backend/tests/test_ci_runs.py`.
2. [verified] Ao completar, collect produz execution idêntica em
   estrutura à de um run local — verified by `backend/tests/test_ci_runs.py`.
3. [verified] Token gravado via API está no keyring e nunca aparece em
   respostas, logs ou arquivos do workspace — verified by
   `backend/tests/test_ci_token.py`.

4. [verified] Inputs opcionais do dispatch (feature/environment/browser/
   source_repo) chegam ao workflow — verified by `backend/tests/test_ci_runs.py`.
5. [unverified] Instancia sem cofre responde a tela de problemas e o status do token sem erro, anuncia a falta com o remedio, recusa a gravacao explicando, e aceita a credencial pelo ambiente sem vazar o valor nem toca-lo no disco — verified by `backend/tests/test_sem_cofre.py`.
6. [verified] O bloco `github` sobrevive a duas gravações seguidas pela tela e continua no `arbites.yaml`; um bloco pela metade não é gravado; um alvo sem GitHub continua válido para execução local; e a recusa do disparo aponta Automação → Configurar — verified by `backend/tests/test_alvo_github.py`.
7. [verified] Instalação nova responde lista vazia; declarar grava no `arbites.yaml` e é exatamente o que a ingestão enxerga; workflow e artifact em branco não viram chave; origem sem repositório é descartada; escrever exige `admin` e ler não — verified by `backend/tests/test_origens_observabilidade.py`.
8. [verified] Os três formatos saem como anexo nomeado pelo período; o CSV traz uma linha por medida com a execução de origem; o Markdown não afirma piora de sinal sem direção declarada; o PDF é PDF com painel vazio, com série constante e com várias mudanças — verified by `backend/tests/test_export_observabilidade.py`.
9. [verified] O critério da WCAG sai da tag do axe, o número é de elementos e não de regras, JSON quebrado não derruba a ingestão, achado declarado e lido do axe têm a mesma forma e somam; rótulo de valor único e de cardinalidade alta ficam fora do recorte; e cada repositório responde a própria taxa, pior primeiro — verified by `backend/tests/test_manifesto_v2.py`, `backend/tests/test_recortes_observabilidade.py`.
10. [verified] As três abas abrem em 390px e 1440px sem estouro horizontal; as pizzas desenham com uma e com várias fatias; o recorte por repositório e por rótulo aparece com o pior primeiro; e a aba de acessibilidade lista regra, gravidade, critério WCAG, elementos e página — verified by `backend/tests/test_recortes_observabilidade.py`, `backend/tests/test_export_observabilidade.py`.
11. [verified] Um `analysis.md` no anexo não entra na marca d'água, um anexo nomeado como a chave de outro run não faz esse run ser pulado, e a marca atravessa a virada de ano — verified by `backend/tests/test_marca_dagua.py`.

## Maturity

**MVP (committed):**

- workflow_dispatch, correlação, polling com timeline, coleta de artifact,
  PAT no keyring, `tests.yml` de exemplo.

**Future (aspirational, not committed):**

- Self-hosted runner na máquina local (registrado como alternativa em
  ADR; não entra na v1).

## Out of scope for this spec

- Execução local (ver `local-automation`).
