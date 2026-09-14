import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { EmptyState } from "./EmptyState";
import { ConfirmModal } from "./Modal";
import { useToast } from "./Toast";
import type { Todo, TodoList, TodoListItem } from "../types";

/**
 * Listas de To Do (change 0164).
 *
 * A divisão em relação ao afazer é o desenho todo: o **afazer** é a nota
 * adesiva — uma coisa a fazer, com prazo, status e cor. A **lista** é o
 * roteiro: passos que só fazem sentido juntos, com prazo DA LISTA.
 *
 * A linha não tem prazo próprio, e é isso que dá sentido ao vínculo: quando
 * uma linha precisa de prazo, de status e de aparecer no sino, ela se liga a
 * um afazer. O afazer traz a data; a linha traz o passo.
 */

const STATUS_DOT: Record<string, string> = {
  open: "dot-col-pending",
  doing: "dot-col-in_progress",
  blocked: "dot-col-blocked",
  done: "dot-col-passed",
};

function prazoClasse(due: string | null, hoje: string, aberta: boolean): string {
  if (!due || !aberta) return "muted";
  if (due < hoje) return "overdue";
  return due === hoje ? "vence-hoje" : "muted";
}

export function TodoLists({
  onError,
  onNavigate,
}: {
  onError: (message: string) => void;
  onNavigate: (id: string) => void;
}) {
  const [listas, setListas] = useState<TodoList[]>([]);
  const [afazeres, setAfazeres] = useState<Todo[]>([]);
  const [criando, setCriando] = useState(false);
  const [titulo, setTitulo] = useState("");
  const [prazo, setPrazo] = useState("");
  const [excluindo, setExcluindo] = useState<TodoList | null>(null);
  const { toast } = useToast();
  const hoje = new Date().toISOString().slice(0, 10);

  const carregar = useCallback(async () => {
    try {
      const [ls, ts] = await Promise.all([api.todoLists(), api.todos()]);
      setListas(ls);
      setAfazeres(ts);
    } catch (e) {
      onError((e as Error).message);
    }
  }, [onError]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const trocar = (atualizada: TodoList) =>
    setListas((antes) => antes.map((l) => (l.id === atualizada.id ? atualizada : l)));

  const acao = async (fn: () => Promise<TodoList>) => {
    try {
      trocar(await fn());
    } catch (e) {
      onError((e as Error).message);
      void carregar();
    }
  };

  async function criar() {
    if (!titulo.trim()) return;
    try {
      await api.createTodoList(titulo.trim(), prazo || null);
      setTitulo("");
      setPrazo("");
      setCriando(false);
      await carregar();
      toast("Lista criada");
    } catch (e) {
      onError((e as Error).message);
    }
  }

  async function excluir(lista: TodoList) {
    setExcluindo(null);
    try {
      await api.deleteTodoList(lista.id);
      await carregar();
      toast("Lista movida para a lixeira");
    } catch (e) {
      onError((e as Error).message);
    }
  }

  // Afazer já usado por alguma linha não aparece para escolher de novo: o
  // vínculo é um-para-um, e oferecer o que vai ser recusado é uma armadilha.
  const jaVinculados = new Set(
    listas.flatMap((l) => l.items.map((i) => i.todo).filter(Boolean) as string[]),
  );

  return (
    <div>
      {/* Não uso `.list-toolbar` aqui: lá dentro vale `button { flex: 1 }`,
          regra feita para uma fileira de botões que dividem a linha — com um
          botão só ele estica de ponta a ponta. */}
      <div className="listas-topo">
        <button className="primary" onClick={() => setCriando((v) => !v)}>
          {criando ? "Cancelar" : "Nova lista"}
        </button>
      </div>

      {criando && (
        <div className="card block lista-nova">
          <input
            placeholder="Título da lista — ex.: Preparar release 4.2"
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void criar()}
            autoFocus
          />
          <input
            type="date"
            aria-label="Prazo da lista"
            title="Prazo da lista — o sino cobra enquanto houver linha aberta"
            value={prazo}
            onChange={(e) => setPrazo(e.target.value)}
          />
          <button className="primary" onClick={() => void criar()} disabled={!titulo.trim()}>
            Criar
          </button>
        </div>
      )}

      {listas.length === 0 ? (
        <EmptyState
          icon="todos"
          title="Nenhuma lista ainda"
          action={{ label: "Nova lista", onClick: () => setCriando(true) }}
        >
          Uma lista é um <strong>roteiro</strong>: passos que só fazem sentido
          juntos, com um prazo da lista. Quando uma linha precisa de prazo e
          status próprios, vincule-a a um afazer — o afazer traz a data, a
          linha traz o passo.
        </EmptyState>
      ) : (
        <div className="listas">
          {listas.map((lista) => (
            <Lista
              key={lista.id}
              lista={lista}
              hoje={hoje}
              afazeres={afazeres.filter(
                (t) => !jaVinculados.has(t.id) || lista.items.some((i) => i.todo === t.id),
              )}
              onAcao={acao}
              onExcluir={() => setExcluindo(lista)}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      )}

      {excluindo && (
        <ConfirmModal
          title="Excluir lista"
          message={
            <>
              Mover <span className="mono">{excluindo.id}</span> para a lixeira?
              As linhas vão junto; os afazeres vinculados{" "}
              <strong>continuam existindo</strong>.
            </>
          }
          confirmLabel="Mover para a lixeira"
          danger
          onConfirm={() => void excluir(excluindo)}
          onCancel={() => setExcluindo(null)}
        />
      )}
    </div>
  );
}

function Lista({
  lista,
  hoje,
  afazeres,
  onAcao,
  onExcluir,
  onNavigate,
}: {
  lista: TodoList;
  hoje: string;
  afazeres: Todo[];
  onAcao: (fn: () => Promise<TodoList>) => Promise<void>;
  onExcluir: () => void;
  onNavigate: (id: string) => void;
}) {
  const [nova, setNova] = useState("");
  const pct = lista.progress.total
    ? Math.round((lista.progress.done / lista.progress.total) * 100)
    : 0;
  const aberta = lista.status === "active" && lista.progress.open > 0;

  return (
    <section className={`card lista lista-${lista.status}`}>
      <div className="lista-topo">
        <div className="lista-titulo">
          <span className="mono muted caption">{lista.id}</span>
          <h3>{lista.title}</h3>
        </div>
        <span className="spacer" style={{ flex: 1 }} />
        {lista.due && (
          <span
            className={`mono caption ${prazoClasse(lista.due, hoje, aberta)}`}
            title={
              aberta
                ? "prazo da lista — o sino cobra enquanto houver linha aberta"
                : "prazo da lista"
            }
          >
            📅 {lista.due}
          </span>
        )}
        <select
          className="status-select"
          value={lista.status}
          aria-label="Status da lista"
          onChange={(e) =>
            void onAcao(() => api.updateTodoList(lista.id, { status: e.target.value }))
          }
        >
          <option value="active">active</option>
          <option value="done">done</option>
          <option value="archived">archived</option>
        </select>
        <button className="btn-sm danger" onClick={onExcluir}>
          Excluir
        </button>
      </div>

      <div className="lista-progresso" title={`${lista.progress.done} de ${lista.progress.total}`}>
        <div className="lista-barra">
          <span style={{ width: `${pct}%` }} />
        </div>
        <span className="caption muted">
          {lista.progress.done}/{lista.progress.total}
        </span>
      </div>

      <ul className="lista-linhas">
        {lista.items.map((item) => (
          <Linha
            key={item.id}
            lista={lista}
            item={item}
            afazeres={afazeres}
            onAcao={onAcao}
            onNavigate={onNavigate}
          />
        ))}
      </ul>

      <div className="lista-adicionar">
        <input
          placeholder="Adicionar um passo…"
          value={nova}
          onChange={(e) => setNova(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && nova.trim()) {
              const texto = nova.trim();
              setNova("");
              void onAcao(() => api.addTodoListItem(lista.id, texto));
            }
          }}
        />
      </div>
    </section>
  );
}

function Linha({
  lista,
  item,
  afazeres,
  onAcao,
  onNavigate,
}: {
  lista: TodoList;
  item: TodoListItem;
  afazeres: Todo[];
  onAcao: (fn: () => Promise<TodoList>) => Promise<void>;
  onNavigate: (id: string) => void;
}) {
  const [editando, setEditando] = useState(false);
  const [texto, setTexto] = useState(item.text);

  return (
    <li className={`lista-linha ${item.done ? "lista-feita" : ""}`.trim()}>
      <input
        type="checkbox"
        checked={item.done}
        aria-label={`Concluir ${item.text}`}
        onChange={() =>
          void onAcao(() =>
            api.updateTodoListItem(lista.id, item.id, { done: !item.done }),
          )
        }
      />
      {editando ? (
        <input
          className="lista-editar"
          value={texto}
          autoFocus
          onChange={(e) => setTexto(e.target.value)}
          onBlur={() => {
            setEditando(false);
            if (texto.trim() && texto !== item.text) {
              void onAcao(() =>
                api.updateTodoListItem(lista.id, item.id, { text: texto.trim() }),
              );
            }
          }}
          onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()}
        />
      ) : (
        <button className="lista-texto" onClick={() => setEditando(true)} title="Editar">
          {item.text}
        </button>
      )}

      {/* O afazer vinculado aparece RESOLVIDO: prazo e status dele sem quem lê
          precisar abrir outra tela. É o ponto do vínculo. */}
      {item.todo_ref ? (
        <button
          className="lista-afazer"
          onClick={() => onNavigate(item.todo_ref!.id)}
          title={`${item.todo_ref.title} — ${item.todo_ref.status}${
            item.todo_ref.due ? ` · vence ${item.todo_ref.due}` : ""
          }`}
        >
          <span className={`status-dot ${STATUS_DOT[item.todo_ref.status]}`} />
          <span className="mono">{item.todo_ref.id}</span>
          {item.todo_ref.due && <span className="caption">📅 {item.todo_ref.due}</span>}
        </button>
      ) : null}

      <select
        className="lista-vincular"
        value={item.todo ?? ""}
        aria-label="Vincular a um afazer"
        title="Vincular a um afazer — ele traz o prazo e o status"
        onChange={(e) =>
          void onAcao(() =>
            api.updateTodoListItem(lista.id, item.id, {
              todo: e.target.value || null,
            }),
          )
        }
      >
        <option value="">sem afazer</option>
        {afazeres.map((t) => (
          <option key={t.id} value={t.id}>
            {t.id} — {t.title.slice(0, 40)}
          </option>
        ))}
      </select>

      <button
        className="btn-sm lista-remover"
        title="Remover a linha"
        onClick={() => void onAcao(() => api.deleteTodoListItem(lista.id, item.id))}
      >
        ×
      </button>
    </li>
  );
}
