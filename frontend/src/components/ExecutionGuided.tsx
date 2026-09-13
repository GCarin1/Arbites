import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { ResultPanel } from "./Executions";
import type { Execution, ExecutionSummary, ResultEntry } from "../types";

/**
 * Modo guiado: sentar e executar.
 *
 * O Kanban é bom para arrastar e ver o todo, e ruim para o que o QA faz na
 * maior parte do tempo — executar vinte casos em sequência. Ali cada caso
 * custa abrir o modal, marcar, fechar, procurar o próximo: cinco gestos de
 * navegação para um de trabalho.
 *
 * Aqui são três painéis lado a lado — ciclos, casos do ciclo, caso ativo —
 * e um rodapé que dá o resultado e avança num gesto só. Nenhum endpoint
 * novo: é outra leitura da mesma execution que o Kanban lê e escreve.
 */

const RESULT_ACTIONS = [
  { status: "passed", label: "Passou", className: "primary" },
  { status: "failed", label: "Falhou", className: "danger" },
  { status: "blocked", label: "Bloqueado", className: "" },
];

/** Casos ainda sem resultado final — a fila que o modo guiado percorre. */
function isPending(result: ResultEntry): boolean {
  return ["pending", "in_progress"].includes(result.column || result.status);
}

export function ExecutionGuided({
  initialId,
  onError,
  onChanged,
}: {
  initialId: string | null;
  onError: (message: string) => void;
  onChanged: () => void;
}) {
  const [cycles, setCycles] = useState<ExecutionSummary[]>([]);
  const [cycleId, setCycleId] = useState<string | null>(initialId);
  const [execution, setExecution] = useState<Execution | null>(null);
  const [activeCt, setActiveCt] = useState<string | null>(null);
  const [titleOf, setTitleOf] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .executions()
      .then((list) => {
        setCycles(list);
        // sem ciclo escolhido, abre o mais recente que ainda está aberto
        setCycleId((current) =>
          current ?? (list.find((c) => c.status !== "closed") ?? list[0])?.id ?? null,
        );
      })
      .catch((e) => onError(e instanceof Error ? e.message : String(e)));
  }, [onError]);

  const loadCycle = useCallback(
    (id: string) =>
      api
        .execution(id)
        .then((exec) => {
          setExecution(exec);
          setActiveCt((current) => {
            const stillThere = exec.results.some((r) => r.testcase_id === current);
            if (stillThere) return current;
            return (exec.results.find(isPending) ?? exec.results[0])?.testcase_id ?? null;
          });
        })
        .catch((e) => onError(e instanceof Error ? e.message : String(e))),
    [onError],
  );

  useEffect(() => {
    if (cycleId) void loadCycle(cycleId);
  }, [cycleId, loadCycle]);

  // Títulos dos CTs: o id sozinho não diz o que se está testando. UMA
  // leitura da lista, como o Kanban faz — pedir caso a caso faria o número
  // de requisições crescer com o tamanho do ciclo, e o modo guiado existe
  // justamente para a regressão grande.
  useEffect(() => {
    let alive = true;
    api
      .testcases()
      .then((tcs) => {
        if (alive) setTitleOf(Object.fromEntries(tcs.map((t) => [t.id, t.title])));
      })
      .catch(() => {
        // sem título o modo guiado ainda funciona: o id identifica o caso
      });
    return () => {
      alive = false;
    };
  }, []);

  const results = execution?.results ?? [];
  const active = results.find((r) => r.testcase_id === activeCt) ?? null;
  const position = active ? results.indexOf(active) + 1 : 0;
  const closed = execution?.status === "closed";
  const remaining = useMemo(() => results.filter(isPending).length, [results]);

  /** Próximo caso ainda pendente DEPOIS do atual; null quando a fila acabou. */
  function nextPending(from: ResultEntry | null, exec: Execution): string | null {
    const list = exec.results;
    const start = from ? list.findIndex((r) => r.testcase_id === from.testcase_id) + 1 : 0;
    const ahead = list.slice(start).find(isPending);
    return ahead?.testcase_id ?? null;
  }

  async function resolveAndAdvance(status: string) {
    if (!execution || !active || closed) return;
    setSaving(true);
    try {
      const updated = await api.resultStatus(execution.id, active.testcase_id, {
        status,
        column: status,
      });
      setExecution(updated);
      onChanged();
      // para no último em vez de voltar ao começo: dar a volta faria o QA
      // revisitar o que acabou de fechar sem perceber
      const ahead = nextPending(active, updated);
      if (ahead) setActiveCt(ahead);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  function step(delta: number) {
    if (!active) return;
    const index = results.indexOf(active) + delta;
    if (index >= 0 && index < results.length) setActiveCt(results[index].testcase_id);
  }

  return (
    <div className="guided">
      <aside className="guided-cycles">
        <div className="guided-panel-title caption">Ciclos</div>
        {cycles.length === 0 && <p className="empty caption">Nenhum ciclo ainda.</p>}
        {cycles.map((cycle) => (
          <button
            key={cycle.id}
            className={`guided-cycle ${cycle.id === cycleId ? "active" : ""}`}
            onClick={() => setCycleId(cycle.id)}
          >
            <span className="mono caption">{cycle.id}</span>
            <span className="guided-cycle-name">{cycle.name}</span>
            <span className="caption muted">
              {cycle.status === "closed" ? "fechado" : cycle.sprint ?? "—"}
            </span>
          </button>
        ))}
      </aside>

      <section className="guided-cases">
        <div className="guided-panel-title caption">
          Casos {execution ? `· ${remaining} por executar` : ""}
        </div>
        {results.map((result) => (
          <button
            key={result.testcase_id}
            className={`guided-case ${
              result.testcase_id === activeCt ? "active" : ""
            } ${isPending(result) ? "" : "done"}`}
            onClick={() => setActiveCt(result.testcase_id)}
          >
            <span
              className={`status-dot dot-col-${result.column || result.status}`}
              aria-label={result.column || result.status}
            />
            <span className="mono caption">{result.testcase_id}</span>
            <span className="guided-case-title">{titleOf[result.testcase_id] ?? ""}</span>
          </button>
        ))}
      </section>

      <section className="guided-active">
        {!execution || !active ? (
          <p className="empty">Escolha um ciclo com casos para começar.</p>
        ) : (
          <>
            <div className="guided-active-head">
              <h2>
                <span className="mono muted">{active.testcase_id}</span>
                <span>{titleOf[active.testcase_id] ?? ""}</span>
              </h2>
              <span className={`status-dot dot-col-${active.column || active.status}`}>
                {active.column || active.status}
              </span>
            </div>

            {/* o mesmo painel do Kanban, sem o modal em volta */}
            <ResultPanel
              execution={execution}
              result={active}
              closed={closed}
              onUpdate={(updated) => {
                setExecution(updated);
                onChanged();
              }}
              onError={onError}
            />

            <div className="guided-footer">
              <button onClick={() => step(-1)} disabled={position <= 1}>
                ← Anterior
              </button>
              <span className="caption muted">
                {position} de {results.length}
              </span>
              <button
                onClick={() => step(1)}
                disabled={position >= results.length}
              >
                Próximo →
              </button>
              <span className="spacer" />
              {closed ? (
                <span className="caption muted">
                  ciclo fechado — percorrível, não gravável
                </span>
              ) : (
                RESULT_ACTIONS.map((action) => (
                  <button
                    key={action.status}
                    className={action.className}
                    disabled={saving}
                    onClick={() => void resolveAndAdvance(action.status)}
                    title={`${action.label} e ir para o próximo pendente`}
                  >
                    {action.label} e avançar
                  </button>
                ))
              )}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
