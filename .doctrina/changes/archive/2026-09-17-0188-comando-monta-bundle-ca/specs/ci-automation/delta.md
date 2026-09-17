# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

```ops
bump-version minor
append-requirement event: When o operador pede o bundle de CA pela CLI, the system shall escrever um arquivo com as raízes públicas somadas aos certificados de autenticação de servidor do armazenamento do sistema operacional, conferir que o arquivo carrega, e imprimir a linha de declaração pronta.
append-requirement event: When o certificado de um destino não é aceito, the system shall dizer o nome de quem o emitiu, porque é esse nome que se procura na hora de obter o certificado certo.
append-requirement unwanted: The system shall not ler o armazenamento de certificados do sistema por conta própria numa chamada externa; ampliar a própria confiança sem que ninguém tenha dito nada é decisão de quem opera a máquina, e o comando que monta o bundle só escreve um arquivo que continua precisando ser declarado.
append-requirement unwanted: The system shall not incluir no bundle certificado que não esteja habilitado para autenticar servidor; o armazenamento do sistema guarda também autoridades de assinatura de código e de e-mail.
append-criterion [verified] O bundle montado soma as raízes públicas às do armazenamento do sistema, carrega de verdade, descarta certificado sem uso de servidor e não duplica o que aparece em dois armazéns; fora do Windows o comando diz isso e aponta os caminhos usuais; sem nenhum certificado da máquina o recado é que a CA não está instalada; e a linha de declaração sai com barra normal — verified by `backend/tests/test_bundle_ca_do_sistema.py`.
append-criterion [verified] O diagnóstico nomeia o emissor do certificado apresentado pelo destino e não derruba nada quando o destino está inalcançável — verified by `backend/tests/test_bundle_ca_do_sistema.py`.
```
