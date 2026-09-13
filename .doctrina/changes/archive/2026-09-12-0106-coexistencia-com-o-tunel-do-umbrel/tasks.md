# Tasks — Change 0106-coexistencia-com-o-tunel-do-umbrel

- [x] `docker-compose.yml`: publicar `8347` no host, remover o serviço `cloudflared` e deixar o túnel dedicado como alternativa comentada no rodapé.
- [x] `.env.example`: `TUNNEL_TOKEN` vira opcional, com a nota de que quem tem o token é o app do Umbrel.
- [x] `docs/self-hosting.md` §1: diagrama do túnel compartilhado e a consequência de ficar visível na LAN atrás do mesmo login.
- [x] `docs/self-hosting.md` §1: seção sobre o wildcard do BFFless e por que túnel compartilhado não é o mesmo que proxy compartilhado.
- [x] `docs/self-hosting.md` §2: subir, conferir pela LAN, e criar o route ordenado acima do wildcard, com a tabela do resultado esperado.
- [x] `docs/self-hosting.md` §2.4: alternativa com túnel dedicado, onde o desempate é no DNS.
- [x] `docs/self-hosting.md` §5 e §6: sintomas do erro de ordenação e do 502; a LAN reescrita como consequência, não como opção.

## Closing steps

- [x] Apply the change (chore: sem deltas de spec).
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-12-0106-coexistencia-com-o-tunel-do-umbrel/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
