import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { notifySwitchesChanged } from "../switches";
import type {
  ActivityEntry,
  AdminOverview,
  LoginAttempt,
  ManagedUser,
  Role,
  Switch,
} from "../types";
import { EmptyState, NoMatches } from "./EmptyState";
import { TabBar } from "./TabBar";
import { useToast } from "./Toast";

type Pane = "users" | "access" | "activity" | "system";

const PANE_TABS: readonly (readonly [Pane, string])[] = [
  ["users", "Usuários"],
  ["access", "Acessos"],
  ["activity", "Atividade"],
  ["system", "Sistema"],
];

const ROLES: Role[] = ["admin", "editor", "viewer"];

const STATUS_LABEL: Record<string, string> = {
  pending: "Pendente",
  active: "Ativo",
  disabled: "Desativado",
  rejected: "Recusado",
};

function when(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("pt-BR");
}

export function Admin({ currentUserId }: { currentUserId: number }) {
  const [pane, setPane] = useState<Pane>("users");
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [attempts, setAttempts] = useState<LoginAttempt[]>([]);
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [filterUser, setFilterUser] = useState("");
  const [filterPath, setFilterPath] = useState("");
  const [pendingRole, setPendingRole] = useState<Record<number, Role>>({});
  const { toast } = useToast();

  const load = useCallback(async () => {
    try {
      const [u, a, o, act] = await Promise.all([
        api.adminUsers(),
        api.adminAccessLog(),
        api.adminOverview(),
        api.adminActivity({ user: filterUser, path: filterPath }),
      ]);
      setUsers(u.users);
      setAttempts(a.attempts);
      setOverview(o);
      setActivity(act.entries);
    } catch (err) {
      toast(err instanceof Error ? err.message : "falha ao carregar", "error");
    }
  }, [toast, filterUser, filterPath]);

  useEffect(() => {
    void load();
  }, [load]);

  const act = useCallback(
    async (run: () => Promise<unknown>, done: string) => {
      try {
        await run();
        toast(done);
        await load();
      } catch (err) {
        toast(
          err instanceof Error ? err.message : "falha na operação",
          "error",
        );
      }
    },
    [load, toast],
  );

  const pending = users.filter((u) => u.status === "pending");
  const rest = users.filter((u) => u.status !== "pending");

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Administração</h1>
      </div>
      {/* A faixa canônica rola dentro de si (0135). Como botões soltos num
          `card-head`, as quatro abas empurravam a largura da PÁGINA em
          390 px e a tela inteira rolava de lado (0142). */}
      <TabBar
        tabs={PANE_TABS}
        value={pane}
        onChange={setPane}
        className="block"
        label="Seções da administração"
      />

      {pane === "users" && (
        <>
          <div className="card block">
            <div className="card-head">
              <h3>Aguardando liberação</h3>
            </div>
            {pending.length === 0 ? (
              <EmptyState compact icon="profile" title="Nenhum cadastro aguardando">
                Quem se cadastra entra nesta fila e não consegue entrar até
                alguém liberar. Ao liberar, você escolhe o papel da conta.
              </EmptyState>
            ) : (
              <div className="table-wrap">
                <table className="dense stack-narrow">
                <thead>
                  <tr>
                    <th>Conta</th>
                    <th>Cadastro</th>
                    <th>Papel na liberação</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {pending.map((u) => (
                    <tr key={u.id}>
                      <td data-label="Conta">
                        {u.name || "—"}
                        <br />
                        <span className="muted">{u.email}</span>
                      </td>
                      <td data-label="Cadastro">{when(u.created_at)}</td>
                      <td data-label="Papel na liberação">
                        <select
                          value={pendingRole[u.id] ?? "viewer"}
                          onChange={(e) =>
                            setPendingRole({
                              ...pendingRole,
                              [u.id]: e.target.value as Role,
                            })
                          }
                        >
                          {ROLES.map((r) => (
                            <option key={r} value={r}>
                              {r}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td data-label="">
                        <button
                          className="primary"
                          onClick={() =>
                            act(
                              () =>
                                api.adminApprove(
                                  u.id,
                                  pendingRole[u.id] ?? "viewer",
                                ),
                              `${u.email} liberado`,
                            )
                          }
                        >
                          Liberar
                        </button>{" "}
                        <button
                          className="danger"
                          onClick={() =>
                            act(() => api.adminReject(u.id), `${u.email} recusado`)
                          }
                        >
                          Recusar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            )}
          </div>

          <div className="card block">
            <div className="card-head">
              <h3>Contas</h3>
            </div>
            <div className="table-wrap">
              <table className="dense stack-narrow">
              <thead>
                <tr>
                  <th>Conta</th>
                  <th>Papel</th>
                  <th>Status</th>
                  <th>Último login</th>
                  <th>Sessões</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {rest.map((u) => {
                  const isSelf = u.id === currentUserId;
                  return (
                    <tr key={u.id}>
                      <td data-label="Conta">
                        {u.name || "—"}
                        <br />
                        <span className="muted">{u.email}</span>
                      </td>
                      <td data-label="Papel">
                        <select
                          value={u.role}
                          disabled={isSelf}
                          onChange={(e) =>
                            act(
                              () => api.adminSetRole(u.id, e.target.value as Role),
                              `${u.email} agora é ${e.target.value}`,
                            )
                          }
                        >
                          {ROLES.map((r) => (
                            <option key={r} value={r}>
                              {r}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td data-label="Status">{STATUS_LABEL[u.status] ?? u.status}</td>
                      <td data-label="Último login">{when(u.last_login_at)}</td>
                      <td data-label="Sessões">{u.open_sessions}</td>
                      <td data-label="">
                        {isSelf ? (
                          <span className="muted">esta é a sua conta</span>
                        ) : (
                          <>
                            {u.status === "active" ? (
                              <button
                                onClick={() =>
                                  act(
                                    () => api.adminDisable(u.id),
                                    `${u.email} desativado`,
                                  )
                                }
                              >
                                Desativar
                              </button>
                            ) : (
                              <button
                                onClick={() =>
                                  act(
                                    () => api.adminEnable(u.id),
                                    `${u.email} reativado`,
                                  )
                                }
                              >
                                Reativar
                              </button>
                            )}{" "}
                            <button
                              disabled={u.open_sessions === 0}
                              onClick={() =>
                                act(
                                  () => api.adminRevokeSessions(u.id),
                                  `sessões de ${u.email} encerradas`,
                                )
                              }
                            >
                              Encerrar sessões
                            </button>{" "}
                            <button
                              onClick={() => {
                                const temporary = window.prompt(
                                  `Senha temporária para ${u.email}` +
                                    " (mínimo 12 caracteres; será trocada no" +
                                    " primeiro login):",
                                );
                                if (temporary) {
                                  void act(
                                    () => api.adminResetPassword(u.id, temporary),
                                    `senha temporária definida para ${u.email}`,
                                  );
                                }
                              }}
                            >
                              Definir senha
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            </div>
            <p className="muted">
              Contas não são apagadas: desativar preserva a autoria das
              execuções e defeitos já registrados.
            </p>
          </div>
        </>
      )}

      {pane === "access" && (
        <div className="card block">
          <div className="card-head">
            <h3>Tentativas de autenticação</h3>
          </div>
          <div className="table-wrap">
            <table className="dense stack-narrow">
            <thead>
              <tr>
                <th>Quando</th>
                <th>Conta informada</th>
                <th>Resultado</th>
                <th>IP</th>
                <th>Navegador</th>
              </tr>
            </thead>
            <tbody>
              {attempts.map((a, i) => (
                <tr key={`${a.at}-${i}`}>
                  <td data-label="Quando">{when(a.at)}</td>
                  <td data-label="Conta informada">{a.email}</td>
                  <td data-label="Resultado">
                    <span
                      className={`status-dot ${
                        a.ok ? "dot-col-passed" : "dot-col-failed"
                      }`}
                    />
                    {a.ok ? "Entrou" : "Recusado"}
                  </td>
                  <td className="mono">{a.ip || "—"}</td>
                  <td className="muted">{a.user_agent || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
            </div>
          {attempts.length === 0 && (
            <EmptyState compact icon="audit" title="Nenhuma tentativa de acesso registrada">
              Cada login, aceito ou recusado, aparece aqui com horário, IP e
              navegador. Vazio é a boa notícia num ambiente recém-instalado.
            </EmptyState>
          )}
        </div>
      )}

      {pane === "activity" && (
        <div className="card block">
          <div className="card-head">
            <h3>Quem fez o quê</h3>
          </div>
          <div className="field-grid">
            <div className="field col-3">
              <label htmlFor="act-user">Autor</label>
              <input
                id="act-user"
                placeholder="e-mail exato"
                value={filterUser}
                onChange={(e) => setFilterUser(e.target.value)}
              />
            </div>
            <div className="field col-3">
              <label htmlFor="act-path">Caminho contém</label>
              <input
                id="act-path"
                placeholder="/testcases"
                value={filterPath}
                onChange={(e) => setFilterPath(e.target.value)}
              />
            </div>
          </div>
          <div className="table-wrap">
            <table className="dense stack-narrow">
              <thead>
                <tr>
                  <th>Quando</th>
                  <th>Autor</th>
                  <th>Ação</th>
                  <th>IP</th>
                </tr>
              </thead>
              <tbody>
                {activity.map((e, i) => (
                  <tr key={`${e.at}-${i}`}>
                    <td data-label="Quando">{when(e.at)}</td>
                    <td data-label="Autor">{e.user_email}</td>
                    <td className="mono" data-label="Ação">
                      {e.method} {e.path}
                    </td>
                    <td className="mono" data-label="IP">{e.ip || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {activity.length === 0 &&
            (filterUser || filterPath ? (
              <NoMatches
                what="escritas"
                onClear={() => {
                  setFilterUser("");
                  setFilterPath("");
                }}
              />
            ) : (
              <EmptyState compact icon="audit" title="Nenhuma escrita registrada">
                Toda alteração passa por aqui com autor, rota e horário.
                Leituras não entram, e tentativas recusadas também não.
              </EmptyState>
            ))}
        </div>
      )}

      {pane === "system" && overview && (
        <>
          <SwitchCard
            title="Módulos do produto"
            hint={
              "Desligue o que esta instância não usa. O módulo some do menu, " +
              "recusa o link direto e o servidor passa a recusar as chamadas " +
              "dele — não é só um rótulo de desativado. Vale na hora, sem " +
              "reiniciar o processo."
            }
            switches={overview.switches.filter((s) => s.kind === "module")}
            onToggle={(s) =>
              act(
                async () => {
                  const r = await api.setSwitch(s.name, !s.enabled);
                  // a casca relê a lista: o menu e a rota mudam na hora
                  notifySwitchesChanged();
                  return r;
                },
                `${s.label}: ${s.enabled ? "desligado" : "ligado"}`,
              )
            }
          />

          <SwitchCard
            title="Superfícies perigosas"
            hint={
              "Não são telas, são capacidades técnicas do servidor. Desligue " +
              "o que esta instância não precisa para reduzir o alcance de " +
              "quem entrar sem convite."
            }
            switches={overview.switches.filter((s) => s.kind !== "module")}
            onToggle={(s) =>
              act(
                async () => {
                  const r = await api.setSwitch(s.name, !s.enabled);
                  // a casca relê a lista: o menu e a rota mudam na hora
                  notifySwitchesChanged();
                  return r;
                },
                `${s.label}: ${s.enabled ? "desligado" : "ligado"}`,
              )
            }
          />

          <div className="card block">
            <div className="card-head">
              <h3>Instância</h3>
            </div>
            <div className="field-grid">
              <div className="field col-3">
                <label>Versão</label>
                <span>{overview.version}</span>
              </div>
              <div className="field col-3">
                <label>Último reindex</label>
                <span>{when(overview.index.last_reindex)}</span>
              </div>
              <div className="field col-3">
                <label>Itens na lixeira</label>
                <span>{overview.trash_items}</span>
              </div>
              <div className="field col-3">
                <label>Contas</label>
                <span>
                  {overview.users.active} ativas · {overview.users.pending}{" "}
                  pendentes · {overview.users.disabled} desativadas
                </span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}


/**
 * Lista de interruptores com um TOGGLE por linha (change 0143).
 *
 * Antes era uma tabela com um botão "Desligar"/"Ligar": o rótulo do botão
 * dizia a AÇÃO, não o ESTADO, e para saber se a feature estava ligada era
 * preciso ler o botão ao contrário. Um `switch` de verdade mostra o estado e
 * aceita o clique no mesmo lugar, e o teclado o alcança como qualquer caixa
 * de marcar.
 */
function SwitchCard({
  title,
  hint,
  switches,
  onToggle,
}: {
  title: string;
  hint: string;
  switches: Switch[];
  onToggle: (s: Switch) => void;
}) {
  return (
    <div className="card block">
      <div className="card-head">
        <h3>{title}</h3>
      </div>
      <p className="muted">{hint}</p>
      <ul className="switch-list">
        {switches.map((s) => (
          <li key={s.name} className="switch-row">
            <label className="switch-label" htmlFor={`sw-${s.name}`}>
              <span className="switch-name">{s.label}</span>
              <span className="caption muted mono">{s.name}</span>
              <span className="caption muted">
                {s.updated_at
                  ? `${when(s.updated_at)} por ${s.updated_by}`
                  : "nunca alterado"}
              </span>
            </label>
            <span className="switch-state">
              <span className={`caption ${s.enabled ? "" : "muted"}`}>
                {s.enabled ? "Ligado" : "Desligado"}
              </span>
              <input
                id={`sw-${s.name}`}
                type="checkbox"
                role="switch"
                className="toggle"
                checked={s.enabled}
                onChange={() => onToggle(s)}
              />
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
