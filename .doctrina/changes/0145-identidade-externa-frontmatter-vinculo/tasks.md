# Tasks — Change 0145-identidade-externa-frontmatter-vinculo

- [ ] Escrever a spec da capability `integrations` (vem no delta ADDED).
- [ ] Definir o formato do vínculo no frontmatter e a leitura/escrita dele,
      com mais de um sistema por artefato.
- [ ] Calcular e guardar o hash do conteúdo local na sincronia
      (`synced_hash`), que é o que torna a comparação possível.
- [ ] Expor as consultas `external_links` e `unsynced` na API.
- [ ] Definir a porta `ExternalTracker` com capacidades declaradas, sem
      nenhum adaptador ainda.
- [ ] Detectar conflito (remoto mudou de revisão E local mudou de hash) e
      registrá-lo, sem escolher lado.
- [ ] Escrever os testes: sobrevive ao reindex, dois sistemas, pendência,
      conflito, e preview que nomeia o que a ferramenta não representa.

## Closing steps

- [ ] Apply the change: merge each delta into the corresponding spec.
- [ ] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0145-identidade-externa-frontmatter-vinculo/`.
- [ ] Update `.doctrina/index.json` with new or modified artifacts.
