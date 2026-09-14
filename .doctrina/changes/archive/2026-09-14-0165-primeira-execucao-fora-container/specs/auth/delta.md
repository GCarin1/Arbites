# Spec Delta — capability: auth

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/auth/spec.md`

---

```ops
append-requirement ubiquitous: The system shall ler um arquivo de ambiente do diretorio de execucao no arranque, dando precedencia as variaveis ja definidas no processo, para que a configuracao funcione igual dentro e fora de container.
append-requirement state: While nao existe administrador ativo e o ambiente nao traz credencial de bootstrap, the system shall registrar um erro dizendo que ninguem consegue entrar e como corrigir, em vez de subir em silencio.
append-requirement ubiquitous: The system shall oferecer um comando local para descartar o historico de tentativas de login, para que o bloqueio por tentativas nao deixe o dono da instancia sem saida na propria maquina.
append-criterion [unverified] O arquivo de ambiente e aplicado sem sobrepor variavel ja exportada e sem expor valores; arranque sem admin e sem credencial registra erro nomeando as variaveis; o comando de destrave libera o login e pode alcancar uma conta so — verified by `backend/tests/test_primeira_execucao.py`.
bump-version minor
```
