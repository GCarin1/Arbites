import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { ActivityDay, ActivityHeatmapData } from "../types";

type Metric = "total" | "executions" | "defects" | "testcases" | "requirements" | "auto_runs";

const METRICS: { key: Metric; label: string }[] = [
  { key: "total", label: "Toda atividade" },
  { key: "executions", label: "Casos executados" },
  { key: "defects", label: "Bugs encontrados" },
  { key: "testcases", label: "CTs criados" },
  { key: "requirements", label: "Requisitos criados" },
  { key: "auto_runs", label: "Runs de automação" },
];

const WEEKDAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
const MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

function toDate(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function iso(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate(),
  ).padStart(2, "0")}`;
}

function ptDate(isoStr: string): string {
  const [y, m, d] = isoStr.split("-");
  return `${d}/${m}/${y}`;
}

/** Nível de cor 0–4 a partir do valor vs. o máximo do período (estilo GitHub). */
function level(value: number, max: number): number {
  if (value <= 0 || max <= 0) return 0;
  const q = value / max;
  if (q > 0.66) return 4;
  if (q > 0.33) return 3;
  if (q > 0.1) return 2;
  return 1;
}

const EMPTY_DAY: ActivityDay = {
  date: "",
  executions: 0,
  defects: 0,
  testcases: 0,
  requirements: 0,
  auto_runs: 0,
  total: 0,
};

type Hover = { day: ActivityDay; x: number; y: number } | null;

export function ActivityHeatmap({ onError }: { onError: (message: string) => void }) {
  const [data, setData] = useState<ActivityHeatmapData | null>(null);
  const [metric, setMetric] = useState<Metric>("total");
  const [year, setYear] = useState(0); // 0 = últimos 12 meses
  const [hover, setHover] = useState<Hover>(null);

  useEffect(() => {
    api
      .metricsActivity(371, year)
      .then(setData)
      .catch((e) => onError(e instanceof Error ? e.message : String(e)));
  }, [year, onError]);

  const { weeks, byDate, max, monthLabels } = useMemo(() => {
    if (!data) {
      return {
        weeks: [] as string[][],
        byDate: new Map<string, ActivityDay>(),
        max: 0,
        monthLabels: [] as { col: number; label: string }[],
      };
    }
    const map = new Map<string, ActivityDay>();
    for (const d of data.days) map.set(d.date, d);

    const cells: string[] = [];
    const end = toDate(data.to);
    for (let d = toDate(data.from); d <= end; d.setDate(d.getDate() + 1)) cells.push(iso(d));
    const cols: string[][] = [];
    for (let i = 0; i < cells.length; i += 7) cols.push(cells.slice(i, i + 7));

    const labels: { col: number; label: string }[] = [];
    let lastMonth = -1;
    cols.forEach((week, ci) => {
      const first = week[0] && toDate(week[0]);
      if (first && first.getMonth() !== lastMonth) {
        lastMonth = first.getMonth();
        labels.push({ col: ci, label: MONTHS[first.getMonth()] });
      }
    });

    const m = Math.max(0, ...data.days.map((d) => d[metric]));
    return { weeks: cols, byDate: map, max: m, monthLabels: labels };
  }, [data, metric]);

  if (!data) return null;
  const metricLabel = METRICS.find((m) => m.key === metric)?.label ?? "";
  const total = data.totals?.[metric] ?? 0;
  const years = data.years ?? []; // resiliente a resposta antiga/parcial do backend

  return (
    <div className="card" style={{ marginBottom: 24, position: "relative" }}>
      <div className="card-head">
        <h3>Atividade</h3>
        <span className="spacer" style={{ flex: 1 }} />
        <select value={year} onChange={(e) => setYear(Number(e.target.value))}>
          <option value={0}>Últimos 12 meses</option>
          {[...years].reverse().map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        <select value={metric} onChange={(e) => setMetric(e.target.value as Metric)}>
          {METRICS.map((m) => (
            <option key={m.key} value={m.key}>
              {m.label}
            </option>
          ))}
        </select>
      </div>
      <p className="caption muted" style={{ marginBottom: 12 }}>
        {total} no período · {metricLabel.toLowerCase()}
      </p>

      <div className="heatmap">
        <div className="heatmap-weekdays">
          {WEEKDAYS.map((w, i) => (
            <span key={w} className="heatmap-weekday">
              {i % 2 === 0 ? w : ""}
            </span>
          ))}
        </div>
        <div className="heatmap-main">
          <div className="heatmap-months">
            {weeks.map((_, ci) => {
              const label = monthLabels.find((m) => m.col === ci)?.label ?? "";
              return (
                <span key={ci} className="heatmap-month">
                  {label}
                </span>
              );
            })}
          </div>
          <div className="heatmap-grid">
            {weeks.map((week, ci) => (
              <div key={ci} className="heatmap-col">
                {Array.from({ length: 7 }).map((_, ri) => {
                  const day = week[ri];
                  if (!day) return <span key={ri} className="heatmap-cell heatmap-empty" />;
                  const entry = byDate.get(day) ?? { ...EMPTY_DAY, date: day };
                  const value = entry[metric];
                  return (
                    <span
                      key={day}
                      className={`heatmap-cell heat-${level(value, max)}`}
                      onMouseEnter={(e) =>
                        setHover({ day: entry, x: e.clientX, y: e.clientY })
                      }
                      onMouseMove={(e) =>
                        setHover({ day: entry, x: e.clientX, y: e.clientY })
                      }
                      onMouseLeave={() => setHover(null)}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="heatmap-legend caption muted">
        <span>menos</span>
        {[0, 1, 2, 3, 4].map((l) => (
          <span key={l} className={`heatmap-cell heat-${l}`} />
        ))}
        <span>mais</span>
      </div>

      {hover && (
        <div
          className="heatmap-tip"
          style={{ left: hover.x, top: hover.y }}
          role="tooltip"
        >
          <div className="heatmap-tip-title">
            <strong>{hover.day.total}</strong> mudança{hover.day.total === 1 ? "" : "s"} em{" "}
            {ptDate(hover.day.date)}
          </div>
          {hover.day.total > 0 && (
            <div className="heatmap-tip-breakdown caption">
              {hover.day.executions > 0 && <span>{hover.day.executions} exec.</span>}
              {hover.day.defects > 0 && <span>{hover.day.defects} bugs</span>}
              {hover.day.testcases > 0 && <span>{hover.day.testcases} CTs</span>}
              {hover.day.requirements > 0 && <span>{hover.day.requirements} req.</span>}
              {hover.day.auto_runs > 0 && <span>{hover.day.auto_runs} auto</span>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
