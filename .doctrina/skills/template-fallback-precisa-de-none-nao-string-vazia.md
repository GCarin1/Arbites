---
name: template-fallback-precisa-de-none-nao-string-vazia
description: Um campo Pydantic opcional com default de string vazia (str = "") nunca cai no fallback de template (payload.campo if payload.campo is not None else TEMPLATE), porque "" is not None é sempre True. O default precisa ser None (str | None = None) para o guard funcionar.
when: Ao criar um endpoint POST que grava um corpo/conteúdo com um TEMPLATE PADRÃO quando o cliente não envia nada — sempre que o modelo Pydantic tem um campo tipo body/content com fallback condicional.
---

# Skill — template-fallback-precisa-de-none-nao-string-vazia

## When to use this skill

- Vai criar um `POST /entidade` cujo corpo/conteúdo, se omitido, deve gravar
  um TEMPLATE padrão (ex.: `## Contexto\n\n...\n\n## Decisão\n\n...`).
- O código tem a forma: `payload.body if payload.body is not None else TEMPLATE`.

## O bug (real, encontrado neste projeto)

```python
class DecisionIn(BaseModel):
    body: str = ""   # 🐛 default é STRING VAZIA, não None
```
```python
_write_doc(path, meta, payload.body if payload.body is not None else DEFAULT_BODY)
```

`payload.body` nunca é `None` — na ausência do campo no request, o Pydantic
já preenche com o default `""`. `"" is not None` é `True`. O `else` NUNCA
executa. Todo registro criado sem `body` explícito grava um arquivo com
corpo **vazio**, não o template — sem erro, sem aviso, só o comportamento
errado silenciosamente.

O padrão CORRETO já existia no mesmo arquivo, só não foi copiado:
```python
class TestcaseIn(BaseModel):
    body: str | None = None   # ✅ default é None de verdade
```

## Procedure

1. **Para qualquer campo com fallback condicional em `is not None`, o tipo
   TEM que ser `str | None = None`**, nunca `str = ""`. São semânticas
   diferentes: `""` é "o cliente mandou vazio de propósito"; `None` é "o
   cliente não mandou nada".
2. **Antes de escrever um novo modelo com esse padrão, copie o campo
   irmão já existente** (ex.: `TestcaseIn.body`) em vez de reescrever do
   zero — é assim que esse exato bug já tinha sido evitado alhures no
   mesmo arquivo.
3. **Teste o caminho "sem enviar o campo"** explicitamente — não só "com
   valor". Um teste que só cobre `POST` com `body` preenchido nunca pega
   esse bug; precisa de um `POST` sem o campo, checando que o template
   apareceu na resposta/arquivo.

## Anti-patterns

- Copiar a ESTRUTURA de um `BaseModel` sem prestar atenção ao tipo exato de
  cada campo — o `= ""` vs `= None` é fácil de digitar errado e o Pydantic
  não avisa (ambos são "válidos" do ponto de vista de tipos).
- Testar só o caminho "campo preenchido" de um endpoint de criação.

## Related material

- `backend/arbites/api.py` — `DecisionIn.body`, `TestcaseIn.body` (o padrão
  correto pré-existente), `DEFAULT_DECISION_BODY`/`DEFAULT_TC_BODY`.
- `backend/tests/test_decisions.py` —
  `test_create_decision_with_default_body_template` (POST sem `body`).
