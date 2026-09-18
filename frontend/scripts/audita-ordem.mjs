/**
 * A ORDEM das seções da Observabilidade, verificada no DOM (change 0196).
 *
 * "O que mudou" e "Testes instáveis" abriam a aba e empurravam para baixo os
 * números que se consulta todo dia. Notícia vem depois do estado, e essa é
 * uma decisão que uma edição futura desfaz sem querer — daí a verificação.
 *
 * Uso:
 *   node frontend/scripts/audita-ordem.mjs --url http://127.0.0.1:8347 \
 *        --email voce@exemplo.com --senha ...
 *
 * Código 1 se a ordem quebrou, para poder virar gate.
 */

let chromium;
try {
  ({ chromium } = await import("playwright"));
} catch {
  const raiz = process.env.PLAYWRIGHT_ROOT;
  if (!raiz) {
    console.error("playwright não encontrado. PLAYWRIGHT_ROOT=<node_modules>");
    process.exit(2);
  }
  ({ chromium } = await import(`${raiz}/playwright/index.mjs`));
}

function arg(nome, padrao) {
  const i = process.argv.indexOf(`--${nome}`);
  return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : padrao;
}

const url = arg("url", "http://127.0.0.1:8347");
const email = arg("email", "");
const senha = arg("senha", "");

// A ordem esperada, do topo para o fim. O estado primeiro; as listas de
// exceção e a área de investigação depois.
const ESPERADA = [
  "Execuções no período",
  "Execuções por resultado",
  "Sinais no tempo",
  "Onde doer",
  "O que mudou",
];

const navegador = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
});
const ctx = await navegador.newContext({ viewport: { width: 1440, height: 1000 } });
const pagina = await ctx.newPage();
await pagina.goto(url);
if (email) {
  await pagina.fill("input[type=email]", email);
  await pagina.fill("input[type=password]", senha);
  await pagina.click("button[type=submit]");
  await pagina.waitForTimeout(1800);
}
await pagina.goto(`${url}/#/observability`);
await pagina.waitForTimeout(3000);

const posicoes = await pagina.evaluate((titulos) => {
  const achar = (texto) => {
    const nos = [...document.querySelectorAll("h2, h3, h4, span")];
    const no = nos.find((n) => n.textContent.trim() === texto);
    if (!no) return null;
    return no.getBoundingClientRect().top + window.scrollY;
  };
  return titulos.map((t) => [t, achar(t)]);
}, ESPERADA);

let falhou = false;
let anterior = -Infinity;
let anteriorNome = "(topo)";
for (const [titulo, y] of posicoes) {
  if (y === null) {
    console.log(`·  ${titulo}: ausente nesta instância (sem dado no período)`);
    continue;
  }
  if (y < anterior) {
    console.log(`✗  "${titulo}" aparece ANTES de "${anteriorNome}"`);
    falhou = true;
  } else {
    console.log(`ok ${titulo}`);
  }
  anterior = y;
  anteriorNome = titulo;
}

await navegador.close();
console.log(falhou ? "\nordem quebrada" : "\nordem correta");
process.exit(falhou ? 1 : 0);
