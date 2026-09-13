# Spec Delta — capability: defects

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/defects/spec.md`

---

O recurso está certo e o nome dele, na interface, está errado.

Por trás de "lição aprendida" há três campos concretos — **causa raiz**,
**correção aplicada** e **como prevenir a recorrência** — e um uso claro:
quando alguém pede à IA um caso de teste numa área relacionada, essas
análises entram no prompt para o mesmo bug não voltar. É postmortem técnico,
a mesma prática de um post-mortem de incidente.

"Lição aprendida", sozinha num filtro ao lado de uma lista de bugs, não diz
nada disso. Em português o termo carrega o vocabulário de retrospectiva de
equipe, e foi exatamente assim que o dono do produto leu: como se o campo
falasse de atitudes de pessoas. Um rótulo que faz quem conhece o produto
entender o oposto do que o campo guarda não é questão de gosto — é defeito
de nome.

A correção é chamar na interface pelo que se preenche: análise da causa. O
frontmatter, o parâmetro da rota e o índice não mudam — eles estão
documentados, moram nos `.md` de workspaces existentes, e renomeá-los
quebraria dado gravado para resolver um problema que é de leitura.

```ops
bump-version patch
append-requirement ubiquitous: The system shall nomear na interface o conjunto causa raiz, correção e prevenção como análise da causa do defeito, sem usar vocabulário que sugira avaliação de pessoas.
append-requirement unwanted: The system shall not renomear o frontmatter, o parâmetro de filtro nem as colunas do índice ao ajustar o nome exibido; o dado já gravado nos workspaces continua válido.
append-criterion [unverified] A interface nomeia o conjunto como análise da causa, e o frontmatter, o filtro da rota e o índice seguem com os nomes originais — verified by `frontend/src/components/Defects.tsx` + `backend/tests/test_lessons_learned.py`.
```
