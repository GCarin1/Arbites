---
name: config-deriva-do-projeto-nao-fixa-campos
description: Catálogos/formulários de configuração de um projeto-alvo devem ser DERIVADOS do próprio projeto (ex.: `.env`/`.env.example`), nunca uma lista fixa embutida de campos de um projeto específico.
when: O agente vai expor na UI um catálogo/lista de campos de configuração de um projeto-alvo externo (variáveis de `.env`, parâmetros, chaves), ou vê uma constante hardcoded com campos que só fazem sentido para um projeto.
---

# Skill — config-deriva-do-projeto-nao-fixa-campos

## When to use this skill

- Vai construir/alterar um endpoint ou UI que lista "os campos de
  configuração" de um projeto-alvo (ex.: `GET /env/catalog`, formulário de
  `.env`, parâmetros de execução).
- Encontrou uma constante como `ENV_CATALOG = [...]` com chaves específicas
  de UM projeto (nomes de empresa, drivers, provedores) embutidas no código.

## Procedure

1. **Derive do artefato do próprio projeto.** Para `.env`, leia
   `local_path/.env.example` (preferido — documenta as chaves) e
   `local_path/.env`, e extraia `{section, key, description}`:
   - `# Seção` seguido de linha em branco → seção;
   - `# descrição` logo acima de uma chave → descrição;
   - `KEY=valor  # inline` → descrição (tem prioridade).
2. **Parametrize por target.** O endpoint recebe `?target=` e resolve o
   `local_path`; sem target útil ou sem arquivo → catálogo **vazio** (o
   usuário adiciona chaves livres), nunca um fallback fixo.
3. **UI tolera vazio.** Renderize um empty-state instrutivo ("adicione um
   `.env.example` para documentar as variáveis") em vez de campos inventados.
4. **Teste com um projeto fake** que tenha o seu próprio `.env.example`, e
   asserte que campos de OUTRO projeto (ex.: `BROWSERSTACK_*`,
   `TEST_DOCUMENTO`) **não** aparecem.

## Anti-patterns

- `ENV_CATALOG = [{"key": "TEST_DOCUMENTO", ...}, {"key": "BROWSERSTACK_...", ...}]`
  fixo no backend — impõe o vocabulário de um projeto a todos os usuários.
  Foi o bug do change 0099.
- Fazer o usuário se adaptar aos campos da ferramenta; é a ferramenta que se
  adapta ao projeto inserido.

## Related material

- `backend/arbites/api.py` — `derive_env_catalog`, rota `GET /env/catalog`.
- `frontend/src/components/Automation.tsx` — `EnvCard`.
