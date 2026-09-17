# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

Numa rede que re-assina o TLS, toda chamada ao GitHub morria com
`CERTIFICATE_VERIFY_FAILED` — e o erro subia cru, virando 500 com traceback.

```ops
append-requirement ubiquitous: The system shall aceitar um bundle de CA declarado por variável de ambiente e usá-lo na verificação TLS de toda chamada externa, para funcionar em rede que re-assina o tráfego.
append-requirement event: When uma chamada externa falha no transporte, the system shall recusá-la com mensagem própria distinguindo certificado não confiável de destino inalcançável, em vez de deixar a exceção subir como erro interno.
append-requirement unwanted: The system shall not oferecer desligar a verificação de certificado; a credencial do provedor viaja nessa conexão, e sem verificar o certificado não há como saber para quem.
append-criterion [verified] Qualquer das três variáveis aponta o bundle, na ordem declarada, e um caminho inexistente cai no padrão em vez de estourar; erro de certificado e queda de rede saem com códigos e mensagens diferentes; e a ingestão registra o erro no resumo, sem exceção não tratada — verified by `backend/tests/test_tls_corporativo.py`.
set-header Last updated: 2026-09-17
bump-version minor
```
