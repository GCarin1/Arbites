import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { AdminOverview, LoginAttempt, ManagedUser, Role, Switch } from "../types";
import { useToast } from "./Toast";

type Pane = "users" | "access" | "system";

const PANES: { key: Pane; label: string }[] = [
  { key: "users", label: "Usuários" },
  { key: "access", label: "Acessos" },
  { key: "system", label: "Sistema" },
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
  const [pendingRole, setPendingRole] = useState<Record<number, Role>>({});
  const { toast } = useToast();

  const load = useCallback(async () => {
    try {
      const [u, a, o] = await Promise.all([
        api.adminUsers(),
        api.adminAccessLog(),
        api.adminOverview(),
      ]);
      setUsers(u.users);
      setAttempts(a.attempts);
      setOverview(o);
    } catch (err) {
      toast(err instanceof Error ? err.message : "falha ao carregar", "error");
    }
  }, [toast]);

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
      <div className="card-head block">
        <h3>Administração</h3>
        <span className="spacer" />
        {PANES.map((p) => (
          <button
            key={p.key}
            className={pane === p.key ? "primary" : ""}
            onClick={() => setPane(p.key)}
          >
            {p.label}
          </button>
        ))}
      </div>

      {pane === "users" && (
        <>
          <div className="card block">
            <div className="card-head">
              <h3>Aguardando liberação</h3>
            </div>
            {pending.length === 0 ? (
              <p className="muted">
                Nenhum cadastro aguardando. Contas novas aparecem aqui antes de
                conseguirem entrar.
              </p>
            ) : (
              <div className="table-wrap">
                <table className="dense">
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
                      <td>
                        {u.name || "—"}
                        <br />
                        <span className="muted">{u.email}</span>
                      </td>
                      <td>{when(u.created_at)}</td>
                      <td>
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
                      <td>
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
              <table className="dense">
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
                      <td>
                        {u.name || "—"}
                        <br />
                        <span className="muted">{u.email}</span>
                      </td>
                      <td>
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
                      <td>{STATUS_LABEL[u.status] ?? u.status}</td>
                      <td>{when(u.last_login_at)}</td>
                      <td>{u.open_sessions}</td>
                      <td>
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
            <table className="dense">
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
                  <td>{when(a.at)}</td>
                  <td>{a.email}</td>
                  <td>
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
            <p className="muted">Nenhuma tentativa registrada ainda.</p>
          )}
        </div>
      )}

      {pane === "system" && overview && (
        <>
          <div className="card block">
            <div className="card-head">
              <h3>Superfícies perigosas</h3>
            </div>
            <p className="muted">
              Desligue o que esta instância não usa. Vale na hora, sem
              reiniciar o processo.
            </p>
            <div className="table-wrap">
              <table className="dense">
              <tbody>
                {overview.switches.map((s: Switch) => (
                  <tr key={s.name}>
                    <td>
                      {s.label}
                      <br />
                      <span className="muted mono">{s.name}</span>
                    </td>
                    <td>
                      {s.updated_at ? (
                        <span className="muted">
                          {when(s.updated_at)} por {s.updated_by}
                        </span>
                      ) : (
                        <span className="muted">nunca alterado</span>
                      )}
                    </td>
                    <td>
                      <button
                        className={s.enabled ? "danger" : "primary"}
                        onClick={() =>
                          act(
                            () => api.setSwitch(s.name, !s.enabled),
                            `${s.label}: ${s.enabled ? "desligado" : "ligado"}`,
                          )
                        }
                      >
                        {s.enabled ? "Desligar" : "Ligar"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </div>

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
