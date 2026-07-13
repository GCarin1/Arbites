# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

Fix: seleção e execução de `.feature` em repositório SEM cenários tagueados
`@CT-` — requisitos a acrescentar (todos [unverified] até implementar):

### Ubiquitous

- The system shall listar no dropdown de features do run os arquivos
  `.feature` reais que o glob do target resolve no disco (mesma fonte do
  preview de browse), anotando por arquivo quantos cenários estão mapeados
  a CTs e quantos não — nunca uma lista vazia quando o disco tem features.
- The system shall derivar a regex de tag de cenário do prefixo de CT
  CONFIGURADO (`id_prefixes.testcase`), não de `CT-` fixo.

### Event-driven

- When o usuário roda um `.feature` inteiro cujos cenários não têm tag de
  CT, the system shall executar o arquivo mesmo assim (execution sem CTs
  vinculados ou com resultado "não mapeado" explícito), em vez de recusar
  com `422 empty_selection`.
- When um target tem features no glob mas nenhum cenário tagueado, the
  system shall explicar isso na UI (contagem de cenários sem tag + como
  taguear para rastreabilidade), em vez de exibir um select vazio.

### Unwanted-behavior (must-not)

- The system shall not usar fontes divergentes para o preview e para a
  operação da mesma lista — o que o browse mostra é o que o dropdown do
  run oferece.

### Acceptance criteria (a acrescentar)

- [unverified] Target salvo apontando para um repositório de features SEM
  tags de CT: o dropdown lista os arquivos do glob e rodar um arquivo
  inteiro cria a execution e dispara o behave — verified by teste de API
  com repositório sintético em tmp_path (incluindo caminho com
  espaços/acentos/vírgulas).
- [unverified] Com `id_prefixes.testcase` customizado, cenários tagueados
  com o prefixo configurado são mapeados normalmente — verified by teste
  de scan com prefixo custom.
