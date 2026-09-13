# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

O produto é escuro e continua escuro: é a identidade dele, e trocá-la sem
demanda de ninguém seria reescrever a cara da ferramenta. O que falta é a
escolha — quem trabalha em sala clara, ou projeta a tela numa reunião de
QA, lê pior num fundo escuro, e hoje não tem alternativa.

O caminho já estava quase pronto: tudo lê token. Quase. Dez cores estão
cravadas no código dos componentes — nove no gráfico de tendência do
dashboard (grade, eixos, tooltip e as três barras) e duas em links. Elas são
exatamente o que quebraria num tema claro: grade cinza-escura sobre fundo
branco some, e texto claro sobre tooltip branco desaparece. Enquanto
estiverem cravadas, "tema claro" é uma promessa que o dashboard não cumpre.

Por isso a ordem importa: primeiro as cores voltam a ser token, depois o
tema existe. O contrário entregaria uma tela clara com um gráfico ilegível
no meio.

```ops
bump-version minor
append-requirement ubiquitous: The system shall derivar toda cor exibida — inclusive a de gráfico, grade, eixo e dica de valor — dos tokens em tempo de execução, admitindo valor escrito apenas como último recurso caso a leitura do token falhe.
append-requirement ubiquitous: The system shall oferecer tema claro além do escuro, com a escolha guardada no navegador de quem escolheu e aplicada antes da primeira pintura.
append-requirement state: While a pessoa não tiver escolhido um tema, the system shall seguir a preferência declarada pelo sistema operacional dela.
append-requirement unwanted: The system shall not trocar o tema escuro por claro como padrão do produto; a escolha é de quem lê, e o escuro continua sendo o ponto de partida.
append-criterion [unverified] Grade, eixos, dica de valor e barras do gráfico acompanham o tema porque vêm dos tokens, e não de cor decidida no componente — verified by `frontend/src/components/Dashboard.tsx`.
append-criterion [unverified] O tema claro muda fundo, superfície, borda e texto mantendo os estados distinguíveis, e a escolha sobrevive ao recarregamento — verified by `frontend/src/styles.css` + `frontend/src/theme.ts`.
```
