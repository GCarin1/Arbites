import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { notifySwitchesChanged } from "../switches";
import type { AgentToken, ExternalLink, Switch } from "../types";
import { EmptyState } from "./EmptyState";
import { ConfirmModal } from "./Modal";
import { useToast } from "./Toast";

/** O que o agente alcança hoje, separado por efeito (change 0149). */
const LEITURAS: [string, string][] = [
  ["coverage_gaps", "o que falta cobrir, por story e por critério EARS"],
  ["impact_of_files", "quais casos um diff afeta (vínculo e correlação, separados)"],
  ["pending_rerun", "casos cujos passos mudaram depois do último resultado"],
  ["context_pack", "pacote de contexto de um escopo"],
  ["execution_report", "resultado, passos e evidências de um ciclo"],
  ["external_links", "o que já está ligado lá fora, e em que estado"],
  ["integration_capabilities", "o que cada sistema externo consegue representar"],
];

const ESCRITAS: [string, string][] = [
  ["create_or_update_testcase", "grava o caso em BDD, idempotente pelo vínculo"],
  ["record_result", "resultado de um caso num ciclo, com passos e evidência"],
  ["link_external", "registra que este caso corresponde àquele card"],
];

const CLIENTES: { key: string; label: string; hint: string }[] = [
  { key: "cursor", label: "Cursor", hint: "Settings → MCP → Add new server" },
  { key: "claude", label: "Claude Desktop", hint: "claude_desktop_config.json" },
  { key: "generico", label: "Genérico", hint: "qualquer cliente MCP por stdio" },
];


function quando(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR");
  } catch {
    return iso;
  }
}

/**
 * A página do MCP (change 0149).
 *
 * É onde se liga o servidor, se gera a credencial do agente, se vê o que ele
 * alcança e o que ele já fez. Mora na aba de IA porque responde a mesma
 * pergunta das outras: *como a IA alcança o meu trabalho?*
 *
 * NÃO é um console de MCP: não se chama ferramenta na mão por aqui. Quem
 * chama é o agente, e um playground seria uma segunda porta para auditar.
 */
export function McpPanel({
  isAdmin,
  onError,
}: {
  isAdmin: boolean;
  onError: (message: string) => void;
}) {
  const [switches, setSwitches] = useState<Switch[]>([]);
  const [tokens, setTokens] = useState<AgentToken[]>([]);
  const [links, setLinks] = useState<ExternalLink[]>([]);
  const [cliente, setCliente] = useState("cursor");
  const [novoNome, setNovoNome] = useState("");
  const [emClaro, setEmClaro] = useState<string | null>(null);
  const [revogando, setRevogando] = useState<AgentToken | null>(null);
  const { toast } = useToast();

  const carregar = useCallback(async () => {
    try {
      const [sw, tk, lk] = await Promise.all([
        api.switches(),
        api.agentTokens(),
        api.externalLinks().catch(() => ({ links: [], count: 0 })),
      ]);
      setSwitches(sw.switches);
      setTokens(tk.tokens);
      setLinks(lk.links);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }, [onError]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const ligado = (nome: string) =>
    switches.find((s) => s.name === nome)?.enabled ?? false;

  async function virar(nome: string, para: boolean) {
    try {
      await api.setSwitch(nome, para);
      notifySwitchesChanged();
      await carregar();
      toast(para ? "ligado" : "desligado");
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function gerar() {
    try {
      const r = await api.createAgentToken(novoNome.trim() || "agente");
      setEmClaro(r.token);
      setNovoNome("");
      await carregar();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function revogar(alvo: AgentToken) {
    setRevogando(null);
    try {
      await api.revokeAgentToken(alvo.id);
      toast(`credencial "${alvo.name}" revogada`);
      await carregar();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  // O endereço REAL da instância, não um placeholder: quem cola o bloco não
  // deveria ter que adivinhar onde o Arbites mora.
  const endereco = window.location.origin;
  const config = JSON.stringify(
    {
      mcpServers: {
        arbites: {
          command: "python",
          args: ["-m", "arbites.mcp"],
          env: {
            ARBITES_URL: endereco,
            ARBITES_TOKEN: emClaro ?? "<credencial gerada abaixo>",
          },
        },
      },
    },
    null,
    2,
  );

  const conflitos = links.filter((l) => l.state === "conflict").length;
  const ligados = links.filter((l) => l.system).length;
  const nunca = links.filter((l) => l.state === "never_synced").length;

  return (
    <>
      <div className="card block">
        <div className="card-head">
          <h3>Servidor MCP</h3>
          <span className="spacer" />
          <span className={`status-dot ${ligado("mcp_server") ? "dot-active" : "dot-draft"}`}>
            {ligado("mcp_server") ? "ligado" : "desligado"}
          </span>
        </div>
        <p className="muted">
          Um agente (Cursor, Claude Desktop) passa a alcançar este workspace
          para responder o que ele não calcula sozinho: onde falta cobertura,
          quais casos um diff afeta, o que já está ligado lá fora. Ele entra
          pela mesma porta que o navegador — papel, módulo desligado e log de
          atividade valem igual.
        </p>
        <ul className="switch-list">
          <li className="switch-row">
            <label className="switch-label" htmlFor="sw-mcp-server">
              <span className="switch-name">Servidor MCP</span>
              <span className="caption muted">
                Desligado, nenhuma credencial de agente funciona. A sua sessão
                no navegador não é afetada.
              </span>
            </label>
            <span className="switch-state">
              <span className={`caption ${ligado("mcp_server") ? "" : "muted"}`}>
                {ligado("mcp_server") ? "Ligado" : "Desligado"}
              </span>
              <input
                id="sw-mcp-server"
                type="checkbox"
                role="switch"
                className="toggle"
                disabled={!isAdmin}
                checked={ligado("mcp_server")}
                onChange={() => void virar("mcp_server", !ligado("mcp_server"))}
              />
            </span>
          </li>
          <li className="switch-row">
            <label className="switch-label" htmlFor="sw-mcp-write">
              <span className="switch-name">Permitir escrita</span>
              <span className="caption muted">
                A pergunta é "ele mexe ou só olha?", e ela tem duas respostas —
                por isso um interruptor, e não um por ferramenta. Nasce
                desligado.
              </span>
            </label>
            <span className="switch-state">
              <span className={`caption ${ligado("mcp_write") ? "" : "muted"}`}>
                {ligado("mcp_write") ? "Lê e escreve" : "Somente leitura"}
              </span>
              <input
                id="sw-mcp-write"
                type="checkbox"
                role="switch"
                className="toggle"
                disabled={!isAdmin}
                checked={ligado("mcp_write")}
                onChange={() => void virar("mcp_write", !ligado("mcp_write"))}
              />
            </span>
          </li>
        </ul>
        {!isAdmin && (
          <p className="caption muted" style={{ marginTop: 8 }}>
            Ver a configuração não é privilégio; mudá-la é. Só uma conta
            administradora liga, desliga e gera credencial.
          </p>
        )}
      </div>

      <div className="card block">
        <div className="card-head">
          <h3>Como conectar</h3>
          <span className="spacer" />
          <select value={cliente} onChange={(e) => setCliente(e.target.value)}>
            {CLIENTES.map((c) => (
              <option key={c.key} value={c.key}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
        <p className="muted">
          {CLIENTES.find((c) => c.key === cliente)?.hint} — cole o bloco abaixo
          e reinicie o cliente.
        </p>
        <pre className="mcp-config scroll-x">
          <code>{config}</code>
        </pre>
        <div className="toolbar">
          <button
            onClick={() => {
              void navigator.clipboard?.writeText(config);
              toast("configuração copiada");
            }}
          >
            Copiar configuração
          </button>
          {!emClaro && (
            <span className="caption muted">
              A credencial entra no lugar do marcador — gere uma abaixo.
            </span>
          )}
        </div>
      </div>

      <div className="card block">
        <div className="card-head">
          <h3>Credencial do agente</h3>
        </div>
        <p className="muted">
          Separada da sua sessão no navegador: revogar o agente não derruba a
          sua sessão, e sair do navegador não derruba o agente. Ela herda o
          papel da sua conta — o agente nunca alcança mais que você.
        </p>

        {emClaro && (
          <div className="error-banner" style={{ wordBreak: "break-all" }}>
            <strong>Guarde agora:</strong> esta é a única vez que a credencial
            aparece. Depois daqui só existe o hash dela.
            <div className="mono" style={{ marginTop: 6 }}>{emClaro}</div>
          </div>
        )}

        {isAdmin && (
          <div className="toolbar">
            <input
              placeholder="nome da credencial (ex.: cursor do notebook)"
              value={novoNome}
              onChange={(e) => setNovoNome(e.target.value)}
              style={{ maxWidth: 320 }}
            />
            <button className="primary" onClick={() => void gerar()}>
              Gerar credencial
            </button>
          </div>
        )}

        {tokens.length === 0 ? (
          <EmptyState compact icon="ia" title="Nenhuma credencial ainda">
            Sem credencial o agente não entra. Gere uma, cole no cliente MCP e
            ele passa a enxergar o workspace com o seu papel.
          </EmptyState>
        ) : (
          <div className="table-wrap">
            <table className="dense stack-narrow">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Criada</th>
                  <th>Último uso</th>
                  {isAdmin && <th />}
                </tr>
              </thead>
              <tbody>
                {tokens.map((t) => (
                  <tr key={t.id}>
                    <td data-label="Nome">{t.name}</td>
                    <td className="caption muted" data-label="Criada">
                      {quando(t.created_at)}
                    </td>
                    <td className="caption muted" data-label="Último uso">
                      {t.last_used_at ? quando(t.last_used_at) : "nunca usada"}
                    </td>
                    {isAdmin && (
                      <td data-label="">
                        <button className="btn-sm danger" onClick={() => setRevogando(t)}>
                          Revogar
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card block">
        <div className="card-head">
          <h3>O que o agente alcança</h3>
        </div>
        <h4 className="section-title">Leitura — sempre disponível</h4>
        <ul className="mcp-tools">
          {LEITURAS.map(([nome, oque]) => (
            <li key={nome}>
              <span className="mono">{nome}</span>
              <span className="muted"> — {oque}</span>
            </li>
          ))}
        </ul>
        <h4 className="section-title">
          Escrita — {ligado("mcp_write") ? "liberada" : "bloqueada"}
        </h4>
        <ul className={`mcp-tools ${ligado("mcp_write") ? "" : "mcp-tools-off"}`}>
          {ESCRITAS.map(([nome, oque]) => (
            <li key={nome}>
              <span className="mono">{nome}</span>
              <span className="muted"> — {oque}</span>
            </li>
          ))}
        </ul>
        <p className="caption muted">
          Com a escrita desligada, qualquer alteração vinda do agente é
          recusada pelo servidor — inclusive por caminhos que ainda não
          existem.
        </p>
      </div>

      <div className="card block">
        <div className="card-head">
          <h3>Vínculos externos</h3>
        </div>
        <p className="muted">
          É o que evita o agente criar de novo o que já existe lá fora: antes
          de criar, ele pergunta o que já está ligado.
        </p>
        <div className="mcp-links-summary">
          <span className="status-dot dot-col-passed">{ligados} ligado(s)</span>
          <span className="status-dot dot-col-pending">{nunca} nunca sincronizado(s)</span>
          <span className={`status-dot ${conflitos ? "dot-col-failed" : "dot-col-passed"}`}>
            {conflitos} em conflito
          </span>
        </div>
        {conflitos > 0 && (
          <p className="caption">
            Conflito é mudança dos <strong>dois</strong> lados desde a última
            sincronia. O Arbites não escolhe por você — nenhum lado é
            sobrescrito até alguém decidir.
          </p>
        )}
      </div>

      {revogando && (
        <ConfirmModal
          danger
          title="Revogar credencial"
          message={
            <>
              Revogar <strong>{revogando.name}</strong>? O agente que a usa
              perde o acesso na próxima chamada. A sua sessão no navegador
              continua.
            </>
          }
          confirmLabel="Revogar"
          onConfirm={() => void revogar(revogando)}
          onCancel={() => setRevogando(null)}
        />
      )}
    </>
  );
}
