# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

Um bundle apontado e inutilizável era ignorado em silêncio, e a mensagem
mandava declarar a variável que já estava declarada — quem recebe isso
conclui, com razão, que a ferramenta não está lendo o arquivo.

```ops
append-requirement state: While o bundle de CA apontado por variável de ambiente não puder ser usado, the system shall dizer qual variável, qual caminho e por quê — no arranque e na lista de problemas —, em vez de cair no bundle padrão em silêncio.
append-requirement unwanted: The system shall not pedir que se declare um bundle de CA quando já há um declarado; existir, ser arquivo e ser um bundle carregável são condições distintas, e cada falha tem a sua mensagem.
append-criterion [verified] Caminho inexistente, pasta no lugar do arquivo e arquivo que não é bundle são nomeados com a variável e o caminho; bundle carregável mas sem a CA do destino tem mensagem própria apontando o certificado raiz do proxy; e o problema aparece na lista sem ninguém disparar chamada externa — verified by `backend/tests/test_bundle_ca_quebrado.py`.
set-header Last updated: 2026-09-17
bump-version patch
```
