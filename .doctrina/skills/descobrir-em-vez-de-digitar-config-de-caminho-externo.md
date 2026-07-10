---
name: descobrir-em-vez-de-digitar-config-de-caminho-externo
description: Quando um formulário de config pede um caminho externo (pasta/glob de outro repositório) que o usuário não decora, ofereça um botão que ESCANEIA o filesystem de verdade e devolve a lista real para escolher — não deixe o usuário digitar um padrão às cegas.
when: Ao criar/editar um form que configura acesso a um caminho de filesystem fora do workspace (repo de automação, pasta de artefatos, glob de arquivos) — especialmente quando o app já roda local-first e pode ler o disco do usuário.
---

# Skill — descobrir-em-vez-de-digitar-config-de-caminho-externo

## When to use this skill

- Form de configuração pede um `local_path`/glob apontando pra um
  repositório ou pasta FORA do workspace do app (ex.: repo de automação
  Behave, pasta de scripts, diretório de artefatos).
- O usuário reclamou (ou reclamaria) de ter que digitar um caminho/padrão
  sem confirmação de que está certo, ou de ter que editar um arquivo de
  config à mão pra registrar isso.

## Procedure

1. **CRUD pela UI, não arquivo de config manual.** Se já existe um padrão de
   "substituir a lista inteira" pra outro array de config no mesmo app (ex.:
   `PUT /ai/providers`), reuse o MESMO padrão para o array novo — não invente
   um esquema de API diferente (POST/PUT/DELETE por item) sem necessidade.
2. **Scan avulso, independente do registro.** Crie um endpoint de
   "descobrir" que aceita o caminho bruto digitado (NÃO exige que a entidade
   já esteja salva) e devolve o que existe de verdade no filesystem. Isso
   desacopla "validar o caminho" de "persistir a config" — o usuário vê o
   resultado antes de decidir salvar.
3. **Devolva uma lista selecionável, não só um boolean de "existe".** Cada
   item encontrado (arquivo, subpasta) com metadado útil (contagem de
   cenários, tamanho, o que for relevante) — clicar num item deve poder
   estreitar a config (ex.: fixar o glob nesse arquivo específico) em vez de
   só informar.
4. **Não tente um seletor de pasta nativo numa SPA web** (não existe API de
   filesystem picker sem Electron/Tauri) — o botão "buscar"/"escanear" É o
   substituto correto: dá o MESMO feedback de confiança sem exigir um picker
   nativo.
5. **Trate ausência do caminho como resultado, não como erro fatal em
   cascata:** ao salvar a lista inteira, um item com caminho inválido não
   deve derrubar a rota (os outros itens salvam normalmente); reporte
   contagem zero pra aquele item, não uma exceção.

## Anti-patterns

- "Documentar em algum lugar que o campo X aceita um glob" e deixar o
  usuário descobrir sozinho se digitou certo.
- Pedir pra editar o `arbites.yaml`/config file na mão quando já existe
  precedente de CRUD pela UI para arrays irmãos no mesmo app.
- Um endpoint de scan que só funciona para uma entidade JÁ SALVA — inútil
  no exato momento em que o usuário está decidindo se o caminho está certo.

## Related material

- `backend/arbites/gherkin_scan.py` — `list_feature_files` (scan avulso).
- `backend/arbites/api.py` — `GET /automation/browse-features`,
  `PUT /targets` (mesmo padrão de `PUT /ai/providers`).
- `frontend/src/components/Automation.tsx` — `TargetsCard` (botão "Buscar
  arquivos .feature", lista clicável).
- Spec `local-automation` (#8, #9).
