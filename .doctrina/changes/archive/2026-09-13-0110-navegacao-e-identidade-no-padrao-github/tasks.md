# Tasks — Change 0110-navegacao-e-identidade-no-padrao-github

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Rotas `GET/PUT/DELETE /profile/avatar` em `backend/arbites/api.py`, com sniff por assinatura de bytes (PNG/JPEG/WebP) e teto de 1 MB.
- [x] `backend/tests/test_avatar.py`: upload sobrevive ao reinício, remoção volta ao identicon, isolamento entre contas e recusa de não-imagem com extensão de imagem.
- [x] `frontend/src/components/Identicon.tsx`: grade 5×5 espelhada e cor derivadas do hash do e-mail, em SVG e sem chamada externa.
- [x] `frontend/src/components/AccountMenu.tsx` ligado ao header: avatar no canto superior direito com Perfil, Administração (só `admin`) e Sair.
- [x] Tela de Perfil com troca de foto e volta ao identicon; estilos do menu e do editor em `styles.css`.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0110-navegacao-e-identidade-no-padrao-github/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
