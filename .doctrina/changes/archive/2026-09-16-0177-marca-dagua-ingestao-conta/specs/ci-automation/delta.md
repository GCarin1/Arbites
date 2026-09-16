# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

A marca d'água derivada do disco varria também a pasta de anexos do run, onde
mora a análise que o pipeline publica.

```ops
append-requirement ubiquitous: The system shall derivar a marca d'água da ingestão apenas dos documentos de execução, ignorando os anexos gravados ao lado — um anexo nunca pode responder "este run já foi ingerido".
append-criterion [verified] Um `analysis.md` no anexo não entra na marca d'água, um anexo nomeado como a chave de outro run não faz esse run ser pulado, e a marca atravessa a virada de ano — verified by `backend/tests/test_marca_dagua.py`.
set-header Last updated: 2026-09-16
bump-version patch
```
