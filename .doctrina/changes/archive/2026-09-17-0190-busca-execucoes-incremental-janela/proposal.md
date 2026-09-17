# Change 0190-busca-execucoes-incremental-janela — buscar só o que falta

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** ci-automation

## Why

A pergunta veio como receio: *"se eu já busquei 30 dias e depois peço 90, ele
vai buscar os 90 de novo, duplicando ou sobrescrevendo?"*

Duplicar, não duplicava — a chave do run é o nome do arquivo, e ingerir duas
vezes reescreve o mesmo documento. Mas o custo era real e se repetia a cada
clique: toda busca recomeçava do zero.

E havia um defeito pior escondido atrás disso. A varredura parava na primeira
página inteiramente conhecida, com o comentário "o passado está coberto". Não
estava. Para quem tem 30 dias no disco e pede 90, a primeira página é toda
conhecida, a busca parava ali, e **os 60 dias mais antigos nunca chegavam**.
Um buraco permanente numa série temporal, silencioso.

A causa das duas coisas é a mesma: faltava a resposta para "até onde eu já
olhei". Essa pergunta o disco não responde — um mês sem nenhuma execução e um
mês nunca varrido são idênticos no disco.

## What

- `backend/arbites/ci_cobertura.py` (novo): os intervalos já varridos por
  origem, em `ci/cobertura.json`, com `fundir()` e `lacunas()`.
- `ingerir(limite, dias, refazer)`: calcula a lacuna da janela e varre só
  ela. A resposta traz `window`, `scanned` e `reused`.
- `_pendentes()` passa a parar pela **data**, não pela página conhecida, e a
  pedir ao provedor o filtro `created` — alcançar uma lacuna antiga deixa de
  custar paginar por tudo que veio depois dela.
- `MARGEM_HORAS = 48`: a borda recente nunca entra na cobertura.
- `POST /ci/ingest?days=&refresh=`, o período da tela vai junto, e o botão
  **Reconferir período** na aba Configuração.

## Scope boundaries

A marca d'água continua sendo o disco (ADR 0016) — a cobertura é uma
otimização, e perdê-la custa tempo e nunca dados. Nada é apagado por esta
change, e reconferir não rebaixa artifact que já está no disco.

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] The affected spec's acceptance criteria are met and cite their evidence.
- [x] `backend/tests/test_busca_incremental.py`: 16 testes — a aritmética das
      lacunas (incluindo buraco no meio e intervalos que não podem fundir) e
      seis de ponta a ponta contra o provedor falso, que honra o filtro de
      data para o teste não provar uma coisa e a produção fazer outra.

## Open questions

Nenhuma.
