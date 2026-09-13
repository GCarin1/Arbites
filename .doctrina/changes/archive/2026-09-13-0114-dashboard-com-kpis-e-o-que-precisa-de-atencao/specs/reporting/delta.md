# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

O dashboard hoje começa por dentro: painel executivo, health score, e só
então os indicadores. Quem abre a tela para responder "como estamos?" tem de
descer para achar o número, e o número aparece sem a leitura dele.

A reorganização inverte a ordem, no padrão das ferramentas de mercado: uma
linha de indicadores no topo, com os números que o produto **já apura** — sem
métrica nova — e logo abaixo um bloco em prosa dizendo o que precisa de
atenção.

O bloco é alimentado pelo resumo executivo de IA que já existe. A parte que
não pode falhar é a degradação: sem provider de IA configurado, o bloco não
some nem fica vazio — ele mostra os mesmos achados determinísticos que o
`GET /metrics/dashboard` já devolve (alertas e ações recomendadas). A leitura
do número é obrigação do dashboard; a IA é só a melhor redação dela.

```ops
bump-version minor
append-requirement ubiquitous: The system shall abrir o dashboard por uma linha de indicadores — cobertura de requisito, cobertura de execução, pass rate, taxa de bloqueio, retrabalho e health score —, todos derivados dos números que o produto já apura, sem métrica nova.
append-requirement ubiquitous: The system shall apresentar, logo abaixo dos indicadores, um bloco "O que precisa de atenção" em prosa, com a síntese, os riscos e as ações recomendadas do período filtrado.
append-requirement state: While não houver provider de IA configurado, the system shall preencher o bloco de atenção com os alertas e as ações recomendadas determinísticos de `GET /metrics/dashboard`, em vez de esconder o bloco ou deixá-lo vazio.
append-requirement unwanted: The system shall not condicionar nenhum número do dashboard à disponibilidade da IA; o indicador é apurado do índice e continua correto com a IA desligada.
append-criterion [unverified] O contexto do bloco de atenção traz os indicadores do período filtrado e as ações recomendadas, e nenhum deles depende de provider de IA configurado — verified by `backend/tests/test_dashboard_attention.py`.
append-criterion [unverified] Com a IA desligada o dashboard responde inteiro e o bloco de atenção é preenchido pelos achados determinísticos; com provider, o resumo narrado é gerado a partir dos mesmos números — verified by `backend/tests/test_dashboard_attention.py`.
```
