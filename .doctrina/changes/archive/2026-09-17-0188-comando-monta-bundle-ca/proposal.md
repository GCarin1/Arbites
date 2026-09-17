# Change 0188-comando-monta-bundle-ca — onde achar o `.pem` certo

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** ci-automation

## Why

A mensagem da change 0186 — "o arquivo é legível, mas não contém a CA que
assina este destino, costuma ser o certificado RAIZ do proxy" — está
correta e é inútil. Ela nomeia o erro e deixa a pessoa procurando o arquivo
sozinha, e a resposta que ela dá de volta é a pergunta óbvia: **onde eu acho
esse `.pem`?**

Quem tenta resolver na mão erra quase sempre, e erra em silêncio: exporta o
certificado do SITE em vez do da CA, ou o intermediário no lugar da raiz, ou
salva em DER com extensão `.pem`. Todos os três produzem um arquivo legível
que não contém a CA do destino — a mesma mensagem, de novo.

E o certificado certo já está na máquina: sem ele o navegador não abriria
nada. O que falta não é o arquivo, é juntá-lo ao que o Python enxerga.

## What

- `backend/arbites/bundle_ca.py` (novo) e `python -m arbites bundle-ca
  --saida <arquivo>`: soma as raízes públicas do `certifi` aos certificados
  de autenticação de servidor do armazenamento do Windows, confere que o
  arquivo carrega, e imprime a linha do `.env` pronta, com barra normal.
- `diagnostico.quem_assinou()`: o **emissor** do certificado que o destino
  apresentou — o nome que se procura na hora de exportar. Aparece sozinho
  quando a conexão falha por certificado.
- `tls.explicacao()`: a mensagem da tela deixa de sugerir uma caçada e passa
  a apontar o comando.
- README: a seção de rede corporativa, com o caminho pelo `certmgr.msc` para
  quem precisar exportar à mão.
- `cryptography` passa a ser dependência declarada: uma resposta que só
  aparece quando a biblioteca está instalada não serve para quem está preso.

## Scope boundaries

O programa **não** passa a ler o armazenamento do sistema por conta própria
numa chamada externa. O comando escreve um arquivo; declarar esse arquivo
continua sendo um ato explícito de quem opera a máquina. E continua não
existindo forma de desligar a verificação — o handshake sem verificação de
`quem_assinou()` não carrega credencial, cabeçalho nem byte de aplicação, e
fecha assim que o certificado chega.

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] The affected spec's acceptance criteria are met and cite their evidence.
- [x] `backend/tests/test_bundle_ca_do_sistema.py`: 11 testes, incluindo o
      armazém falso do Windows, o descarte do certificado sem uso de
      servidor, a deduplicação entre `ROOT` e `CA`, e um servidor TLS real
      com certificado próprio para provar a leitura do emissor.
- [x] `quem_assinou("api.github.com")` executado contra a rede deste
      ambiente — que também re-assina TLS — nomeando o emissor corretamente.

## Open questions

Nenhuma.
