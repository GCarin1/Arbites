# Change 0201-cliente-mcp-acha-pacote — o pacote que o cliente não achava

- **Status:** applied
- **Applied:** 2026-09-18
- **Date:** 2026-09-18
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** mcp-server

## Why

A change 0200 tratou o servidor que morria por falta de token. O erro
continuou. Desta vez reproduzi com um **cliente MCP de verdade**, fazendo o
mesmo handshake que o VS Code faz, e o `Connection closed` apareceu aqui —
idêntico.

A causa é anterior a tudo que a 0200 mexeu: `python -m arbites.mcp` só
encontra o pacote quando o processo nasce dentro de `backend/`. O cliente MCP
não nasce ali — ele lança o comando a partir da pasta dele. O Python responde
`No module named arbites` em stderr, que a maioria dos clientes não exibe, e
sobra o erro genérico. **A documentação era a causa direta**: o `mcp.json` do
README mostrava o comando sem `cwd` nenhum.

E o diagnóstico da 0200 não alcançava esse caso, por construção: ele roda de
dentro do projeto, onde o import sempre funciona.

## What

- **`backend/pyproject.toml`**: o projeto passa a ser instalável
  (`pip install -e backend`), e aí o comando funciona de qualquer diretório.
  `requires-python` é `>=3.11` e não `>=3.12` do `AGENTS.md`: exigir uma
  versão acima da que roda a suíte trocaria "não acha o pacote" por "versão
  errada", que não é progresso.
- **README**: o `mcp.json` ganha `cwd`, com o aviso de que a falta dele é a
  causa nº 1 do erro, e a alternativa da instalação.
- **`diagnostico.secao_mcp()`**: afere a partir de um diretório temporário,
  sem `PYTHONPATH` — a condição real do cliente —, e imprime o comando exato
  do conserto. Aferir de dentro do projeto daria um "ok" que não vale nada.
- **`--url` e `--token`** no diagnóstico do MCP: o bloco `env` do `mcp.json` é
  entregue pelo cliente ao processo que ele lança e **não existe no
  PowerShell**. Sem essa passagem, quem rodasse o diagnóstico à mão leria
  sempre "NAO DEFINIDO" e iria procurar o problema errado — foi o que
  aconteceu.
- As duas mensagens que apontavam lugares diferentes para gerar a credencial
  passam a apontar a mesma aba (IA → MCP), com teste que trava isso.

## Scope boundaries

Nenhuma ferramenta muda, nem o contrato do protocolo.

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] The affected spec's acceptance criteria are met and cite their evidence.
- [x] Cliente MCP real, três cenários: sem `cwd` reproduz o
      `Connection closed`; com `cwd=backend` conecta e lista 13 ferramentas;
      instalado com `pip install -e`, conecta lançado de `/tmp`.
- [x] `backend/tests/test_mcp_alcancavel.py` e `test_mcp_arranque.py`.

## Open questions

Nenhuma.
