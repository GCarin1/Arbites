# Spec Delta — capability: workspace-core

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/workspace-core/spec.md`

```ops
bump-version minor
append-requirement event: When o operador pede diagnóstico pela CLI, the system shall imprimir o que ESTE processo enxerga — o caminho onde o `.env` foi procurado, as chaves reconhecidas, as linhas descartadas com número e motivo, o valor literal de cada variável de CA, o resultado de abrir cada bundle apontado, uma conexão HTTPS real ao destino e as fontes de observabilidade configuradas.
append-requirement event: When o processo arranca, the system shall procurar o `.env` a partir do diretório atual e subindo até cinco pastas acima, e imprimir o caminho do arquivo efetivamente lido junto das chaves aplicadas.
append-requirement event: When um `.env` é lido, the system shall aceitar o marcador de ordem de bytes que o Bloco de Notas do Windows grava, para que a primeira linha do arquivo valha como as demais.
append-requirement unwanted: The system shall not imprimir valor de token ou de senha em nenhuma saída de diagnóstico; nome da chave, origem e comprimento bastam para reconhecer o erro, e um relatório feito para ser colado num chat vaza o que imprime.
append-requirement unwanted: The system shall not descartar em silêncio uma linha de `.env` que se parece com atribuição; um arquivo que parece certo e não chega ao processo não tem o que depurar.
append-criterion [verified] O `.env` da raiz do projeto é lido quando o comando roda de `backend/`, o caminho usado é impresso, e a busca para no quinto nível para não sequestrar um `.env` alheio — verified by `backend/tests/test_diagnostico.py`.
append-criterion [verified] O diagnóstico nomeia o diretório onde procurou o `.env`, aponta a linha descartada com número e motivo, denuncia o valor com barra duplicada, aspas, espaço ou `%VAR%`, diz quando a primeira variável de CA quebrada mascara uma seguinte válida, separa falha de certificado de falha de rede e PAT recusado, e não imprime senha nem token — verified by `backend/tests/test_diagnostico.py`.
```
