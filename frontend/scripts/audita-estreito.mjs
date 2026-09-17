/**
 * Detector de quebra de layout em tela estreita (change 0181).
 *
 * Por que existe: medir `document.documentElement.scrollWidth` contra
 * `innerWidth` — o teste que esta base usava — só pega o estouro da PÁGINA.
 * As telas passavam nele e ainda assim quebravam, porque o que quebra de
 * verdade em 390px passa por baixo desse número:
 *
 *   - texto cortado DENTRO de um cartão (o pai tem `overflow: hidden` e
 *     `text-overflow: ellipsis`: a página não estoura, a frase some);
 *   - filho mais largo que o ancestral que o corta;
 *   - elemento passando da borda da viewport;
 *   - alvo de toque abaixo de 24x24 CSS px (WCAG 2.5.8 AA).
 *
 * Três coisas NÃO são defeito e o detector precisa saber disso, senão o
 * ruído afoga o achado:
 *   - a gaveta do menu, que mora fora da tela quando fechada;
 *   - filho largo dentro de um container que ROLA de lado (é o padrão aceito
 *     aqui para tabela e faixa de abas);
 *   - texto `.sr-only`, recortado de propósito.
 *
 * Uso:
 *   node frontend/scripts/audita-estreito.mjs --url http://127.0.0.1:8000 \
 *        --email voce@exemplo.com --senha ... [--largura 390]
 *
 * Saída: uma linha por tela, e o detalhe de cada achado. Código 1 se achou
 * algo, para poder virar gate.
 */

/* Playwright NÃO é dependência do projeto: instalá-lo aqui puxaria centenas
   de MB para quem só quer rodar o Arbites, e este script é ferramenta de
   quem revisa, não do produto. Resolve de onde estiver — do projeto, do
   global, ou de onde `PLAYWRIGHT_ROOT` apontar. */
let chromium;
try {
  ({ chromium } = await import("playwright"));
} catch {
  const raiz = process.env.PLAYWRIGHT_ROOT;
  if (!raiz) {
    console.error(
      "playwright não encontrado.\n"
      + "  npm i -D playwright && npx playwright install chromium\n"
      + "ou aponte uma instalação existente:\n"
      + "  PLAYWRIGHT_ROOT=/caminho/para/node_modules node frontend/scripts/audita-estreito.mjs ...",
    );
    process.exit(2);
  }
  // `playwright/index.js` é CJS: num import dinâmico o objeto exportado
  // chega em `.default`, e desestruturar direto devolve undefined.
  const mod = await import(`${raiz}/playwright/index.js`);
  chromium = mod.chromium ?? mod.default?.chromium;
}

const arg = (nome, padrao) => {
  const i = process.argv.indexOf(`--${nome}`);
  return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : padrao;
};

const URL = arg("url", "http://127.0.0.1:8000");
const EMAIL = arg("email", "");
const SENHA = arg("senha", "");
const LARGURA = Number(arg("largura", 390));
const NAVEGADOR = arg(
  "chromium",
  process.env.PLAYWRIGHT_CHROMIUM || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
);

/** Telas do menu; `abas` são as faixas internas a visitar em cada uma. */
const TELAS = [
  ["Hoje", null],
  ["Requisitos", null],
  ["Test cases", null],
  ["Execuções", null],
  ["Automação", null],
  ["Dashboard", null],
  ["Observabilidade",
    ["Painel", "Acessibilidade", "Evidências", "Análise", "Configuração"]],
  ["Defeitos", null],
  ["Afazeres", null],
  ["Auditoria", null],
  ["IA", null],
];

const DETECTOR = () => {
  const achados = [];
  const vw = window.innerWidth;
  const texto = (el) => (el.innerText || el.textContent || "").trim().slice(0, 70);
  const onde = (el) => {
    const partes = [];
    let n = el;
    for (let i = 0; n && i < 3; i++, n = n.parentElement) {
      const cls = typeof n.className === "string" && n.className.trim()
        ? "." + n.className.trim().split(/\s+/).slice(0, 2).join(".")
        : "";
      partes.unshift(n.tagName.toLowerCase() + cls);
    }
    return partes.join(" > ");
  };

  // A gaveta do menu mora fora da tela quando fechada: tudo dentro dela
  // sairia como falso positivo.
  const foraDeTela = [];
  for (const el of document.querySelectorAll("body *")) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && (r.right <= 0 || r.left >= vw)) foraDeTela.push(el);
  }
  const escondido = (el) => foraDeTela.some((raiz) => raiz.contains(el));
  const soLeitor = (el) => el.closest(".sr-only, .visually-hidden") !== null;
  const rolaDeLado = (el) => {
    for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) {
      if (["auto", "scroll"].includes(getComputedStyle(n).overflowX)
          && n.scrollWidth > n.clientWidth + 1) return true;
    }
    return false;
  };
  /** O ancestral que realmente CORTA — não o pai imediato. Um gráfico pode
   *  ser mais largo que seu wrapper e ainda caber no cartão. */
  const cortador = (el) => {
    for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.overflowX !== "visible" || cs.overflowY !== "visible") return n;
    }
    return null;
  };

  for (const el of document.querySelectorAll("body *")) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (escondido(el) || soLeitor(el)) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || cs.display === "none" || cs.opacity === "0") continue;

    if (!rolaDeLado(el)) {
      if (r.right > vw + 1) {
        achados.push({ tipo: "passa-da-viewport", px: Math.round(r.right - vw),
                       onde: onde(el), texto: texto(el) });
      }
      if (r.left < -1) {
        achados.push({ tipo: "antes-da-esquerda", px: Math.round(-r.left),
                       onde: onde(el), texto: texto(el) });
      }
      const corta = cortador(el);
      if (corta) {
        const rc = corta.getBoundingClientRect();
        const csc = getComputedStyle(corta);
        if (!["auto", "scroll"].includes(csc.overflowX) && r.right > rc.right + 2) {
          achados.push({ tipo: "cortado-pelo-ancestral",
                         px: Math.round(r.right - rc.right),
                         onde: onde(el), texto: texto(el) });
        }
      }
    }

    const ehCampo = ["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName);
    if (!ehCampo && cs.overflowX === "hidden" && el.scrollWidth > el.clientWidth + 1) {
      achados.push({ tipo: "texto-cortado", px: el.scrollWidth - el.clientWidth,
                     onde: onde(el), texto: texto(el) });
    }
  }

  /* Rotulo de celula empilhada escrito POR CIMA do valor.
     Nao e estouro: os dois cabem na linha, um em cima do outro. O texto do
     `::before` e ink, nao caixa — a caixa continua com a largura da faixa —,
     entao nenhuma medida de retangulo pega. Mede-se a largura NATURAL do
     texto com a fonte do proprio pseudo-elemento e compara-se com a faixa. */
  const regua = document.createElement("span");
  regua.style.cssText = "position:absolute;visibility:hidden;white-space:pre;left:-9999px";
  document.body.appendChild(regua);
  for (const td of document.querySelectorAll("td[data-label]")) {
    const cs = getComputedStyle(td);
    if (cs.display !== "grid" || escondido(td)) continue;
    const antes = getComputedStyle(td, "::before");
    const faixa = parseFloat(cs.gridTemplateColumns.split(" ")[0]);
    if (!faixa) continue;
    regua.style.font = antes.font || `${antes.fontSize} ${antes.fontFamily}`;
    regua.style.letterSpacing = antes.letterSpacing;
    regua.style.textTransform = antes.textTransform;
    regua.textContent = td.getAttribute("data-label") || "";
    const natural = regua.getBoundingClientRect().width;
    if (antes.whiteSpace === "nowrap" && natural > faixa + 1) {
      achados.push({ tipo: "rotulo-sobre-o-valor",
                     px: Math.round(natural - faixa),
                     onde: onde(td),
                     texto: td.getAttribute("data-label") || "" });
    }
  }
  regua.remove();

  for (const el of document.querySelectorAll(
    "button, a, [role='tab'], input[type=checkbox]")) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0 || escondido(el) || soLeitor(el)) continue;
    // Exceção DECLARADA no elemento, não escondida aqui: `data-alvo-pequeno`
    // diz qual é o caminho equivalente (a exceção "Equivalent" do 2.5.8).
    // Quem declara assume; quem lê o markup vê a justificativa.
    if (el.hasAttribute("data-alvo-pequeno")) continue;
    if (r.height < 24 && (el.innerText || "").trim()) {
      achados.push({ tipo: "alvo-pequeno", px: Math.round(r.height),
                     onde: onde(el), texto: texto(el) });
    }
  }
  return { overflowPagina: document.documentElement.scrollWidth - vw, achados };
};

const navegador = await chromium.launch({ executablePath: NAVEGADOR });
const pagina = await navegador.newPage({ viewport: { width: LARGURA, height: 844 } });
await pagina.goto(URL, { waitUntil: "networkidle" });

if (EMAIL) {
  await pagina.fill("#login-email", EMAIL);
  await pagina.fill("#login-password", SENHA);
  await pagina.click(".login-submit");
  await pagina.waitForTimeout(2500);
}

let total = 0;
for (const [tela, abas] of TELAS) {
  await pagina.evaluate(() =>
    document.querySelector(".nav-toggle, [aria-label='Menu'], .hamburger")?.click());
  await pagina.waitForTimeout(350);
  const abriu = await pagina.evaluate((t) => {
    const alvo = [...document.querySelectorAll("button, a")]
      .find((e) => e.innerText.trim() === t);
    if (alvo) { alvo.click(); return true; }
    return false;
  }, tela);
  if (!abriu) { console.log(`--  ${tela}: não encontrada no menu`); continue; }
  await pagina.waitForTimeout(1800);

  for (const aba of abas ?? [null]) {
    if (aba) {
      await pagina.evaluate((a) => [...document.querySelectorAll('[role="tab"], button')]
        .find((e) => e.innerText.trim() === a)?.click(), aba);
      await pagina.waitForTimeout(1400);
    }
    const nome = aba ? `${tela} / ${aba}` : tela;
    const r = await pagina.evaluate(DETECTOR);
    total += r.achados.length;
    const marca = r.achados.length === 0 && r.overflowPagina <= 0 ? "ok " : ">> ";
    console.log(`${marca}${nome}: ${r.achados.length} achado(s)`
      + (r.overflowPagina > 0 ? ` · página estoura ${r.overflowPagina}px` : ""));
    const vistos = new Set();
    for (const a of r.achados) {
      const chave = `${a.tipo}|${a.onde}`;
      if (vistos.has(chave)) continue;
      vistos.add(chave);
      console.log(`      [${a.tipo} ${a.px}px] ${a.onde}`);
      if (a.texto) console.log(`        ${JSON.stringify(a.texto)}`);
    }
  }
}
await navegador.close();
console.log(total === 0 ? "\nnenhum achado" : `\n${total} achado(s) no total`);
process.exit(total === 0 ? 0 : 1);
