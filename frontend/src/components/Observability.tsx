import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { EmptyState } from "./EmptyState";
import { DocBody } from "./ReadView";
import type { CiRun, CiSignalSeries, Observability as Painel } from "../types";

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

function formatarData(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? "—"
    : d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
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
    <div className="obs-serie">
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

export function Observability({ onError }: { onError: (message: string) => void }) {
  const [dias, setDias] = useState(30);
  const [painel, setPainel] = useState<Painel | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [run, setRun] = useState<CiRun | null>(null);
  const [ingerindo, setIngerindo] = useState(false);

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

  const ingerir = async () => {
    setIngerindo(true);
    try {
      const r = await api.ciIngest();
      if (r.errors?.length) onError(r.errors[0].message);
      await carregar();
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setIngerindo(false);
    }
  };

  if (carregando && !painel) return <p className="empty">Carregando observabilidade…</p>;
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
        </div>
      </header>

      {semDado ? (
        <EmptyState
          icon="dashboard"
          title="Nenhuma execução de CI chegou ainda"
          action={{ label: ingerindo ? "Buscando…" : "Buscar agora", onClick: () => void ingerir() }}
        >
          Esta área vive do que a sua automação já produz. Declare a origem em{" "}
          <code>observability.sources</code> no <code>arbites.yaml</code> e publique
          um <code>arbites.json</code> junto do artifact do workflow — os sinais,
          prints, logs e a análise em Markdown entram sozinhos a partir daí.
        </EmptyState>
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
                {saude.success_rate_previous === null
                  ? "sem base anterior"
                  : `${saude.success_rate_previous}% antes`}
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

          {/* PERGUNTA: alguma medida regrediu, e em qual execução? */}
          <section className="card obs-sinais">
            <h3>Sinais no tempo</h3>
            <p className="obs-pergunta">
              Como cada medida se moveu — clique num ponto para abrir a execução
              que o produziu.
            </p>
            {painel.signals.length === 0 ? (
              <EmptyState
                compact
                icon="dashboard"
                title="Nenhum sinal declarado"
              >
                As execuções chegaram, mas sem <code>arbites.json</code> nenhuma
                medida foi extraída. Declare os sinais no manifesto do artifact
                para a série começar.
              </EmptyState>
            ) : (
              <div className="obs-grade-sinais">
                {painel.signals.map((sinal) => (
                  <article key={sinal.name} className="obs-sinal">
                    <header>
                      <span className="obs-sinal-nome">
                        {sinal.name}
                        <span className="obs-sinal-kind">{sinal.kind}</span>
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
    </div>
  );
}
