# Change 0183-certificado-corporativo-derruba-busca — certificado corporativo derruba a busca de actions com 500 e traceback

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime (confident; signals: traceback) — opened anyway (--force)
- **Affects specs:** ci-automation

## Why

certificado corporativo derruba a busca de actions com 500 e traceback

## What

- `backend/arbites/tls.py` (novo): lê o bundle de `ARBITES_CA_BUNDLE`,
  `REQUESTS_CA_BUNDLE` ou `SSL_CERT_FILE` (nessa ordem; as duas últimas são
  as que o ecossistema Python já usa e a máquina corporativa costuma ter),
  distingue erro de certificado de erro de rede, e monta a explicação — que
  muda conforme já havia bundle apontado ou não.
- `ci.py`: passa `verify=` em toda chamada e converte `httpx.TransportError`
  em `CIError` (`tls_untrusted` ou `unreachable`, ambos 502).
- `ai.py`: o mesmo, porque o mesmo proxy derruba o provider de nuvem.
- `Observability.tsx`: `tls_untrusted` ganha tratamento próprio ao lado de
  `bad_credential` — pedem ações opostas.
- README e `.env.example` explicam a variável e por que não há como desligar
  a verificação.

## Scope boundaries

- **Sem `verify=False`, nem por interruptor.** O PAT do GitHub viaja nessa
  conexão; sem verificar o certificado não há como saber para quem. Apontar
  o bundle é o caminho, e é auditável.
- Não se tenta descobrir a CA sozinho (ler o truststore do Windows, por
  exemplo): adivinhar qual CA confiar é exatamente a decisão que não cabe ao
  programa tomar em silêncio.
- Erro de transporte não é repetido: a marca d'água da ingestão é o disco, e
  clicar de novo recomeça de onde parou. Insistir só adiaria a mensagem.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] O erro relatado foi reproduzido com a exceção real do httpx
      (`ConnectError` com `SSLCertVerificationError` como causa) e deixou de
      ser 500: a rota responde 200 com o erro explicado no resumo.

## Open questions

Nenhuma.
