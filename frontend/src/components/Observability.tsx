import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { EmptyState } from "./EmptyState";
import { ConfirmModal } from "./Modal";
import { Pizza } from "./Pizza";
import { Esqueleto, Progresso } from "./Progresso";
import { TabBar } from "./TabBar";
import { DocBody } from "./ReadView";
import type {
  CiFlaky,
  CiRetention,
  CiRun,
  CiSignalSeries,
  CiAnalise,
  CiAnaliseResumo,
  CiComparativo,
  CiEvidencia,
  CiEvidencias,
  CiRecorte,
  CiSource,
  Observability as Painel,
} from "../types";

/**
 * Observabilidade — o que mudou, quando e por quê (change 0155, ADR 0016).
 *
 * A diferença para o Dashboard não é o nome, é o EIXO. O Dashboard responde
 * "como está agora": é retrato, e serve a quem pergunta o estado. Aqui o eixo
 * é o TEMPO, e toda resposta vem com o período anterior ao lado — um número
 * sozinho não diz se está melhorando.
 *
 * Duas regras mandam no que entra nesta tela:
 *
 * 1. **Todo bloco nomeia a pergunta que responde.** Bloco que não responde a
 *    "o que quebrou desde ontem", "que sinal regrediu" ou "por onde começo a
 *    olhar" não entra. Observabilidade sem pergunta é mural de gráficos.
 *
 * 2. **A descida é obrigatória.** Do ponto do gráfico até o print, sem sair
 *    da aba: ponto → run → job → anexo. Gráfico do qual não se desce é
 *    decoração — mostra que houve um pico e abandona quem olha exatamente no
 *    momento em que a pergunta ficou interessante.
 */

const PERIODOS = [
  { dias: 7, rotulo: "7 dias" },
  { dias: 30, rotulo: "30 dias" },
  { dias: 90, rotulo: "90 dias" },
];

/** O nome técnico é chave de série, não título de cartão. Os derivados são
    um conjunto fechado (ADR 0019), então a tradução cabe aqui — e um nome
    fora da lista aparece como veio, porque um declarado não se traduz. */
const NOME_DO_SINAL: Record<string, string> = {
  duracao_min: "Duração da execução",
  resultado: "Passou (1) ou falhou (0)",
  jobs_falhos: "Jobs que falharam",
  cenarios: "Cenários executados",
  cenarios_falhos: "Cenários que falharam",
  cenarios_taxa: "Cenários aprovados",
  acessibilidade_violacoes: "Violações de acessibilidade",
  acessibilidade_critical: "Violações críticas",
  acessibilidade_serious: "Violações graves",
  wcag_criterios_violados: "Critérios WCAG violados",
};

function formatarData(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? "—"
    : d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
}

/**
 * Plural em português não é sufixo: "execução" vira "execuções", trocando o
 * radical. Concatenar "ões" produz "execuçãoões" — e isso foi para a tela
 * antes de alguém medir.
 */
function plural(n: number, singular: string, plural_: string): string {
  return `${n} ${n === 1 ? singular : plural_}`;
}

function formatarBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const unidades = ["KB", "MB", "GB"];
  let valor = bytes / 1024;
  let i = 0;
  while (valor >= 1024 && i < unidades.length - 1) {
    valor /= 1024;
    i += 1;
  }
  return `${valor.toFixed(valor >= 10 ? 0 : 1)} ${unidades[i]}`;
}

function formatarValor(valor: number | null, unidade: string | null): string {
  if (valor === null || valor === undefined) return "—";
  const numero = Number.isInteger(valor) ? String(valor) : valor.toFixed(2);
  return unidade ? `${numero} ${unidade}` : numero;
}

/**
 * A seta de variação. Quando a direção NÃO foi declarada no `arbites.yaml`,
 * ela é neutra de propósito: o Arbites não sabe que `lcp_ms` maior é pior, e
 * pintar de vermelho um número que subiu seria opinião disfarçada de medição.
 */
function Variacao({ sinal }: { sinal: CiSignalSeries }) {
  if (sinal.delta_pct === null) {
    return <span className="obs-delta obs-delta-neutro">sem base anterior</span>;
  }
  const subiu = sinal.delta_pct > 0;
  const julga = sinal.direction === "lower" || sinal.direction === "higher";
  const pior = sinal.direction === "lower" ? subiu : !subiu;
  const classe = !julga ? "obs-delta-neutro" : pior ? "obs-delta-pior" : "obs-delta-melhor";
  return (
    <span className={`obs-delta ${classe}`}>
      {subiu ? "▲" : "▼"} {Math.abs(sinal.delta_pct)}%
      <span className="obs-delta-base">
        {" "}
        vs. {formatarValor(sinal.previous_average, sinal.unit)}
      </span>
    </span>
  );
}

/**
 * Série em SVG, sem biblioteca: são poucos pontos e o que importa é a FORMA
 * e poder clicar num ponto. Cada ponto é um botão — é ele que começa a
 * descida.
 */
function Serie({
  sinal,
  onPonto,
  selecionado,
}: {
  sinal: CiSignalSeries;
  onPonto: (runId: string) => void;
  selecionado: string | null;
}) {
  const largura = 100;
  const altura = 32;
  const pontos = sinal.points;
  const geometria = useMemo(() => {
    if (pontos.length === 0) return { caminho: "", coords: [] as { x: number; y: number }[] };
    const valores = pontos.map((p) => p.value);
    const min = Math.min(...valores, sinal.goal ?? Infinity);
    const max = Math.max(...valores, sinal.goal ?? -Infinity);
    const amplitude = max - min || 1;
    const coords = pontos.map((p, i) => ({
      x: pontos.length === 1 ? largura / 2 : (i / (pontos.length - 1)) * largura,
      y: altura - ((p.value - min) / amplitude) * altura,
    }));
    return {
      caminho: coords.map((c, i) => `${i ? "L" : "M"}${c.x},${c.y}`).join(" "),
      coords,
      metaY:
        sinal.goal === null
          ? null
          : altura - ((sinal.goal - min) / amplitude) * altura,
    };
  }, [pontos, sinal.goal]);

  if (pontos.length === 0) {
    return <p className="obs-sem-ponto">sem medida neste período</p>;
  }
  return (
    // `--pontos` vai para o CSS porque ele nao sabe contar: e o que da a
    // largura minima da serie e impede que dezenas de pontos virem um borrao
    // de 3px em que nenhum toque acerta (change 0181).
    <div className="obs-serie-rolagem">
    <div
      className="obs-serie"
      style={{ "--pontos": pontos.length } as React.CSSProperties}
    >
      <svg viewBox={`0 0 ${largura} ${altura}`} preserveAspectRatio="none" aria-hidden="true">
        {geometria.metaY !== null && geometria.metaY !== undefined && (
          <line
            x1={0}
            x2={largura}
            y1={geometria.metaY}
            y2={geometria.metaY}
            className="obs-meta-linha"
          />
        )}
        <path d={geometria.caminho} className="obs-linha" />
      </svg>
      <div className="obs-pontos">
        {pontos.map((ponto, i) => (
          <button
            key={`${ponto.run_id}-${i}`}
            type="button"
            className={`obs-ponto ${
              ponto.conclusion && ponto.conclusion !== "success" ? "obs-ponto-falha" : ""
            } ${selecionado === ponto.run_id ? "obs-ponto-ativo" : ""}`.trim()}
            /* WCAG 2.5.8 pede 24x24, e este circulo tem 16. Cresce-lo faria
               os pontos da serie se sobreporem, e a excecao "Equivalente" do
               proprio criterio se aplica: a tabela Execucoes recentes abre a
               MESMA descida, com linha de altura cheia. A excecao fica
               declarada aqui, e nao escondida no detector. */
            data-alvo-pequeno="equivalente: tabela Execuções recentes"
            style={{
              left: `${pontos.length === 1 ? 50 : (i / (pontos.length - 1)) * 100}%`,
              bottom: `${geometria.coords[i] ? 100 - (geometria.coords[i].y / altura) * 100 : 50}%`,
            }}
            onClick={() => onPonto(ponto.run_id)}
            title={`${formatarValor(ponto.value, sinal.unit)} em ${formatarData(ponto.at)} — abrir a execução`}
          >
            <span className="sr-only">
              {formatarValor(ponto.value, sinal.unit)} em {formatarData(ponto.at)}
            </span>
          </button>
        ))}
      </div>
    </div>
    </div>
  );
}

/** A descida: run → job → anexo, aberta no lugar, sem trocar de aba. */
function Descida({ run, onFechar }: { run: CiRun; onFechar: () => void }) {
  const verde = run.conclusion === "success";
  return (
    <section className="card obs-descida" aria-label={`Execução ${run.run_id}`}>
      <header className="obs-descida-topo">
        <div>
          <h3>
            {run.workflow}{" "}
            <span className={`badge ${verde ? "obs-badge-ok" : "obs-badge-falha"}`}>
              {run.conclusion ?? "—"}
            </span>
          </h3>
          <p className="muted">
            {run.event ?? "—"} · {formatarData(run.started_at)} ·{" "}
            {run.branch ?? "—"} · {(run.commit_sha ?? "").slice(0, 7) || "—"}
          </p>
        </div>
        <div className="obs-descida-acoes">
          {run.url && (
            <a className="button-link" href={run.url} target="_blank" rel="noreferrer">
              Ver no provedor
            </a>
          )}
          <button type="button" className="btn-sm" onClick={onFechar}>
            Fechar
          </button>
        </div>
      </header>

      {run.ingest_warning && <p className="obs-aviso">{run.ingest_warning}</p>}

      {run.jobs.length > 0 && (
        <div className="obs-bloco">
          <h4>Jobs</h4>
          <ul className="obs-jobs">
            {run.jobs.map((job) => (
              <li key={job.name}>
                <span
                  className={`obs-bolinha ${
                    job.conclusion === "success" ? "ok" : "falha"
                  }`}
                  aria-hidden="true"
                />
                {job.url ? (
                  <a href={job.url} target="_blank" rel="noreferrer">
                    {job.name}
                  </a>
                ) : (
                  job.name
                )}
                <span className="muted"> · {job.conclusion ?? "—"}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {run.signals.length > 0 && (
        <div className="obs-bloco">
          <h4>Medidas desta execução</h4>
          <ul className="obs-medidas">
            {run.signals.map((s) => (
              <li key={s.name}>
                <span className="obs-medida-nome">{s.name}</span>
                <strong>{formatarValor(s.value, s.unit)}</strong>
              </li>
            ))}
          </ul>
        </div>
      )}

      {run.attachments.length > 0 && (
        <div className="obs-bloco">
          <h4>Anexos</h4>
          <div className="obs-anexos">
            {run.attachments.map((anexo) => (
              <a
                key={anexo.path}
                className="obs-anexo"
                href={api.ciAttachmentUrl(anexo.path)}
                target="_blank"
                rel="noreferrer"
              >
                {anexo.kind === "screenshot" ? (
                  <img src={api.ciAttachmentUrl(anexo.path)} alt={anexo.title ?? anexo.path} />
                ) : (
                  <span className="obs-anexo-arquivo">{anexo.kind}</span>
                )}
                <span className="obs-anexo-nome">
                  {anexo.title ?? anexo.path.split("/").pop()}
                </span>
              </a>
            ))}
          </div>
        </div>
      )}

      {run.analysis && (
        <div className="obs-bloco">
          {/* A análise que o pipeline já escreveu. Reescrevê-la aqui seria
              desperdiçar trabalho feito — ela é renderizada como veio. */}
          <h4>Análise da automação</h4>
          <div className="obs-analise">
            <DocBody text={run.analysis} />
          </div>
        </div>
      )}
    </section>
  );
}

/**
 * Retenção (change 0156) — a prévia ANTES da limpeza.
 *
 * Duas coisas que não são negociáveis aqui: a tela diz o que a limpeza
 * levaria antes de levar (limpeza que só conta o que fez depois de feita
 * obriga a confiar sem poder conferir), e o removido vai para a lixeira,
 * como todo o resto do produto.
 *
 * A regra que o texto precisa deixar clara para quem clica: **o sinal fica,
 * o anexo vai.** A série continua respondendo sobre agosto depois que o
 * print de agosto já foi descartado — é esse o trade-off.
 */
function Retencao({
  onError,
  onLimpou,
}: {
  onError: (message: string) => void;
  onLimpou: () => void;
}) {
  const [dados, setDados] = useState<CiRetention | null>(null);
  const [aberto, setAberto] = useState(false);
  const [limpando, setLimpando] = useState(false);

  const carregar = useCallback(async () => {
    try {
      setDados(await api.ciRetention());
    } catch (e) {
      onError((e as Error).message);
    }
  }, [onError]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  if (!dados) return null;
  const { usage: uso, would_remove: alvo, retention: janelas } = dados;

  return (
    <section className="card obs-retencao">
      <div className="obs-retencao-topo">
        <div>
          <h3>Espaço e retenção</h3>
          <p className="obs-pergunta">
            Quanto isto ocupa, e o que a próxima limpeza levaria.
          </p>
        </div>
        <button type="button" className="btn-sm" onClick={() => setAberto((v) => !v)}>
          {aberto ? "Ocultar" : "Detalhar"}
        </button>
      </div>

      <p className="obs-retencao-linha">
        <strong>{formatarBytes(uso.total_bytes)}</strong> em{" "}
        {plural(uso.runs, "execução", "execuções")} —{" "}
        {formatarBytes(uso.attachments_bytes)} são anexos (print, log) e{" "}
        {formatarBytes(uso.documents_bytes)} são os documentos com os sinais.
      </p>
      <p className="caption muted">
        Anexo é guardado por {janelas.attachments_days} dias; sinal, por{" "}
        {janelas.signals_days}. O anexo é caro e só interessa perto do evento; o
        sinal é barato e é o que faz a série — por isso o print some primeiro e a
        pergunta sobre aquele mês continua respondida.
      </p>

      {alvo.bytes === 0 ? (
        <p className="muted">
          Nada passou das janelas ainda — não há o que limpar.
        </p>
      ) : (
        <>
          <p className="obs-retencao-alvo">
            A próxima limpeza levaria <strong>{formatarBytes(alvo.bytes)}</strong>:
            anexos de {plural(alvo.attachments.length, "execução", "execuções")}
            {alvo.runs.length > 0 && (
              <>
                {" "}e{" "}
                {plural(
                  alvo.runs.length,
                  "execução inteira",
                  "execuções inteiras",
                )}{" "}
                (essas passaram até da janela do sinal)
              </>
            )}
            . Tudo vai para a lixeira e volta enquanto ela não for esvaziada.
          </p>
          {aberto && (
            <ul className="obs-retencao-lista">
              {alvo.attachments.map((item) => (
                <li key={item.path}>
                  <span className="obs-medida-nome">anexos</span> {item.id} ·{" "}
                  {formatarData(item.at)} ·{" "}
                  {plural(item.files, "arquivo", "arquivos")} ·{" "}
                  {formatarBytes(item.bytes)}
                </li>
              ))}
              {alvo.runs.map((item) => (
                <li key={item.path}>
                  <span className="obs-medida-nome">execução inteira</span> {item.id}{" "}
                  · {formatarData(item.at)} · {formatarBytes(item.bytes)}
                </li>
              ))}
            </ul>
          )}
          <button
            type="button"
            className="danger"
            disabled={limpando}
            onClick={() => {
              void (async () => {
                setLimpando(true);
                try {
                  await api.ciRetentionApply();
                  await carregar();
                  onLimpou();
                } catch (e) {
                  onError((e as Error).message);
                } finally {
                  setLimpando(false);
                }
              })();
            }}
          >
            {limpando ? "Limpando…" : "Limpar para a lixeira"}
          </button>
        </>
      )}
    </section>
  );
}

type Aba = "painel" | "acessibilidade" | "evidencias" | "analise" | "config";

const ABAS = [
  ["painel", "Painel"],
  ["acessibilidade", "Acessibilidade"],
  ["evidencias", "Evidências"],
  ["analise", "Análise"],
  ["config", "Configuração"],
] as const satisfies readonly (readonly [Aba, string])[];

const TIPOS_DE_ANEXO: Record<string, string> = {
  screenshot: "prints",
  log: "logs",
  analysis: "análises do pipeline",
  cucumber: "resultados",
  axe: "varreduras de acessibilidade",
  file: "outros",
};

const SAUDE: Record<string, string> = {
  boa: "obs-ok",
  atencao: "obs-atencao",
  ruim: "obs-ruim",
};

const VEREDITO: Record<string, string> = {
  melhorou: "obs-ok",
  piorou: "obs-ruim",
  estavel: "obs-atencao",
  misto: "obs-atencao",
};

/**
 * Galeria de evidências do período (change 0180).
 *
 * Até aqui a evidência só existia dentro da descida: para ver o print da
 * falha era preciso já saber em qual execução ela aconteceu — o que inverte a
 * ordem natural, porque muitas vezes é justamente o print que diz onde olhar.
 *
 * Cada peça carrega o contexto do run: sem ele um print solto não é evidência
 * de nada. E o recorte que se usa de verdade — "só das falhas" — vem ligado,
 * porque o print de um run verde quase nunca é o que se procura.
 */
function Evidencias({ dias, origens, onError, onAbrirRun }: {
  dias: number;
  origens: string[];
  onError: (message: string) => void;
  onAbrirRun: (runId: string) => void;
}) {
  const [dados, setDados] = useState<CiEvidencias | null>(null);
  const [tipo, setTipo] = useState("screenshot");
  const [origem, setOrigem] = useState("");
  const [soFalhas, setSoFalhas] = useState(true);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    let vivo = true;
    setCarregando(true);
    api
      .ciEvidencias({ days: dias, kind: tipo, origin: origem, failuresOnly: soFalhas })
      .then((r) => vivo && setDados(r))
      .catch((e) => vivo && onError((e as Error).message))
      .finally(() => vivo && setCarregando(false));
    return () => {
      vivo = false;
    };
  }, [dias, tipo, origem, soFalhas, onError]);

  const ehImagem = (e: CiEvidencia) => e.kind === "screenshot";

  return (
    <>
      <section className="card">
        <div className="card-head">
          <h3>Evidências do período</h3>
          <span className="spacer" />
          {dados && (
            <span className="caption muted">
              {formatarBytes(dados.total_bytes)} no total
            </span>
          )}
        </div>
        <p className="obs-pergunta">
          O que os testes deixaram para trás — print, log, varredura — com a
          execução que o produziu ao lado. Clique numa peça para abrir o
          arquivo; clique na execução para descer até ela.
        </p>
        <div className="toolbar obs-filtros-evidencia">
          <label className="caption" htmlFor="ev-tipo">Tipo</label>
          <select id="ev-tipo" value={tipo} onChange={(e) => setTipo(e.target.value)}>
            <option value="">todos</option>
            {(dados?.by_kind ?? []).map((f) => (
              <option key={f.label} value={f.label}>
                {TIPOS_DE_ANEXO[f.label] ?? f.label} ({f.value})
              </option>
            ))}
          </select>
          <label className="caption" htmlFor="ev-origem">Origem</label>
          <select
            id="ev-origem"
            value={origem}
            onChange={(e) => setOrigem(e.target.value)}
          >
            <option value="">todas</option>
            {origens.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
          <label className="caption obs-so-falhas">
            <input
              type="checkbox"
              checked={soFalhas}
              onChange={(e) => setSoFalhas(e.target.checked)}
            />
            só das execuções que falharam
          </label>
        </div>
      </section>

      {carregando && <Esqueleto linhas={4} titulo="Carregando evidências" />}

      {!carregando && dados && dados.items.length === 0 && (
        <EmptyState icon="dashboard" title="Nenhuma evidência com esses filtros">
          Os anexos entram junto com a execução, declarados no{" "}
          <code>arbites.json</code> do artifact. Se a busca está vazia, ou o
          período não tem execução com anexo, ou os filtros estão apertados
          demais — tente desmarcar “só das execuções que falharam”.
        </EmptyState>
      )}

      {!carregando && dados && dados.items.length > 0 && (
        <section className="card">
          {dados.truncated && (
            <p className="caption muted">
              Mostrando as mais recentes; há mais evidência no período do que
              cabe nesta lista.
            </p>
          )}
          <div className="obs-galeria">
            {dados.items.map((item) => (
              <figure key={`${item.run_id}:${item.path}`} className="obs-evidencia">
                <a
                  href={api.ciAttachmentUrl(item.path)}
                  target="_blank"
                  rel="noreferrer"
                  className="obs-evidencia-peca"
                >
                  {ehImagem(item) ? (
                    <img
                      src={api.ciAttachmentUrl(item.path)}
                      alt={item.title ?? item.path.split("/").pop() ?? ""}
                      loading="lazy"
                    />
                  ) : (
                    <span className="obs-evidencia-tipo">
                      {TIPOS_DE_ANEXO[item.kind] ?? item.kind}
                    </span>
                  )}
                </a>
                <figcaption>
                  <span className="obs-evidencia-nome">
                    {item.title ?? item.path.split("/").pop()}
                  </span>
                  {/* O contexto do run: sem ele um print solto não é
                      evidência de nada. */}
                  <button
                    type="button"
                    className="obs-evidencia-run"
                    onClick={() => onAbrirRun(item.run_id)}
                  >
                    <span
                      className={`status-dot ${
                        item.conclusion === "success"
                          ? "dot-col-passed"
                          : "dot-col-failed"
                      }`}
                    />
                    {item.trigger_repo ?? item.repo ?? item.run_id}
                  </button>
                  <span className="caption muted">
                    {formatarData(item.at)}
                    {item.bytes ? ` · ${formatarBytes(item.bytes)}` : ""}
                  </span>
                </figcaption>
              </figure>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

/**
 * Agente de análise, histórico e comparativo (change 0179).
 *
 * O painel responde perguntas isoladas; ninguém junta as três no fim do dia.
 * O agente junta, escreve o veredito e guarda — e duas análises guardadas
 * respondem a pergunta que nenhum gráfico responde: "melhorou desde então?".
 */
function Analise({ dias, onError }: {
  dias: number;
  onError: (message: string) => void;
}) {
  const [historico, setHistorico] = useState<CiAnaliseResumo[]>([]);
  const [aberta, setAberta] = useState<(CiAnalise & { body: string }) | null>(null);
  const [gerando, setGerando] = useState(false);
  const [comparando, setComparando] = useState(false);
  const [comparativo, setComparativo] = useState<CiComparativo | null>(null);
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [carregado, setCarregado] = useState(false);

  const carregarHistorico = useCallback(async () => {
    try {
      const r = await api.ciAnalises();
      setHistorico(r.analyses);
      // As duas mais recentes já vêm escolhidas: é a comparação que quase
      // todo mundo quer, e digitar dois ids não ajuda ninguém.
      if (r.analyses.length >= 2) {
        setA((atual) => atual || r.analyses[1].id);
        setB((atual) => atual || r.analyses[0].id);
      }
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setCarregado(true);
    }
  }, [onError]);

  useEffect(() => {
    void carregarHistorico();
  }, [carregarHistorico]);

  const gerar = async () => {
    setGerando(true);
    try {
      const nova = await api.ciAnalisar(dias);
      setAberta(nova);
      await carregarHistorico();
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setGerando(false);
    }
  };

  const comparar = async () => {
    if (!a || !b || a === b) return;
    setComparando(true);
    try {
      setComparativo(await api.ciCompararAnalises(a, b));
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setComparando(false);
    }
  };

  const abrir = async (id: string) => {
    try {
      setAberta(await api.ciAnalise(id));
    } catch (e) {
      onError((e as Error).message);
    }
  };

  if (!carregado) return <p className="empty">Carregando análises…</p>;

  return (
    <>
      <section className="card">
        <div className="card-head">
          <h3>Análise do período</h3>
          <span className="spacer" />
          <button className="primary" onClick={() => void gerar()} disabled={gerando}>
            {gerando ? "Analisando…" : `Analisar os últimos ${dias} dias`}
          </button>
        </div>
        <p className="obs-pergunta">
          O agente lê o período inteiro — saúde, sinais com meta declarada,
          cenários instáveis, acessibilidade e os dois recortes de repositório
          — e escreve o veredito. A análise fica guardada com os números que
          ela viu, para poder ser comparada depois.
        </p>
        {historico.length === 0 && (
          <p className="caption muted">
            Nenhuma análise ainda. Ela exige um provider de IA configurado em{" "}
            <strong>IA → Providers</strong>; a plataforma segue inteira sem ele.
          </p>
        )}
      </section>

      {aberta && (
        <section className="card obs-analise">
          <div className="card-head">
            <h3>{aberta.id}</h3>
            <span className="spacer" />
            {aberta.saude_geral && (
              <span className={`badge ${SAUDE[aberta.saude_geral] ?? ""}`}>
                {aberta.saude_geral}
              </span>
            )}
          </div>
          <p className="caption muted">
            {formatarData(aberta.created_at)}
            {aberta.provider ? ` · ${aberta.provider}` : ""}
          </p>
          <DocBody text={aberta.body} />
        </section>
      )}

      {historico.length > 0 && (
        <section className="card">
          <h3>Histórico</h3>
          <p className="obs-pergunta">
            Cada análise guarda os números do seu período — o histórico
            sobrevive a um reindex porque é arquivo no workspace.
          </p>
          <div className="table-wrap">
            <table className="dense stack-narrow">
              <thead>
                <tr>
                  <th>Análise</th>
                  <th>Quando</th>
                  <th>Período</th>
                  <th>Execuções</th>
                  <th>Taxa</th>
                  <th>Acessibilidade</th>
                  <th>Saúde</th>
                </tr>
              </thead>
              <tbody>
                {historico.map((item) => (
                  <tr
                    key={item.id}
                    className={aberta?.id === item.id ? "obs-linha-ativa" : ""}
                    onClick={() => void abrir(item.id)}
                  >
                    <td data-label="Análise" className="mono">{item.id}</td>
                    <td data-label="Quando">{formatarData(item.created_at)}</td>
                    <td data-label="Período">{item.days ?? "—"} dias</td>
                    <td data-label="Execuções">{item.runs ?? "—"}</td>
                    <td data-label="Taxa">
                      {item.success_rate === null ? "—" : `${item.success_rate}%`}
                    </td>
                    <td data-label="Acessibilidade">{item.findings_total ?? "—"}</td>
                    <td data-label="Saúde">
                      <span className={SAUDE[item.saude_geral ?? ""] ?? ""}>
                        {item.saude_geral ?? "—"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {historico.length >= 2 && (
        <section className="card">
          <h3>Comparar duas análises</h3>
          <p className="obs-pergunta">
            A pergunta que nenhum gráfico responde: melhorou desde então? A
            comparação vai sempre da mais antiga para a mais recente.
          </p>
          <div className="toolbar obs-comparar">
            <label className="caption" htmlFor="obs-comp-a">De</label>
            <select id="obs-comp-a" value={a} onChange={(e) => setA(e.target.value)}>
              {historico.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.id} — {formatarData(h.created_at)}
                </option>
              ))}
            </select>
            <label className="caption" htmlFor="obs-comp-b">Para</label>
            <select id="obs-comp-b" value={b} onChange={(e) => setB(e.target.value)}>
              {historico.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.id} — {formatarData(h.created_at)}
                </option>
              ))}
            </select>
            <button
              className="primary"
              onClick={() => void comparar()}
              disabled={comparando || !a || !b || a === b}
            >
              {comparando ? "Comparando…" : "Comparar"}
            </button>
          </div>
          {a === b && a !== "" && (
            <p className="caption muted">Escolha duas análises diferentes.</p>
          )}
          {comparativo && (
            <div className="obs-comparativo">
              <p>
                <span className={`badge ${VEREDITO[comparativo.veredito] ?? ""}`}>
                  {comparativo.veredito}
                </span>{" "}
                <span className="caption muted">
                  {comparativo.from} → {comparativo.to}
                </span>
              </p>
              <p>{comparativo.sintese}</p>
              {([
                ["Melhorou", comparativo.melhoras, "obs-ok"],
                ["Piorou", comparativo.pioras, "obs-ruim"],
                ["Continua igual", comparativo.permanece, "obs-atencao"],
              ] as const).map(([titulo, itens, classe]) =>
                itens.length ? (
                  <div key={titulo}>
                    <h4 className={classe}>{titulo}</h4>
                    <ul>
                      {itens.map((t, i) => (
                        <li key={i}>{t}</li>
                      ))}
                    </ul>
                  </div>
                ) : null,
              )}
              {comparativo.proximo_passo && (
                <p>
                  <strong>Próximo passo:</strong> {comparativo.proximo_passo}
                </p>
              )}
            </div>
          )}
        </section>
      )}
    </>
  );
}

const IMPACTOS: Record<string, string> = {
  critical: "crítico",
  serious: "grave",
  moderate: "moderado",
  minor: "leve",
  unknown: "sem classificação",
};

const CONCLUSOES: Record<string, string> = {
  success: "passou",
  failure: "falhou",
  cancelled: "cancelado",
  timed_out: "estourou o tempo",
};

const STATUS_CENARIO: Record<string, string> = {
  passed: "passou",
  failed: "falhou",
  blocked: "bloqueado",
  skipped: "pulado",
};

/**
 * Saúde por recorte — repositório de teste, componente, ambiente (0176).
 *
 * Num projeto de micro-frontends a média global não é a saúde de nada: oito
 * componentes atrás de uma taxa só escondem exatamente o que se quer ver.
 * Pior primeiro, porque quem abre o painel quer saber onde dói.
 */
function Recorte({ titulo, pergunta, itens }: {
  titulo: string;
  pergunta: string;
  itens: CiRecorte[];
}) {
  if (!itens.length) return null;
  return (
    <section className="card obs-recorte">
      <h3>{titulo}</h3>
      <p className="obs-pergunta">{pergunta}</p>
      <div className="table-wrap">
        <table className="dense stack-narrow">
          <thead>
            <tr>
              <th>{titulo}</th>
              <th>Execuções</th>
              <th>Falhas</th>
              <th>Taxa de sucesso</th>
              <th>vs. anterior</th>
            </tr>
          </thead>
          <tbody>
            {itens.map((item) => (
              <tr key={item.name}>
                <td data-label={titulo} className="mono">{item.name}</td>
                <td data-label="Execuções">
                  {item.runs}
                  {item.inconclusive > 0 && (
                    <span className="caption muted">
                      {` (${item.inconclusive} fora da conta)`}
                    </span>
                  )}
                </td>
                <td data-label="Falhas">{item.failures}</td>
                <td data-label="Taxa de sucesso">
                  <span
                    className={
                      item.success_rate === null
                        ? ""
                        : item.success_rate >= 95
                          ? "obs-ok"
                          : item.success_rate >= 80
                            ? "obs-atencao"
                            : "obs-ruim"
                    }
                  >
                    {item.success_rate === null ? "—" : `${item.success_rate}%`}
                  </span>
                </td>
                <td data-label="vs. anterior" className="caption muted">
                  {item.delta_pct === null
                    ? "sem base anterior"
                    : `${item.delta_pct > 0 ? "+" : ""}${item.delta_pct}%`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/**
 * Acessibilidade em aba própria (0176).
 *
 * `violacoes_axe: 14` diz que piorou, não diz o quê. Aqui o número vira
 * trabalho priorizável: quantos elementos, de que gravidade, contra qual
 * critério da WCAG, em que página.
 */
function Acessibilidade({ achados, dias }: {
  achados: Painel["findings"];
  dias: number;
}) {
  if (!achados || achados.total === 0) {
    return (
      <EmptyState icon="dashboard" title="Nenhum achado de acessibilidade no período">
        Publique o JSON do <strong>axe-core</strong> como anexo{" "}
        <code>{'{"kind": "axe"}'}</code> no <code>arbites.json</code> — ou
        declare <code>findings</code> direto no manifesto, se usar outra
        ferramenta. O Arbites lê a regra, a gravidade, o critério da WCAG e a
        página sozinho.
      </EmptyState>
    );
  }
  return (
    <>
      <section className="card">
        <h3>Achados no período</h3>
        <p className="obs-pergunta">
          Quantos elementos violam alguma regra, e o quanto isso andou.
        </p>
        <div className="obs-cartoes">
          <div className="obs-cartao">
            <span className="obs-rotulo">ELEMENTOS COM VIOLAÇÃO</span>
            <strong className="obs-numero">{achados.total}</strong>
            <span className="caption muted">
              {achados.previous_total} no período anterior
            </span>
          </div>
          <div className="obs-cartao">
            <span className="obs-rotulo">VARIAÇÃO</span>
            <strong className="obs-numero">
              {achados.delta_pct === null
                ? "—"
                : `${achados.delta_pct > 0 ? "+" : ""}${achados.delta_pct}%`}
            </strong>
            <span className="caption muted">
              {achados.delta_pct === null
                ? "sem base anterior"
                : achados.delta_pct > 0
                  ? "piorou — violação a mais é sempre pior"
                  : "melhorou"}
            </span>
          </div>
          <div className="obs-cartao">
            <span className="obs-rotulo">CRITÉRIOS WCAG ATINGIDOS</span>
            <strong className="obs-numero">{achados.by_wcag.length}</strong>
            <span className="caption muted">critérios distintos com violação</span>
          </div>
        </div>
      </section>

      <div className="obs-pizzas">
        <Pizza
          titulo="Por gravidade"
          pergunta="O que atacar primeiro."
          fatias={achados.by_impact}
          rotulos={IMPACTOS}
        />
        <Pizza
          titulo="Por categoria"
          pergunta="De que tipo é o achado."
          fatias={achados.by_category}
        />
      </div>

      <section className="card">
        <div className="card-head">
          <h3>Regras mais violadas</h3>
          <span className="spacer" />
          <a
            className="button-link"
            href={api.observabilityExportUrl("findings", dias)}
            download
            title="As regras violadas, para priorizar na planilha"
          >
            CSV
          </a>
        </div>
        <p className="obs-pergunta">
          Onde está a maior parte do trabalho — com o critério da WCAG ao lado,
          que é como a norma cobra.
        </p>
        <div className="table-wrap">
          <table className="dense stack-narrow">
            <thead>
              <tr>
                <th>Regra</th>
                <th>Gravidade</th>
                <th>WCAG</th>
                <th>Elementos</th>
                <th>Execuções</th>
              </tr>
            </thead>
            <tbody>
              {achados.top_rules.map((r) => (
                <tr key={r.rule}>
                  <td data-label="Regra">
                    {r.help_url ? (
                      <a href={r.help_url} target="_blank" rel="noreferrer">
                        {r.rule}
                      </a>
                    ) : (
                      r.rule
                    )}
                    {r.help && <span className="caption muted"> — {r.help}</span>}
                  </td>
                  <td data-label="Gravidade">
                    <span className={`badge obs-impacto-${r.impact}`}>
                      {IMPACTOS[r.impact] ?? r.impact}
                    </span>
                  </td>
                  <td data-label="WCAG" className="mono">
                    {r.wcag ? `${r.wcag}${r.level ? ` (${r.level})` : ""}` : "—"}
                  </td>
                  <td data-label="Elementos">{r.count}</td>
                  <td data-label="Execuções">{r.runs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {achados.top_pages.length > 0 && (
        <section className="card">
          <h3>Páginas com mais violações</h3>
          <p className="obs-pergunta">Por onde começar a varredura manual.</p>
          <ul className="obs-lista-paginas">
            {achados.top_pages.map((p) => (
              <li key={p.page}>
                <span className="mono">{p.page}</span>
                <span className="caption muted">{p.count} elemento(s)</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}

export function Observability({ onError }: { onError: (message: string) => void }) {
  const [dias, setDias] = useState(30);
  const [painel, setPainel] = useState<Painel | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [run, setRun] = useState<CiRun | null>(null);
  const [ingerindo, setIngerindo] = useState(false);
  const [origens, setOrigens] = useState<CiSource[]>([]);
  const [novaOrigem, setNovaOrigem] = useState<CiSource>({ repo: "" });
  const [salvandoOrigem, setSalvandoOrigem] = useState(false);
  const [reprocessando, setReprocessando] = useState(false);
  const [limpando, setLimpando] = useState(false);
  const [exportando, setExportando] = useState<{
    formato: string; fracao: number | null;
  } | null>(null);
  const [previaLimpeza, setPreviaLimpeza] = useState<{
    runs: number; attachments: number; bytes: number;
    oldest: string | null; newest: string | null;
  } | null>(null);
  // Configuração sai do meio do painel e vira aba (change 0176): quem lê o
  // painel todo dia não quer tropeçar no formulário que se preenche uma vez.
  const [aba, setAba] = useState<Aba>("painel");
  const [recorte, setRecorte] = useState<string>("");

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      setPainel(await api.observability(dias));
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setCarregando(false);
    }
  }, [dias, onError]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  useEffect(() => {
    // As origens são o pré-requisito da aba inteira: sem elas "Buscar" não
    // tem de onde puxar, e antes só existiam no arbites.yaml (change 0173).
    api
      .ciSources()
      .then((r) => setOrigens(r.sources))
      .catch(() => setOrigens([]));
  }, []);

  const salvarOrigens = async (proximas: CiSource[]) => {
    setSalvandoOrigem(true);
    try {
      const r = await api.ciSourcesSave(proximas);
      setOrigens(r.sources);
      setNovaOrigem({ repo: "" });
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setSalvandoOrigem(false);
    }
  };

  const reprocessar = async () => {
    // Sem rede: relê os anexos que já estão no disco. O reconhecimento do
    // relatório Cucumber melhorou (change 0189), e rebuscar tudo do GitHub
    // só para reler arquivos locais seriam horas de download.
    setReprocessando(true);
    try {
      const r = await api.ciReprocess();
      await carregar();
      onError(
        r.atualizados.length > 0
          ? `${r.atualizados.length} de ${r.lidos} execução(ões) ganharam dado`
            + " novo a partir dos anexos que já estavam no disco."
          : `${r.lidos} execução(ões) relidas; nada mudou.`,
      );
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setReprocessando(false);
    }
  };

  const exportar = async (formato: "pdf" | "csv" | "md") => {
    setExportando({ formato, fracao: 0 });
    try {
      const { blob, nome } = await api.observabilityBaixar(
        formato, dias, (fracao) => setExportando({ formato, fracao }),
      );
      // O arquivo só chega ao disco depois de pronto: um download que
      // aparece pela metade é pior que um que demora.
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = nome;
      link.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setExportando(null);
    }
  };

  const pedirLimpeza = async () => {
    // A prévia vem ANTES do "tem certeza?": uma confirmação que não diz
    // quantas execuções vão embora não é confirmação, é um obstáculo.
    try {
      setPreviaLimpeza(await api.ciPurgePreview());
    } catch (e) {
      onError((e as Error).message);
    }
  };

  const limparTudo = async () => {
    setLimpando(true);
    try {
      const r = await api.ciPurge();
      setPreviaLimpeza(null);
      await carregar();
      onError(
        `${r.removed.runs} execução(ões) e ${r.removed.attachments} anexo(s)`
        + " foram para a lixeira — de lá dá para restaurar.",
      );
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setLimpando(false);
    }
  };

  const abrirRun = useCallback(
    async (runId: string) => {
      try {
        setRun(await api.ciRun(runId));
      } catch (e) {
        onError((e as Error).message);
      }
    },
    [onError],
  );

  const ingerir = async (refazer = false) => {
    setIngerindo(true);
    try {
      // O período da TELA vira a janela da busca, e só a lacuna dela é
      // varrida (change 0190): trocar 30 por 90 busca os 60 que faltam, não
      // os 90 de novo.
      const r = await api.ciIngest(dias, refazer);
      // "Parado por credencial" NÃO é "não há run novo": os dois parecem
      // iguais (nenhum dado novo) e pedem ações opostas (change 0157).
      if (r.stopped === "tls_untrusted") {
        // Certificado e rede pedem ações opostas — configurar e esperar. A
        // mensagem já vem pronta do backend com as variáveis; repeti-la aqui
        // criaria duas verdades (change 0183).
        onError(r.errors?.[0]?.message ?? "certificado não reconhecido");
      } else if (r.stopped === "bad_credential") {
        onError(
          "a ingestão parou porque o GitHub recusou a credencial — reponha o"
          + " token em Automação → Configurar. O intervalo perdido volta inteiro.",
        );
      } else if (r.errors?.length) {
        onError(r.errors[0].message);
      } else if (r.ingested.length === 0 && (r.reused?.length ?? 0) > 0) {
        // "Nada novo" e "nem olhei" parecem iguais na tela e pedem ações
        // opostas — a mesma lição da change 0157.
        onError(
          `o período já estava coberto; nada foi buscado de novo.`
          + ` Use "Reconferir período" para varrer mesmo assim.`,
        );
      }
      await carregar();
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setIngerindo(false);
    }
  };

  // Esqueleto em vez de uma frase centralizada: ele diz o que vem depois, e
  // quando o dado chega nada salta de posição (change 0193).
  if (carregando && !painel) {
    return (
      <div className="obs">
        <header className="obs-topo">
          <div><h2>Observabilidade</h2></div>
        </header>
        <Esqueleto linhas={6} titulo="Carregando a observabilidade" />
      </div>
    );
  }
  if (!painel) return null;

  const { health: saude } = painel;
  const semDado = saude.runs === 0 && painel.signals.length === 0;

  return (
    <div className="obs">
      <header className="obs-topo">
        <div>
          <h2>Observabilidade</h2>
          <p className="muted">
            O que mudou desde o período anterior — {formatarData(painel.period.since)} a{" "}
            {formatarData(painel.period.until)}, comparado com os {dias} dias
            anteriores.
          </p>
        </div>
        <div className="obs-controles">
          <select
            value={dias}
            aria-label="Período"
            onChange={(e) => setDias(Number(e.target.value))}
          >
            {PERIODOS.map((p) => (
              <option key={p.dias} value={p.dias}>
                {p.rotulo}
              </option>
            ))}
          </select>
          <button type="button" onClick={() => void ingerir()} disabled={ingerindo}>
            {ingerindo ? "Buscando…" : "Buscar execuções"}
          </button>
          {/* Exportar o que está na tela, no período escolhido (change 0174):
              PDF leva os gráficos, CSV leva a série para a planilha, MD entra
              em ata e wiki. São três perguntas diferentes, não três botões
              para a mesma. */}
          {/* Botão em vez de `<a download>` (change 0193): o link não tinha
              como dizer que o arquivo estava sendo gerado, e um clique sem
              resposta visível convida ao segundo clique. */}
          <button
            type="button"
            onClick={() => void exportar("pdf")}
            disabled={exportando !== null}
            title="Painel com os gráficos, para anexar"
          >
            PDF
          </button>
          <button
            type="button"
            onClick={() => void exportar("csv")}
            disabled={exportando !== null}
            title="Série de cada sinal, uma linha por medida"
          >
            CSV
          </button>
          <button
            type="button"
            onClick={() => void exportar("md")}
            disabled={exportando !== null}
            title="O painel em texto, para ata e wiki"
          >
            MD
          </button>
        </div>
        {exportando && (
          <Progresso
            valor={exportando.fracao}
            rotulo={`Gerando o ${exportando.formato.toUpperCase()}…`}
          />
        )}
      </header>

      <TabBar
        tabs={ABAS}
        value={aba}
        onChange={setAba}
        label="Seções da observabilidade"
      />

      {aba === "config" ? (
        <>
          <p className="caption muted obs-config-nota">
            De onde as execuções são puxadas e por quanto tempo ficam. É o que
            se preenche uma vez — por isso saiu do meio do painel.
          </p>
          <section className="card obs-perigo">
            <div className="card-head">
              <h3>Limpar toda a observabilidade</h3>
            </div>
            <p className="caption muted">
              Remove todas as execuções ingeridas, seus anexos e o registro de
              até onde a busca já olhou. Vai para a lixeira, como todo o resto
              do Arbites — de lá dá para restaurar enquanto ela não for
              esvaziada. As origens declaradas ficam: o que some é o dado, não
              a configuração.
            </p>
            <button
              type="button"
              className="danger"
              onClick={() => void pedirLimpeza()}
              disabled={limpando}
            >
              {limpando ? "Limpando…" : "Limpar tudo…"}
            </button>
          </section>
          <section className="card">
            <div className="card-head">
              <h3>Reconferir período</h3>
            </div>
            <p className="caption muted">
              A busca guarda até onde já olhou, por origem, e varre só o que
              falta — trocar 30 por 90 dias busca os 60 que faltam, não os 90
              de novo. Isto ignora esse registro e revarre a janela inteira
              que está selecionada no topo. Não apaga nada: o que já está no
              disco não é baixado de novo.
            </p>
            <button
              type="button"
              onClick={() => void ingerir(true)}
              disabled={ingerindo}
            >
              {ingerindo ? "Reconferindo…" : "Reconferir período"}
            </button>
          </section>
          <section className="card">
            <div className="card-head">
              <h3>Reprocessar do disco</h3>
            </div>
            <p className="caption muted">
              Relê os anexos das execuções que já foram ingeridas e refaz o que
              é derivado deles — cenários e achados. Não usa rede e não busca
              nada: serve para quando o reconhecimento de um formato melhorou e
              as execuções antigas ficaram com o resultado anterior.
            </p>
            <button
              type="button"
              onClick={() => void reprocessar()}
              disabled={reprocessando}
            >
              {reprocessando ? "Relendo…" : "Reprocessar do disco"}
            </button>
          </section>
          <section className="card obs-origens">
            <div className="card-head">
              <h3>Origens</h3>
              <span className="spacer" />
              <span className="caption muted">
                de onde as execuções são puxadas
              </span>
            </div>
            {origens.length === 0 ? (
              <p className="caption muted">
                Nenhuma origem declarada ainda — por isso "Buscar execuções" não
                traz nada. Informe o repositório abaixo; workflow e artifact
                vazios significam "todos".
              </p>
            ) : (
              <ul className="obs-lista-origens">
                {origens.map((o) => (
                  <li key={`${o.repo}/${o.workflow ?? ""}`}>
                    <span className="mono">{o.repo}</span>
                    <span className="caption muted">
                      {o.workflow ? o.workflow : "todos os workflows"}
                      {o.artifact ? ` · ${o.artifact}` : ""}
                    </span>
                    <button
                      type="button"
                      className="btn-sm"
                      disabled={salvandoOrigem}
                      onClick={() =>
                        void salvarOrigens(origens.filter((x) => x !== o))
                      }
                    >
                      Remover
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <div className="field-grid">
              <div className="field col-4">
                <label htmlFor="obs-repo">Repositório</label>
                <input
                  id="obs-repo"
                  className="mono"
                  value={novaOrigem.repo}
                  onChange={(e) =>
                    setNovaOrigem((o) => ({ ...o, repo: e.target.value }))
                  }
                  placeholder="organizacao/repositorio"
                />
              </div>
              <div className="field col-4">
                <label htmlFor="obs-workflow">Workflow (opcional)</label>
                <input
                  id="obs-workflow"
                  className="mono"
                  value={novaOrigem.workflow ?? ""}
                  onChange={(e) =>
                    setNovaOrigem((o) => ({ ...o, workflow: e.target.value }))
                  }
                  placeholder="vazio = todos"
                />
              </div>
              <div className="field col-4">
                <label htmlFor="obs-artifact">Artifact (opcional)</label>
                <input
                  id="obs-artifact"
                  className="mono"
                  value={novaOrigem.artifact ?? ""}
                  onChange={(e) =>
                    setNovaOrigem((o) => ({ ...o, artifact: e.target.value }))
                  }
                  placeholder="vazio = todos"
                />
              </div>
            </div>
            <div className="toolbar">
              <button
                type="button"
                className="primary"
                disabled={!novaOrigem.repo.trim() || salvandoOrigem}
                onClick={() => void salvarOrigens([...origens, novaOrigem])}
              >
                {salvandoOrigem ? "Salvando…" : "Adicionar origem"}
              </button>
            </div>
          </section>
          <Retencao onError={onError} onLimpou={() => void carregar()} />
        </>
      ) : semDado ? (
        <EmptyState
          icon="dashboard"
          title="Nenhuma execução de CI chegou ainda"
          action={{
            label: "Declarar uma origem",
            onClick: () => setAba("config"),
          }}
        >
          Esta área vive do que a sua automação já produz. Declare a origem na
          aba <strong>Configuração</strong> e publique um{" "}
          <code>arbites.json</code> junto do artifact do workflow — sinais,
          achados de acessibilidade, prints, logs e a análise em Markdown
          entram sozinhos a partir daí.
        </EmptyState>
      ) : aba === "evidencias" ? (
        <Evidencias
          dias={dias}
          origens={painel.by_origin.map((o) => o.name)}
          onError={onError}
          onAbrirRun={(id) => {
            setAba("painel");
            void abrirRun(id);
          }}
        />
      ) : aba === "analise" ? (
        <Analise dias={dias} onError={onError} />
      ) : aba === "acessibilidade" ? (
        <Acessibilidade achados={painel.findings} dias={dias} />
      ) : (
        <>
          {/* PERGUNTA: o que mudou sozinho desde o período anterior?
              É o bloco que justifica a aba existir — a diferença calculada e
              dita em uma frase, em vez de caçada a olho num mural. */}
          <section className="card obs-mudancas">
            <h3>O que mudou</h3>
            <p className="obs-pergunta">
              O que se moveu sozinho desde o período anterior.
            </p>
            {painel.changes.length === 0 ? (
              <p className="muted">
                Nada se moveu o bastante para merecer atenção neste período.
              </p>
            ) : (
              <ul className="obs-lista-mudancas">
                {painel.changes.map((mudanca, i) => (
                  <li key={i} className={`obs-mudanca obs-mudanca-${mudanca.kind}`}>
                    <span>{mudanca.text}</span>
                    {mudanca.run_id && (
                      <button
                        type="button"
                        className="link-btn"
                        onClick={() => void abrirRun(mudanca.run_id as string)}
                      >
                        abrir a execução
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* PERGUNTA: em que teste eu não posso mais confiar?
              Instabilidade não aparece em média nenhuma — um teste que passa,
              falha e passa de novo some numa taxa de sucesso e continua
              corroendo a confiança na suíte. */}
          {painel.flaky.length > 0 && (
            <section className="card obs-instaveis">
              <h3>Testes instáveis</h3>
              <p className="obs-pergunta">
                Cenários que passaram <em>e</em> falharam neste período. Os
                marcados como <strong>novos</strong> estavam estáveis antes.
              </p>
              <div className="scroll-x">
                <table className="table stack-narrow">
                  <thead>
                    <tr>
                      <th>Cenário</th>
                      <th>Caso</th>
                      <th>Execuções</th>
                      <th>Falhas</th>
                      <th>Viradas</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {[...painel.flaky]
                      .sort((a, b) => Number(b.newly_flaky) - Number(a.newly_flaky))
                      .map((f: CiFlaky) => (
                        <tr key={f.scenario}>
                          <td data-label="Cenário">
                            {f.scenario}
                            {f.newly_flaky && (
                              <span className="badge obs-badge-novo">novo</span>
                            )}
                          </td>
                          <td data-label="Caso" className="mono">
                            {f.testcase_id ?? "—"}
                          </td>
                          <td data-label="Execuções">{f.runs}</td>
                          <td data-label="Falhas">{f.failures}</td>
                          <td data-label="Viradas">{f.flips}</td>
                          <td data-label="">
                            {f.last_run && (
                              <button
                                type="button"
                                className="link-btn"
                                onClick={() => void abrirRun(f.last_run as string)}
                              >
                                última execução
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* PERGUNTA: a automação está rodando, e está passando? */}
          <section className="obs-saude">
            <div className="card obs-cartao">
              <span className="obs-rotulo">Execuções no período</span>
              <strong className="obs-numero">{saude.runs}</strong>
              <span className="muted">
                {saude.runs_previous} no período anterior
              </span>
            </div>
            <div className="card obs-cartao">
              <span className="obs-rotulo">Taxa de sucesso</span>
              <strong className="obs-numero">
                {saude.success_rate === null ? "—" : `${saude.success_rate}%`}
              </strong>
              <span className="muted">
                {/* O denominador junto do número: cancelada e skipped saíram
                    da conta (change 0191), e uma taxa que não fecha com o
                    card ao lado sem explicação parece defeito. */}
                {`de ${saude.conclusive_runs} conclusiva${
                  saude.conclusive_runs === 1 ? "" : "s"
                }`}
                {saude.inconclusive_runs > 0 &&
                  ` · ${saude.inconclusive_runs} fora da conta`}
                {saude.success_rate_previous !== null &&
                  ` · ${saude.success_rate_previous}% antes`}
                {saude.goal !== null && ` · meta ${saude.goal}%`}
              </span>
            </div>
            <div className="card obs-cartao">
              <span className="obs-rotulo">Última execução</span>
              <strong className="obs-numero">{formatarData(saude.last_run_at)}</strong>
              <span className="muted">
                {saude.days_since_last_run === null
                  ? "—"
                  : `há ${saude.days_since_last_run} ${
                      saude.days_since_last_run === 1 ? "dia" : "dias"
                    }`}
              </span>
            </div>
          </section>

          {/* PERGUNTA: de que é feito o período? Série responde "está
              piorando"; divisão responde "de que é feito" — e nenhuma
              substitui a outra (change 0176). */}
          <div className="obs-pizzas">
            <Pizza
              titulo="Execuções por resultado"
              pergunta="Quanto do período foi verde, entre as que deram veredito."
              fatias={painel.distribution.runs_by_conclusion}
              rotulos={CONCLUSOES}
              rodape={
                painel.distribution.inconclusive_total > 0
                  ? `${painel.distribution.inconclusive_total} fora da conta: `
                    + painel.distribution.runs_inconclusive
                        .map((f) => `${f.value} ${CONCLUSOES[f.label] ?? f.label}`)
                        .join(", ")
                    + " — não chegaram a um veredito sobre o produto."
                  : undefined
              }
            />
            <Pizza
              titulo="Cenários por resultado"
              pergunta="Onde a falha se concentra — run inteiro ou cenário solto."
              fatias={painel.distribution.scenarios_by_status}
              rotulos={STATUS_CENARIO}
            />
          </div>

          {/* PERGUNTA: qual PRODUTO está quebrando? Três repositórios
              diferentes no mesmo evento — onde o teste mora, onde a aplicação
              mora e quem disparou. A pergunta é sobre o segundo (0178). */}
          {painel.by_origin.length > 0 && (
            <>
              <div className="obs-pizzas">
                <Pizza
                  titulo="Erros por repositório de origem"
                  pergunta="De quem são as falhas do período — o volume, não a taxa."
                  fatias={painel.errors_by_origin}
                  vazio="nenhuma falha no período"
                />
                <div className="obs-pizza obs-nota-origem">
                  <h4>Por que dois recortes</h4>
                  <p className="caption muted">
                    O repositório de <strong>teste</strong> é onde a suíte
                    mora; o de <strong>origem</strong> é a aplicação cujo
                    deploy mandou rodar. Um repositório de teste serve vários
                    produtos, então só o segundo responde “qual produto está
                    quebrando”.
                  </p>
                  <p className="caption muted">
                    A origem vem do bloco <code>trigger</code> no{" "}
                    <code>arbites.json</code>, ou do rótulo{" "}
                    <code>repo_origem</code>.
                  </p>
                </div>
              </div>
              <Recorte
                titulo="Repositório de origem"
                pergunta="A aplicação cujo deploy disparou a suíte, pior primeiro."
                itens={painel.by_origin}
              />
            </>
          )}

          {/* PERGUNTA: qual repositório/componente está pior? Média global
              não é a saúde de nada quando são vários micro-frontends. */}
          <Recorte
            titulo="Repositório de teste"
            pergunta="Cada repositório de teste que alimenta esta aba, pior primeiro."
            itens={painel.by_repo}
          />
          {painel.label_names.length > 0 && (
            <section className="card obs-recortes">
              <div className="card-head">
                <h3>Por rótulo</h3>
                <span className="spacer" />
                <span className="caption muted">
                  declarado em <code>labels</code> no manifesto
                </span>
              </div>
              <p className="obs-pergunta">
                O repositório do workflow não é o que está sob teste: num
                projeto de micro-frontends o recorte que importa é o
                componente, o ambiente, a camada.
              </p>
              <TabBar
                tabs={painel.label_names.map((n) => [n, n] as const)}
                value={recorte || painel.label_names[0]}
                onChange={setRecorte}
                label="Rótulos declarados"
              />
              <Recorte
                titulo={recorte || painel.label_names[0]}
                pergunta=""
                itens={painel.by_label[recorte || painel.label_names[0]] ?? []}
              />
            </section>
          )}

          {/* PERGUNTA: alguma medida regrediu, e em qual execução? */}
          <section className="card obs-sinais">
            <h3>Sinais no tempo</h3>
            <p className="obs-pergunta">
              Como cada medida se moveu — clique num ponto para abrir a execução
              que o produziu.
            </p>
            {painel.signals.length === 0 ? (
              <EmptyState compact icon="dashboard" title="Nenhuma série ainda">
                Nenhuma execução foi ingerida neste período — sem execução não
                há o que medir. Depois de buscar, o Arbites calcula sozinho
                duração, resultado, cenários e acessibilidade; para métrica
                própria do seu pipeline, declare os sinais no{" "}
                <code>arbites.json</code> do artifact.
              </EmptyState>
            ) : (
              <div className="obs-grade-sinais">
                {painel.signals.map((sinal) => (
                  <article key={sinal.name} className="obs-sinal">
                    <header>
                      <span className="obs-sinal-nome">
                        {NOME_DO_SINAL[sinal.name] ?? sinal.name}
                        {sinal.source === "derivado" ? (
                          <span
                            className="obs-sinal-kind"
                            title={
                              "calculado pelo Arbites a partir da própria"
                              + " execução — o pipeline não mediu isto"
                            }
                          >
                            derivado
                          </span>
                        ) : (
                          <span className="obs-sinal-kind">{sinal.kind}</span>
                        )}
                      </span>
                      <strong>{formatarValor(sinal.current, sinal.unit)}</strong>
                    </header>
                    <Variacao sinal={sinal} />
                    <Serie
                      sinal={sinal}
                      onPonto={(id) => void abrirRun(id)}
                      selecionado={run?.id ?? null}
                    />
                    {sinal.goal !== null && (
                      <p className="obs-meta">
                        meta {formatarValor(sinal.goal, sinal.unit)}
                        {sinal.direction === "lower"
                          ? " (quanto menor, melhor)"
                          : sinal.direction === "higher"
                            ? " (quanto maior, melhor)"
                            : ""}
                      </p>
                    )}
                  </article>
                ))}
              </div>
            )}
          </section>

          {run && <Descida run={run} onFechar={() => setRun(null)} />}

          {/* PERGUNTA: por onde começo a olhar? */}
          <section className="card obs-runs">
            <h3>Execuções recentes</h3>
            <p className="obs-pergunta">A lista por onde se começa a olhar.</p>
            <div className="scroll-x">
              <table className="table stack-narrow">
                <thead>
                  <tr>
                    <th>Quando</th>
                    <th>Workflow</th>
                    <th>Gatilho</th>
                    <th>Resultado</th>
                    <th>Sinais</th>
                    <th>Anexos</th>
                  </tr>
                </thead>
                <tbody>
                  {painel.runs.map((item) => (
                    <tr
                      key={item.id}
                      className={run?.id === item.id ? "obs-linha-ativa" : ""}
                      onClick={() => void abrirRun(item.id)}
                    >
                      <td data-label="Quando">{formatarData(item.started_at)}</td>
                      <td data-label="Workflow">{item.workflow}</td>
                      <td data-label="Gatilho">{item.event ?? "—"}</td>
                      <td data-label="Resultado">
                        <span
                          className={`badge ${
                            item.conclusion === "success"
                              ? "obs-badge-ok"
                              : "obs-badge-falha"
                          }`}
                        >
                          {item.conclusion ?? "—"}
                        </span>
                      </td>
                      <td data-label="Sinais">{item.signals.length}</td>
                      <td data-label="Anexos">{item.attachments.length}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

        </>
      )}

      {previaLimpeza && (
        <ConfirmModal
          danger
          title="Limpar toda a observabilidade"
          message={
            <>
              Isto remove <strong>{previaLimpeza.runs}</strong> execução(ões) e{" "}
              <strong>{previaLimpeza.attachments}</strong> anexo(s)
              {previaLimpeza.bytes > 0 &&
                ` (${(previaLimpeza.bytes / 1024 / 1024).toFixed(1)} MB)`}
              {previaLimpeza.oldest && previaLimpeza.newest && (
                <>
                  {" "}— de {formatarData(previaLimpeza.oldest)} a{" "}
                  {formatarData(previaLimpeza.newest)}
                </>
              )}
              {" "}A série temporal inteira some da tela.
              <br />
              <br />
              Tudo vai para a <strong>lixeira</strong>, não para o apagador: de
              lá dá para restaurar enquanto ela não for esvaziada. As origens
              declaradas continuam onde estão.
            </>
          }
          confirmLabel={`Limpar ${previaLimpeza.runs} execução(ões)`}
          onConfirm={() => void limparTudo()}
          onCancel={() => setPreviaLimpeza(null)}
        />
      )}
    </div>
  );
}
