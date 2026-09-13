# Spec Delta — capability: profile

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/profile/spec.md`

---

O perfil deixa de ser só uma aba e passa a ter presença permanente: o
avatar da conta no canto superior direito, do jeito que o GitHub faz, é o
que responde "quem sou eu nesta instância" sem exigir navegação. Numa
instância de um usuário isso era supérfluo; com o time inteiro no mesmo
workspace, é a diferença entre saber e supor com que conta você está
gravando.

O padrão quando não há foto é um **identicon**: uma grade 5×5 simétrica
derivada do hash do e-mail, gerada como SVG no próprio frontend. Determinística
(a mesma conta sempre tem o mesmo desenho e a mesma cor) e sem nenhuma chamada
externa — Gravatar foi descartado justamente porque exigiria mandar o hash do
e-mail de cada usuário para fora, contra o local-first e a promessa de zero
telemetria.

```ops
bump-version minor
append-requirement ubiquitous: The system shall expor `GET /profile/avatar` e `PUT /profile/avatar` para a conta da sessão, aceitando PNG, JPEG ou WebP de até 1 MB, e `DELETE /profile/avatar` para voltar ao identicon.
append-requirement ubiquitous: The system shall guardar o avatar em `profiles/avatars/<slug-do-e-mail>.<ext>`, ao lado do perfil da conta, sem passar pelo índice descartável.
append-requirement ubiquitous: The system shall exibir o avatar da conta logada no canto superior direito de toda tela, abrindo um menu com Perfil, Administração (apenas para `admin`) e Sair.
append-requirement event: When a conta não tem imagem, the system shall desenhar um identicon determinístico — grade 5×5 espelhada e cor derivadas do hash do e-mail — gerado no cliente, sem requisição a serviço externo.
append-requirement unwanted: The system shall not buscar avatar em serviço externo (Gravatar ou equivalente); enviar o hash do e-mail de cada conta para fora contraria o local-first e a promessa de zero telemetria.
append-requirement unwanted: The system shall not aceitar como avatar arquivo que não seja imagem reconhecida por assinatura de bytes, nem confiar na extensão informada pelo cliente.
append-criterion [unverified] Uma conta sobe uma imagem, ela aparece no canto superior direito e sobrevive ao reinício do processo; removê-la volta ao identicon — verified by `backend/tests/test_avatar.py`.
append-criterion [unverified] Duas contas sem foto recebem identicons diferentes, e a mesma conta recebe sempre o mesmo desenho — verified by `frontend/src/components/Identicon.tsx` + `backend/tests/test_avatar.py`.
append-criterion [unverified] O avatar de uma conta não é legível por outra, e um arquivo que não é imagem é recusado mesmo com extensão de imagem — verified by `backend/tests/test_avatar.py`.
```
