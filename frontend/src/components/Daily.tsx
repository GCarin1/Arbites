import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { DocBody } from "./ReadView";
import type { DailyContext, DailyDigestResult } from "../types";

const today = () => new Date().toISOString().slice(0, 10);

function digestToText(d: DailyDigestResult): string {
  const imp = d.impediments.length ? d.impediments.map((i) => `- ${i}`).join("\n") : "- nenhum";
  const acts = d.action_items.length ? d.action_items.map((a) => `- ${a}`).join("\n") : "- —";
  return (
    `## Resumo\n${d.summary}\n\n## Impedimentos\n${imp}\n\n` +
    `## Andamento\n${d.progress}\n\n## Action items\n${acts}\n`
  );
}

export function Daily({ onError }: { onError: (message: string) => void }) {
  const [day, setDay] = useState(today());
  const [context, setContext] = useState<DailyContext | null>(null);
  const [body, setBody] = useState("");
  const [actionItems, setActionItems] = useState<string[]>([]);
  const [accepted, setAccepted] = useState<Set<string>>(new Set());
  const [dailies, setDailies] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);

  const loadDailies = useCallback(() => {
    api.dailies().then((r) => setDailies(r.dailies)).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setAccepted(new Set());
    try {
      const [ctx, existing] = await Promise.all([
        api.dailyContext(day),
        api.getDaily(day).catch(() => null),
      ]);
      setContext(ctx);
      setBody(existing?.body ?? "");
      setActionItems(existing?.action_items ?? []);
      setSaved(!!existing);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }, [day, onError]);

  useEffect(() => {
    void load();
  }, [load]);
  useEffect(() => {
    loadDailies();
  }, [loadDailies]);

  async function snapshot() {
    try {
      await api.metricsSnapshot();
      await load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function generate() {
    setBusy(true);
    try {
      const d = await api.generateDaily(day);
      setBody(digestToText(d));
      setActionItems(d.action_items);
      setAccepted(new Set());
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function save() {
    setBusy(true);
    try {
      await api.putDaily(day, { body, action_items: actionItems });
      setSaved(true);
      loadDailies();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function acceptItem(item: string) {
    try {
      await api.createTodo({ title: item });
      setAccepted((old) => new Set(old).add(item));
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  const diff = context?.metrics_diff;

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Daily</h1>
        <span className="spacer" />
        <div className="head-controls">
          <input type="date" value={day} onChange={(e) => setDay(e.target.value)} />
          <button onClick={() => void snapshot()}>Snapshot de métricas</button>
          <button className="primary" onClick={() => void generate()} disabled={busy}>
            {busy ? "Gerando…" : "Gerar com IA"}
          </button>
        </div>
      </div>

      {dailies.length > 0 && (
        <div className="daily-history">
          <span className="caption">Dailies salvas:</span>
          {dailies.map((d) => (
            <button
              key={d}
              className={`link-chip mono ${d === day ? "chip-active" : ""}`}
              onClick={() => setDay(d)}
            >
              {d}
            </button>
          ))}
        </div>
      )}

      <div className="daily-grid">
        <div>
          <h3 className="section-title">
            Texto da daily {saved && <span className="status-dot dot-active">salva</span>}
          </h3>
          <textarea
            className="raw"
            style={{ minHeight: 280 }}
            value={body}
            onChange={(e) => {
              setBody(e.target.value);
              setSaved(false);
            }}
            placeholder="Gere com IA ou escreva à mão. O contexto do dia está ao lado."
            spellCheck={false}
          />
          <div className="toolbar">
            <button className="primary" onClick={() => void save()} disabled={busy || !body.trim()}>
              Salvar daily
            </button>
          </div>

          {actionItems.length > 0 && (
            <div className="card">
              <div className="card-head">
                <h3>Action items</h3>
                <span className="spacer" />
                <span className="caption">aceitar cria um afazer</span>
              </div>
              {actionItems.map((item, i) => (
                <div key={i} className="step-row">
                  <span style={{ flex: 1 }}>{item}</span>
                  {accepted.has(item) ? (
                    <span className="status-dot dot-active">virou todo</span>
                  ) : (
                    <button className="btn-sm" onClick={() => void acceptItem(item)}>
                      Criar afazer
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <h3 className="section-title">Contexto do dia</h3>
          {diff && (
            <div className="table-wrap" style={{ marginBottom: 16 }}>
              <table className="dense">
                <thead>
                  <tr>
                    <th>Métrica</th>
                    <th>Hoje</th>
                    <th>Anterior</th>
                    <th>Δ</th>
                  </tr>
                </thead>
                <tbody>
                  {diff.metrics.map((m) => (
                    <tr key={m.metric}>
                      <td>{m.label}</td>
                      <td className="mono">{fmt(m.today)}</td>
                      <td className="mono muted">{fmt(m.previous)}</td>
                      <td className="mono">{m.delta === null ? "—" : `${m.delta >= 0 ? "+" : ""}${Math.round(m.delta * 100)} p.p.`}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {context && <DocBody text={context.markdown} />}
        </div>
      </div>
    </div>
  );
}

function fmt(v: number | null): string {
  return v === null ? "—" : `${Math.round(v * 100)}%`;
}
