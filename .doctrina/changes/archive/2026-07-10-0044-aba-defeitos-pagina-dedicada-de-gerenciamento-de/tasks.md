# Tasks — Change 0044

- [x] Backend: `GET /defects/{id}` (via `_defect_out`, já incluía corpo — só faltava a rota).
- [x] Backend: `DELETE /defects/{id}` (mesmo padrão de `delete_todo` — trash + reindex).
- [x] Frontend: `Defects.tsx` — tabela com filtro status/severidade, criar/editar via Modal
      (SingleRefInput pra CT/execução, MentionTextarea pra descrição), mudança rápida de
      status, excluir com confirmação.
- [x] Frontend: nova aba "Defeitos" na navegação (grupo Acompanhamento).
- [x] Frontend: `navigateTo` ganha o caso `DF-XXXX` (antes explicitamente não navegava);
      `openId`/`onOpened` abrem o editor direto ao chegar via menção/link.
- [x] Reuso do `SEV_DOT` (cores de severidade) já existente no Dashboard — sem inventar
      um novo esquema de cor.
- [x] Testes backend (get individual com corpo, 404, delete→trash, criação avulsa) + suíte
      verde + build.
- [x] Smoke HTTP contra servidor real (criar → listar → get → put → delete → 404).

## Closing steps

- [x] Apply: merge delta na spec defects.
- [x] Archive.
- [x] Update index.json.
