# Spec — ci-automation

**Capability:** ci-automation
**Status:** deprecated
**Implementation:** verified — congelada pela ADR 0012: continua funcionando e no gate, fora do escopo ativo
**Realizes:** SC6
**Last updated:** 2026-09-17
**Version:** 0.16.0

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
- The system shall registrar por execução o repositório de origem que disparou a suíte, com ambiente e referência, declarado no bloco `trigger` do manifesto ou num rótulo de nome conhecido.
- The system shall responder a saúde e o volume de falhas recortados por repositório de origem, ao lado do recorte por repositório de teste — um repositório de teste serve vários produtos e só o primeiro recorte responde qual produto está quebrando.
- The system shall manter o histórico das análises lido do disco, de modo que reconstruir o índice não apague o registro que justifica uma decisão técnica.
- The system shall responder os anexos de todas as execuções do período como uma superfície própria, filtrável por tipo e por repositório de origem, e restringível às execuções que falharam.
- The system shall entregar em cada evidência o contexto da execução que a produziu — identificador, resultado, repositório de teste, repositório de origem e data — porque um anexo sem execução não é evidência de nada.
- The system shall aceitar um bundle de CA declarado por variável de ambiente e usá-lo na verificação TLS de toda chamada externa, para funcionar em rede que re-assina o tráfego.
- The system shall calcular taxa de sucesso e contagem de falhas apenas sobre execuções que deram veredito sobre o produto — concluída com sucesso, com falha, ou por estouro de tempo —, e apresentar junto do número o denominador e quantas ficaram de fora.

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
- When uma análise da observabilidade é pedida, the system shall montar o dossiê do período — saúde, sinais com meta e direção, instabilidade, achados de acessibilidade e os recortes por repositório de teste e de origem — e gravá-la como artefato do workspace junto com esse dossiê.
- When duas análises são comparadas, the system shall entregar os dois dossiês e os dois vereditos ao modelo, ordenados da mais antiga para a mais recente, em vez de calcular melhora no código.
- When uma chamada externa falha no transporte, the system shall recusá-la com mensagem própria distinguindo certificado não confiável de destino inalcançável, em vez de deixar a exceção subir como erro interno.
- When o operador pede o bundle de CA pela CLI, the system shall escrever um arquivo com as raízes públicas somadas aos certificados de autenticação de servidor do armazenamento do sistema operacional, conferir que o arquivo carrega, e imprimir a linha de declaração pronta.
- When o certificado de um destino não é aceito, the system shall dizer o nome de quem o emitiu, porque é esse nome que se procura na hora de obter o certificado certo.
- When um artifact chega sem manifesto, the system shall reconhecer o relatório Cucumber pela forma do conteúdo — uma lista de features com `elements` —, e não pelo nome do arquivo.
- When o operador pede o reprocessamento, the system shall reler os anexos já gravados no disco e refazer apenas o que é derivado deles, sem nenhuma chamada externa.
- When a busca de execuções é pedida, the system shall varrer apenas os intervalos da janela pedida que ainda não constam como cobertos, e registrar a cobertura por origem depois de varrer cada intervalo até o fim.
- When a busca é pedida com reconferência explícita, the system shall ignorar a cobertura registrada e varrer a janela inteira, sem apagar nem rebaixar o que já está no disco.
- When a limpeza total da observabilidade é pedida, the system shall responder antes quantas execuções, quantos anexos, quanto espaço e que intervalo de datas seriam removidos, para que a confirmação seja informada.
- When a limpeza total é confirmada, the system shall mover execuções e anexos para a lixeira, esquecer a cobertura de busca junto, e preservar as origens declaradas.

### State-driven

- While o job está em andamento, the system shall exibir apenas o status
  dos steps do workflow (não dos steps Gherkin — indisponíveis ao vivo).
- While a instancia nao tem cofre de credenciais do sistema operacional, the system shall responder que nao ha credencial em vez de falhar, mantendo a aplicacao inteira utilizavel.
- While nenhuma origem está declarada, the system shall dizer isso na tela de observabilidade junto do campo que a declara, em vez de apenas informar que nenhuma execução chegou.
- While o bundle de CA apontado por variável de ambiente não puder ser usado, the system shall dizer qual variável, qual caminho e por quê — no arranque e na lista de problemas —, em vez de cair no bundle padrão em silêncio.
- While a janela pedida já estiver inteiramente coberta, the system shall dizer que reaproveitou o período em vez de devolver um resultado vazio indistinguível de "não há execução nova".

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
- The system shall not inferir o repositório de origem de uma execução que não o declara; sem declaração a execução fica fora do recorte, porque adivinhar a topologia erraria na primeira exceção.
- The system shall not analisar um período sem execução ingerida; recusa dizendo que não há o que analisar, em vez de devolver um veredito sobre o vazio.
- The system shall not cortar a lista de evidências em silêncio nem deixar o limite pedido virar varredura da base; a lista anuncia quando foi truncada e o limite tem teto próprio.
- The system shall not oferecer desligar a verificação de certificado; a credencial do provedor viaja nessa conexão, e sem verificar o certificado não há como saber para quem.
- The system shall not pedir que se declare um bundle de CA quando já há um declarado; existir, ser arquivo e ser um bundle carregável são condições distintas, e cada falha tem a sua mensagem.
- The system shall not ler o armazenamento de certificados do sistema por conta própria numa chamada externa; ampliar a própria confiança sem que ninguém tenha dito nada é decisão de quem opera a máquina, e o comando que monta o bundle só escreve um arquivo que continua precisando ser declarado.
- The system shall not incluir no bundle certificado que não esteja habilitado para autenticar servidor; o armazenamento do sistema guarda também autoridades de assinatura de código e de e-mail.
- The system shall not classificar um anexo por um nome que o conteúdo desmente; um `result.json` que não é uma lista de features não é um relatório Cucumber, e chamá-lo assim troca um silêncio por uma mentira.
- The system shall not sobrescrever no reprocessamento o que veio do provedor — conclusão, commit, horários —, porque esses campos não estão nos anexos e regravá-los só pode perder informação.
- The system shall not registrar cobertura de um intervalo cuja varredura parou antes do fim, nem incluir na cobertura as últimas horas, porque uma execução longa conclui depois da varredura que a procuraria e o filtro do provedor é pela data de criação.
- The system shall not interromper a paginação ao encontrar uma página inteiramente já ingerida; quem decide a parada é a data, e parar pela página torna o passado mais antigo inalcançável.
- The system shall not contar execução cancelada ou pulada como falha, nem responder 0% num período em que nenhuma execução deu veredito; zero afirma que tudo quebrou, e a verdade é que nada foi medido.
- The system shall not apagar a observabilidade fora da lixeira nem executar a limpeza total para quem não administra a instância.

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
12. [verified] O bloco `trigger` é lido com nomes alternativos de campo e ganha do rótulo; a ausência não inventa origem; um repositório de teste servindo dois produtos responde uma taxa por produto; e o gráfico de erros conta volume de falha, não taxa — verified by `backend/tests/test_origem_do_disparo.py`.
13. [verified] O dossiê é recorte e não cópia do painel, marca o sinal sem direção declarada e destaca a instabilidade nova; a análise vira arquivo com o dossiê junto e sobrevive a um reindex; duas análises no mesmo dia não colidem; identificador com travessia de caminho é recusado; e o comparativo vai sempre da mais antiga para a mais recente, com os números das duas — verified by `backend/tests/test_analise_observabilidade.py`.
14. [verified] Cada evidência traz o contexto da execução; o recorte por falha e os filtros de tipo e origem funcionam; a ordem é da mais recente para a mais antiga; o resumo por tipo não encolhe com os filtros; o truncamento é anunciado e o limite tem teto; e o caminho do anexo não escapa de `ci/` — verified by `backend/tests/test_evidencias_periodo.py`.
15. [verified] Qualquer das três variáveis aponta o bundle, na ordem declarada, e um caminho inexistente cai no padrão em vez de estourar; erro de certificado e queda de rede saem com códigos e mensagens diferentes; e a ingestão registra o erro no resumo, sem exceção não tratada — verified by `backend/tests/test_tls_corporativo.py`.
16. [verified] Caminho inexistente, pasta no lugar do arquivo e arquivo que não é bundle são nomeados com a variável e o caminho; bundle carregável mas sem a CA do destino tem mensagem própria apontando o certificado raiz do proxy; e o problema aparece na lista sem ninguém disparar chamada externa — verified by `backend/tests/test_bundle_ca_quebrado.py`.
17. [verified] O bundle montado soma as raízes públicas às do armazenamento do sistema, carrega de verdade, descarta certificado sem uso de servidor e não duplica o que aparece em dois armazéns; fora do Windows o comando diz isso e aponta os caminhos usuais; sem nenhum certificado da máquina o recado é que a CA não está instalada; e a linha de declaração sai com barra normal — verified by `backend/tests/test_bundle_ca_do_sistema.py`.
18. [verified] O diagnóstico nomeia o emissor do certificado apresentado pelo destino e não derruba nada quando o destino está inalcançável — verified by `backend/tests/test_bundle_ca_do_sistema.py`.
19. [verified] O relatório Cucumber é reconhecido com qualquer nome de arquivo, JSON que não tem a forma não vira cenário, arquivo grande demais não é desserializado, o manifesto declarado continua vencendo a forma, e o reprocessamento do disco recupera o cenário perdido sem tocar nos campos do provedor e sem mudar nada na segunda passada — verified by `backend/tests/test_cenarios_por_forma.py`.
20. [verified] A segunda busca do mesmo período lista uma janela de dois dias em vez de trinta e não rebaixa artifact; ampliar de 30 para 90 dias varre só os 60 que faltam; a borda recente é sempre reconferida; uma execução antiga fora da última página deixa de ser inalcançável; reconferir varre sem apagar; e uma parada no meio não registra cobertura — verified by `backend/tests/test_busca_incremental.py`.
21. [verified] A taxa é calculada sobre as conclusivas (25 de 32, não de 45), estouro de tempo conta como falha, cancelada e pulada ficam fora do denominador e aparecem nomeadas ao lado, um período só de canceladas responde ausência em vez de zero, e a contagem de falhas por repositório deixa de somar o que não falhou — verified by `backend/tests/test_execucao_conclusiva.py`.
22. [verified] A prévia informa execuções, anexos, bytes e intervalo sem remover nada; a limpeza manda tudo para a lixeira e o índice esquece junto; a cobertura de busca é descartada com o dado; as origens declaradas permanecem; e quem não é admin recebe recusa — verified by `backend/tests/test_limpar_observabilidade.py`.

## Maturity

**MVP (committed):**

- workflow_dispatch, correlação, polling com timeline, coleta de artifact,
  PAT no keyring, `tests.yml` de exemplo.

**Future (aspirational, not committed):**

- Self-hosted runner na máquina local (registrado como alternativa em
  ADR; não entra na v1).

## Out of scope for this spec

- Execução local (ver `local-automation`).
