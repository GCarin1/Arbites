# Spec Delta — capability: defects

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/defects/spec.md`

---

## Requirements (EARS)

### Ubiquitous

- The system shall permitir registrar, por defeito, uma **lição aprendida**
  opcional em três campos de frontmatter: `root_cause` (causa raiz), `fix`
  (correção aplicada) e `prevention` (como prevenir a recorrência).
- The system shall expor `GET /defects?has_lesson=true` filtrando apenas
  defeitos com ao menos um dos três campos de lição preenchido.

### Event-driven

- When o usuário abre o formulário de defeito, the system shall exibir uma
  seção "Lição aprendida" (causa raiz/correção/prevenção) editável junto dos
  demais campos, e sinalizar na listagem quais defeitos já têm lição
  registrada.

## Acceptance criteria

6. [verified] Criar/editar um defeito com causa raiz/correção/prevenção
   persiste os três campos, aparecem no `GET` individual, e
   `GET /defects?has_lesson=true` retorna só os defeitos com lição — verified
   by `backend/tests/test_lessons_learned.py`.
