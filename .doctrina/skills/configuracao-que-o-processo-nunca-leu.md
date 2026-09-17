---
name: configuracao-que-o-processo-nunca-leu
description: Diagnosticar configuração que "não funciona" olhando o que o PROCESSO enxerga, não o arquivo que a pessoa mandou por captura de tela.
when: Alguém relata que declarou uma variável, um caminho ou uma credencial e o programa age como se nada tivesse sido declarado.
---

# Skill — configuração que o processo nunca leu

## When to use this skill

- A pessoa diz "eu já defini essa variável" e a tela continua pedindo que
  ela defina.
- Uma credencial, um caminho de certificado ou um endereço "estão certos no
  arquivo" e o comportamento é o de ausência.
- Você está prestes a pedir mais um print do arquivo de configuração.

## O erro que esta skill evita

Depurar o **arquivo** quando o defeito está na **diferença entre o arquivo e
o processo**. O arquivo fica certo em todas as rodadas; a pessoa reconfirma;
você deduz de novo; e o ciclo se repete. Aconteceu quatro vezes seguidas
antes da change 0187, e nas quatro o arquivo estava impecável.

Deduzir o valor lendo o arquivo é a forma mais cara de errar: custa um ciclo
inteiro de ida e volta, e a pessoa perde a confiança de que a ferramenta lê
o que ela escreve.

## Procedure

1. **Pare de pedir print.** A pergunta não é "o que o arquivo diz", é "o que
   chegou ao processo". São coisas diferentes, e só a segunda decide.

2. **Liste as diferenças possíveis antes de escolher uma.** Em configuração
   por arquivo há sempre as mesmas famílias, e todas são invisíveis:
   - **Lugar** — qual arquivo foi lido? Quase sempre o do diretório atual, e
     o comando documentado costuma ser rodado de outra pasta.
   - **Linha descartada em silêncio** — BOM do Bloco de Notas no começo do
     arquivo, `export` na frente, chave com ponto, CRLF.
   - **Precedência** — uma variável já no ambiente vence o arquivo, por
     desenho, e nada na tela diz isso.
   - **Valor literal** — aspas que sobraram, espaço no fim, `\\` duplicado,
     `~` e `%VAR%` que ninguém expande.
   - **Processo errado** — outro interpretador, outro venv, outro container.

3. **Dê um comando que imprime, não uma teoria que explica.** No Arbites:

   ```
   python -m arbites diagnostico
   ```

   Ele imprime o arquivo efetivamente lido, as chaves reconhecidas, as
   linhas descartadas com número e motivo, o `repr()` de cada valor e uma
   conexão real ao destino. Peça a saída dele, não outro print do arquivo.

4. **`repr()`, sempre.** `print(valor)` esconde exatamente o que quebra:
   espaço, aspas e barra. `repr()` mostra, e ainda assim traduza por extenso
   — nem todo mundo lê `repr()`.

5. **Segredo nunca entra na saída.** Um relatório de diagnóstico existe para
   ser colado num chat. Chave, origem e comprimento bastam para reconhecer
   "colei errado"; o valor não sai nunca. Decida por NOME da chave
   (`TOKEN`, `PASSWORD`, `SECRET`, `KEY`), não por heurística de conteúdo.

6. **Quando achar o defeito, conserte o silêncio junto.** O caso que exige
   diagnóstico é o caso que deveria ter avisado sozinho:
   - o arranque passa a imprimir QUAL arquivo leu;
   - a linha ignorada passa a ser nomeada;
   - a mensagem da TELA ganha a pista (quem só lê a tela nunca vê o
     terminal).

7. **Não conserte "adivinhando bonito".** Aceitar `C:\\\\Users\\\\...` como
   se fosse `C:\Users\...` é um palpite que funciona até o dia em que o
   caminho duplicado era o certo. Nomeie o problema com a linha corrigida
   pronta para colar — não reescreva o valor em silêncio.

## Check

- A saída do diagnóstico responde, sem você deduzir nada: **qual arquivo**,
  **quais chaves**, **qual valor literal**, **funcionou ou não**.
- Nenhum valor de token ou senha aparece nela.
- O sintoma original agora se anuncia sozinho no arranque ou na tela, sem
  ninguém precisar rodar o diagnóstico.
