# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

O bloco `github` do alvo existia só no YAML: não tinha campo na tela nem
representação no modelo que a tela envia. Salvar o alvo pela tela apagava o
que tivesse sido escrito à mão, e o disparo respondia 422 sem que houvesse
lugar onde resolver.

```ops
append-requirement ubiquitous: The system shall oferecer na tela de configuração do alvo os campos de repositório, workflow e branch do GitHub, e preservá-los em toda gravação — nenhuma configuração feita à mão no `arbites.yaml` pode ser descartada por um salvamento pela tela.
append-requirement unwanted: The system shall not gravar um bloco `github` pela metade; repositório sem workflow (ou o contrário) é descartado, porque um bloco incompleto faz o disparo acusar falta de configuração com o bloco aparentemente presente no arquivo.
append-requirement event: When o disparo é pedido para um alvo sem repositório e workflow, the system shall recusá-lo nomeando a tela onde se configura, em vez de citar apenas a chave do arquivo de configuração.
append-criterion [verified] O bloco `github` sobrevive a duas gravações seguidas pela tela e continua no `arbites.yaml`; um bloco pela metade não é gravado; um alvo sem GitHub continua válido para execução local; e a recusa do disparo aponta Automação → Configurar — verified by `backend/tests/test_alvo_github.py`.
set-header Last updated: 2026-09-15
bump-version minor
```
