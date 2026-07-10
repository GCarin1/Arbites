# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

## Requirements (EARS)

### Ubiquitous

- The system shall expor `PUT /targets`, substituindo `automation_targets`
  no `arbites.yaml` por inteiro (mesmo padrão de `PUT /ai/providers`) —
  cadastro de target não exige editar o YAML manualmente.
- The system shall expor `GET /automation/browse-features` que escaneia
  `local_path` em busca de arquivos `.feature` (sem exigir que o target já
  exista/esteja salvo) e devolve caminho relativo + contagem de cenários de
  cada um, para o usuário escolher em vez de digitar um glob às cegas.

### Event-driven

- When o usuário salva a configuração de targets pela UI, the system shall
  reescanear cada target salvo (mesmo comportamento de `POST
  /targets/{name}/scan`), populando cenários/warnings imediatamente.

## Acceptance criteria

8. [verified] Salvar um target pela UI persiste em `arbites.yaml`, aparece
   em `GET /targets` com a contagem de cenários já escaneada, e um target
   com `local_path` inexistente não derruba a rota — verified by
   `backend/tests/test_automation_targets_config.py`.

9. [verified] `GET /automation/browse-features` lista os `.feature`
    encontrados (caminho relativo + nº de cenários) para um `local_path`
    arbitrário, mesmo sem target salvo; caminho inexistente é rejeitado
    (422) — verified by `backend/tests/test_automation_targets_config.py`.
