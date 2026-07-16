# Opinião do agente — uso do framework SDD Doctrina neste projeto

**Contexto:** uso intensivo ao longo do catálogo A1→I4 (e hotfixes), em
`pf-b3-investidor-b3i-testes-front`, via CLI `npx doctrina` + artefatos em
`.doctrina/`.  
**Natureza:** opinião operacional de quem implementa, não avaliação formal
de produto.

## Resumo

O Doctrina **facilitou manter coerência** (spec ↔ código ↔ evidência) numa
suíte de automação que cresce por muitos eixos (WebDriver, CI, IA, flaky,
shards). Onde mais senti atrito foi em **ritmo vs cerimônia** (fechar change
quando o fix é óbvio), **dupla fonte de verdade parcial** (spec já editada
in-repo + delta ops) e **feedback de drift** (index/skills) que interrompe
o fluxo no fim. Abaixo: o que ajudou, gaps e melhorias concretas no fluxo.

---

## O que facilitou (o que eu “ganhei”)

1. **Orientação automática do próximo passo**  
   `doctrina next` / `status` / playbook do `work` reduziram a dúvida
   “o que faço agora?” num backlog longo (A1…I4).

2. **Contrato explícito + ACs com evidência**  
   Cobrar `verified by tests/...` torna o “Definition of Done” checável —
   `coverage` / `verify` / `validate` pegam buraco de gate de verdade, não
   só markdown bonito.

3. **ADRs imutáveis nos trade-offs certos**  
   Context pack (0003), shards (0004), reuse de sessão (0005): decisões que
   eu **não deveria reabrir** a cada chat. Evita regressão de desenho.

4. **Skills como memória de incidentes**  
   Exemplos: headed Chromium, flaky `@flaky`, Behave 1.2 vs 1.3
   (`has_failed`). Depois do erro em CI, o skill impede o mesmo antipadrão.

5. **Close atestado em uma passada**  
   `doctrina close` (analyze → apply → verify → coverage → archive) força
   o pacote sair consistente; erros vêm com comando de rerun.

6. **Separação archive × active**  
   Não poluir o read pack com histórico antigo (`changes/archive/`) ajuda
   o agent a não “alucinar” contexto de changes mortas.

---

## Onde senti gap / precisei me esforçar

1. **Cerimônia vs hotfix**  
   Bug óbvio em produção/CI (ex.: `has_failed` no Behave 1.2.6) pedia fix
   imediato; o fluxo “ideal” quer change + delta + close. Acabei **fixando
   o código primeiro** e documentando depois — o framework ainda não tem um
   “hotfix lane” leve o bastante.

2. **Deltas ops quando a spec já está escrita in-repo**  
   Padrão frequente: editar `spec.md` completo e depois delta só com
   `set-header` / “already updated”. Funciona, mas é **trabalho duplicado**/redundante;
   `apply` vira no-op de conteúdo.

3. **Index drift recorrente**  
   Após archive/skills, `validate --fix` / `index rebuild` quase sempre
   no fim. É correto, mas **quebra o mood de “já fechei”**.

4. **CLI via `npx` e mensagens longas**  
   Em Windows + OneDrive, cold start do `npx doctrina` é lento; playbooks
   impressos são densos (bom para novas sessões, ruidosos no 30º item).

5. **Capability match do `work` é heurístico**  
   Scores de capability ajudam, mas o agent ainda precisa **confirmar**
   caps certas (observability vs CI). Fácil acertar demais ou de menos.

6. **Backlog humano (`BACKLOG.md`) paralelo ao index**  
   Ordem A1→I4 vivia fora do Doctrina “nativo”; sincronizar status done/
   proposed foi **manual**. Gap de product backlog ↔ changes.

7. **Skills sugeridos por `skill suggest`**  
   Às vezes duplicam skills já existentes (ex. flaky G2). Falta
   dedupe forte por similaridade de `when:` / descrição.

8. **Evidência E2E `[unverified]`**  
   ACs que exigem behave real / BrowserStack / outro repo ficam eternas
   `[unverified]` mesmo com YAML e unitários. O framework **não guia bem**
   o que contar como “verificado em CI periódico” vs unit gate.

9. **Encoding / path**  
   Paths OneDrive + acentuação às vezes atrapalham scripts; não é culpa
   do Doctrina, mas o fluxo assume shell confortável.

---

## Melhorias que agregariam no fluxo Doctrina

### Fluxo / DX do agent

| Ideia | Por quê |
|---|---|
| **`doctrina hotfix "<prompt>"`** — change mínima, 1 delta ops, close curto, sem forçar design.md | Separar trilho de incidente de trilho de feature |
| **`close --from-impl`** se code+tests já batem o AC | Evita re-aplicar delta vazio |
| Auto **`validate --fix`** embutido no `close` (não só no fim do agente) | Menos “passeei no verify e falhei no index” |
| Playbook **compacto** (`work --brief`) | Menos tokens, menos ruído |

### Specs e cobertura

| Ideia | Por quê |
|---|---|
| Critério **`[ci-verified]`** ou âncora a workflow run / job name | Smoke agendado “prova” AC E2E sem pytest |
| Ao editar AC no spec, **sugerir/gerar** stub de teste pytest | Fecha o loop evidência |
| Diff de AC: `doctrina coverage --orphan-tests` | Testes sem AC e ACs sem teste |

### Skills e memória

| Ideia | Por quê |
|---|---|
| `skill suggest` com **bloqueio de near-duplicate** | Evita segunda skill flaky |
| Ao falhar verify com traceback conhecido, **prompt** “gravar skill?” | Captura lição no momento da dor |
| Frontmatter `behave_pin` / `stack_constraints` | Skills dependem de versão (1.2.6 vs 1.3) |

### Backlog e governance

| Ideia | Por quê |
|---|---|
| Catalog IDs (A1, G1…) **first-class** no index / `doctrina backlog` | Um só mapa |
| `doctrina work` aceitar `--catalog G1` já arquivado → refuse + link | Evita reabrir trabalho done |
| Ledger legível para gestor (1 página de “o que mudou no mês”) | Ponte SDD ↔ comunicação executiva |

### Paridade local × CI

| Ideia | Por quê |
|---|---|
| `doctrina doctor` checando pin `requirements.txt` vs `pip show` | O bug Behave 1.3 local / 1.2.6 CI |
| Matrix “API surface by pin” em skills geradas | Menos AttributeError surpresa |

---

## Veredito pessoal

**Mantería o Doctrina neste tipo de projeto** — automação E2E com muitos
cruzamentos (CI, WebDriver, IA) se beneficia de SDD + ADRs + skills.

O valor máximo aparece quando:

1. a change é **não óbvia** (sharding, reuse de sessão, contrato do pack), e  
2. o agent **fecha de verdade** com verify/coverage, não só escreve markdown.

O valor mínimo aparece em **patch de uma linha por incompatibilidade de
lib**: aí o framework ainda parece pesado sem um modo hotfix.

---

## Ligação com o trabalho recente

- Catálogo A1–I4 fechado com close/archive → prova de que o loop escala.  
- Hotfix Behave `has_failed` → mostrou o gap CI pin vs API 1.3 e originou
  a skill `behave-api-compat-step-status`.  
- Change **0021** (HTML/métricas/Summary+IA) é o próximo ciclo “feature”
  clássico Doctrina — bom caso para o trilho completo após as decisões do
  humano.
