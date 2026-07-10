# Tasks — Change 0034

- [x] `_client`: timeout 120 → 300 s (modelos locais de raciocínio).
- [x] OpenAICompatible: usar `reasoning_content` quando `content` vier vazio.
- [x] `_IMPORT_SYSTEM`: prompt curto e determinístico (evita loop de raciocínio).
- [x] Modal de import: botão "Enviar" explícito; seleção não submete sozinha.
- [x] Teste `test_reasoning_content_used_when_content_empty` + suíte verde + build.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder.
- [x] Update `.doctrina/index.json`.
