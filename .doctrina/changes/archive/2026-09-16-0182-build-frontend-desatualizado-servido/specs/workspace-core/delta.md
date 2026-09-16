# Spec Delta — capability: workspace-core

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/workspace-core/spec.md`

---

`frontend/dist/` não é versionado, então `git pull` atualiza o código e não o
que o processo entrega. Quem pula o build continua vendo a interface anterior,
sem nada dizendo isso — e um conserto que "não apareceu" fica indistinguível
de um que não funcionou.

```ops
append-requirement event: When o processo sobe e o código do frontend é mais recente que o build servido, the system shall avisar no arranque que a interface entregue é a anterior, nomeando o comando de reconstrução com o caminho desta instalação.
append-requirement ubiquitous: The system shall incluir esse mesmo aviso na lista de problemas da API, para que a interface desatualizada — que continua consultando a API atual — possa mostrá-lo a quem não viu o terminal.
append-requirement unwanted: The system shall not tratar ausência de build como build velho, nem afirmar obsolescência quando o código-fonte não está ao lado do `dist`; sem o que comparar a resposta é "não sei", e a comparação por data de arquivo só justifica aviso, nunca recusa.
append-criterion [verified] Build em dia não avisa; `dist` mais antigo que `src` avisa no arranque e na lista de problemas, com o comando e o caminho corretos; `index.html`, `package.json` e `vite.config.ts` contam como fonte e `node_modules` não; e `dist` sem código ao lado (o caso do container) não afirma nada — verified by `backend/tests/test_build_desatualizado.py`.
set-header Last updated: 2026-09-16
bump-version minor
```
