---
name: git-log-subprocess-null-separado-read-only
description: Como chamar `git log` via subprocess de forma segura para extrair commits + arquivos tocados, sem ambiguidade de parsing e sem risco de travar ou escrever no repositório do usuário.
when: O agente está integrando com um repositório git local via subprocess (churn, histórico de arquivo, blame, etc.), não via uma API remota (GitHub Actions já tem seu próprio client HTTP).
---

# Skill — git-log-subprocess-null-separado-read-only

## When to use this skill

- O agente precisa extrair dados de um repositório git LOCAL (não remoto)
  via `subprocess`, ex.: churn por arquivo, histórico de commits, mensagens.
- O agente está integrando uma feature que cruza dados de git com dados de
  outro sistema (aqui: defeitos rastreados no Arbites).

## Procedure

1. Sempre passe `timeout=` no `subprocess.run` — um repo gigante/lento
   (ou um `local_path` apontando pra fora de um repo) não pode travar a
   request HTTP que disparou o scan.
2. Use `check=True` dentro de um `try/except (OSError,
   subprocess.SubprocessError)` que devolve uma lista vazia — nunca deixe a
   exceção subir e derrubar a rota. Um repo com `local_path` inválido é uma
   configuração do usuário, não um bug do servidor.
3. Para separar commits ao fazer parsing de `--name-only`, use um separador
   que NUNCA aparece em mensagem de commit nem em nome de arquivo:
   `--pretty=format:%x00%s` (NUL antes do subject). Quebra de linha (`\n`)
   não serve — mensagens de commit multi-linha e a lista de arquivos usam
   `\n` livremente, então splitar por linha embaralha tudo.
   ```python
   subprocess.run(
       ["git", "log", f"--since={days}.days", "--name-only",
        "--pretty=format:%x00%s"],
       cwd=str(local_path), capture_output=True, text=True,
       timeout=15, check=True,
   )
   ```
   Depois: `stdout.split("\x00")[1:]` — o primeiro elemento é sempre vazio
   (nada antes do primeiro NUL), descarte-o.
4. Nunca use um comando git que escreve (`checkout`, `pull`, `reset`,
   `clean`) num repositório do usuário sem confirmação explícita — este
   padrão é estritamente read-only (`git log`).
5. Para cruzar commits com entidades de outro sistema (aqui: `DF-\d+` do
   Arbites), valide a menção contra o índice real antes de contar — uma
   string parecida com um ID (`DF-123` numa mensagem qualquer) não é prova
   de que o defeito existe; carregue os IDs reais primeiro e faça
   interseção.

## Anti-patterns

- Splitar `--name-only` por linha em branco (`\n\n`) para separar commits —
  quebra com mensagens de commit multi-linha (uma linha em branco no meio
  da mensagem já corta errado).
- Rodar `git log` sem `timeout` — um repo com histórico gigante ou um
  `local_path` que na verdade é uma pasta comum (não-git) pode pendurar a
  request.
- Deixar `subprocess.SubprocessError`/`OSError` propagar e virar 500 — trate
  como "esse repo específico não pôde ser escaneado", não como falha da
  rota inteira (os demais repos configurados devem continuar funcionando).

## Related material

- `backend/arbites/risk_map.py` — `_git_log`/`scan_repo`.
- `.doctrina/specs/risk-map/spec.md` — critérios de aceitação #2 e #3.
