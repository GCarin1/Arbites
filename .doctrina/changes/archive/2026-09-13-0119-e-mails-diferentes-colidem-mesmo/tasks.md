# Tasks — Change 0119-e-mails-diferentes-colidem-mesmo

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Identidade de arquivo por conta: slug + sufixo curto derivado do e-mail completo, num helper único usado pelo perfil e pelo avatar.
- [x] Adoção do nome antigo na primeira leitura, para não perder perfil nem avatar já gravados.
- [x] `backend/tests/test_profile_identity.py`: contas que colidem no slug ficam separadas, e o arquivo antigo é adotado.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0119-e-mails-diferentes-colidem-mesmo/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
