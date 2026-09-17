# Change 0187-comando-diagnostico-mostra-processo — o comando que mostra o que o processo enxerga

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** workspace-core

## Why

Quatro rodadas seguidas de configuração de rede corporativa foram depuradas
por captura de tela: a pessoa mandava o `.env`, eu deduzia o que o Python
leria dali, e errava. O arquivo estava certo todas as vezes — o que faltava
era a diferença entre o arquivo e o que chegou ao processo, e essa diferença
não aparece em print nenhum.

São três diferenças possíveis, todas invisíveis:

1. o `.env` lido era o do **diretório atual** — e o comando documentado no
   README é `cd backend && python -m arbites serve`, enquanto o `.env` de
   todo mundo está na **raiz do projeto**, um nível acima;
2. uma linha pode ser descartada **em silêncio** — e o Bloco de Notas do
   Windows grava BOM, que fazia a PRIMEIRA chave do arquivo ser ignorada;
3. a variável já no ambiente **vence** o arquivo, por desenho.

A terceira é deliberada; a primeira e a segunda eram defeitos. A primeira era o
pior tipo: o arquivo existe, está correto, e o processo nunca o lê — sem um
sinal sequer. A segunda: `read_text(encoding="utf-8")` deixava o BOM colado
no nome da primeira chave, que então não passava no teste de nome e sumia
sem uma palavra.

## What

- `backend/arbites/diagnostico.py` (novo): `relatorio()` em seções — versão
  em execução e interpretador, `.env` (onde foi procurado, chaves
  reconhecidas, linhas descartadas, quem o ambiente venceu), CA/TLS (o
  `repr()` de cada variável, existência, e se o bundle abre), credencial
  (origem e comprimento, nunca o valor), rede (uma conexão HTTPS real,
  anônima e depois com o PAT) e workspace (as fontes de observabilidade).
- `python -m arbites diagnostico [--workspace ...] [--sem-rede]`.
- `envfile`: procura o `.env` subindo até cinco pastas acima do diretório
  atual (`localizar()`), lê com `utf-8-sig` (o defeito do BOM), ganha
  `descartadas()` —
  linha, motivo, e nunca o valor — e `pista_do_valor()`, que traduz barra
  duplicada, aspas sobrando, espaço nas pontas e `%VAR%`.
- `tls`: a mensagem da TELA passa a carregar a pista do valor e, quando nada
  está declarado, aponta o comando de diagnóstico.
- O arranque passa a imprimir QUAL `.env` foi lido — ou que não achou
  nenhum. Dizer o caminho é o que torna a busca para cima honesta.

## Scope boundaries

Não mexe na precedência ambiente > arquivo (é a regra, e está certa), não
passa a interpretar `export` nem expansão de variável no `.env` (um `.env`
que age como shell engana), e não ganha nenhuma forma de desligar a
verificação TLS — o PAT viaja nessa conexão.

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] The affected spec's acceptance criteria are met and cite their evidence.
- [x] `backend/tests/test_diagnostico.py`: 22 testes, incluindo o BOM, o
      mascaramento entre variáveis de CA, a separação entre falha de
      certificado e PAT recusado, e que senha e token não aparecem na saída.
- [x] Execução real do comando contra um `.env` sintético quebrado (BOM +
      barra duplicada + `export` + linha solta) e uma conexão HTTPS de
      verdade através de um proxy que inspeciona TLS.

## Open questions

Nenhuma.
