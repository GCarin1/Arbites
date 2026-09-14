import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import { NavIcon } from "./NavIcons";
import type { Notification, NotificationTarget } from "../types";

/**
 * O sino (change 0161).
 *
 * A lista é DERIVADA do estado vivo pelo servidor — não é uma caixa de
 * entrada. A consequência é deliberada e vale entender: um problema que foi
 * resolvido some daqui mesmo sem ter sido lido, porque deixou de existir.
 * Caixa de entrada gravada criaria um segundo estado, e o segundo diverge do
 * primeiro: alguém clicaria num aviso já corrigido e não acharia nada lá.
 *
 * O que o servidor guarda por pessoa é só "o que eu li" e "até onde limpei".
 */

const ROTULO: Record<string, { label: string; dot: string }> = {
  problema: { label: "problema", dot: "dot-col-failed" },
  prazo: { label: "prazo", dot: "dot-col-blocked" },
  observabilidade: { label: "observabilidade", dot: "dot-col-blocked" },
  feito: { label: "concluído", dot: "dot-col-passed" },
  info: { label: "log", dot: "dot-col-pending" },
};

function quando(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const minutos = Math.floor((Date.now() - d.getTime()) / 60000);
  if (minutos < 1) return "agora";
  if (minutos < 60) return `há ${minutos} min`;
  const horas = Math.floor(minutos / 60);
  if (horas < 24) return `há ${horas} h`;
  const dias = Math.floor(horas / 24);
  return dias === 1 ? "ontem" : `há ${dias} dias`;
}

export function NotificationBell({
  onGo,
  onError,
}: {
  /** Leva para a origem da notificação. */
  onGo: (target: NotificationTarget) => void;
  onError?: (message: string) => void;
}) {
  const [itens, setItens] = useState<Notification[]>([]);
  const [naoLidas, setNaoLidas] = useState(0);
  const [aberto, setAberto] = useState(false);
  const caixa = useRef<HTMLDivElement>(null);

  const carregar = useCallback(async () => {
    try {
      const r = await api.notifications();
      setItens(r.items);
      setNaoLidas(r.unread);
    } catch (e) {
      // Sino que grita erro no topo de toda tela é pior do que sino mudo:
      // o resto da aplicação não depende dele.
      onError?.((e as Error).message);
    }
  }, [onError]);

  useEffect(() => {
    void carregar();
    // Local-first: uma consulta por minuto basta e não pede websocket.
    const t = window.setInterval(() => void carregar(), 60000);
    return () => window.clearInterval(t);
  }, [carregar]);

  // Fecha ao clicar fora e no Esc — um painel que só fecha no próprio botão
  // fica no caminho de quem já seguiu para outra coisa.
  useEffect(() => {
    if (!aberto) return;
    const foraClique = (e: MouseEvent) => {
      if (caixa.current && !caixa.current.contains(e.target as Node)) {
        setAberto(false);
      }
    };
    const tecla = (e: KeyboardEvent) => e.key === "Escape" && setAberto(false);
    document.addEventListener("mousedown", foraClique);
    document.addEventListener("keydown", tecla);
    return () => {
      document.removeEventListener("mousedown", foraClique);
      document.removeEventListener("keydown", tecla);
    };
  }, [aberto]);

  const marcar = async (item: Notification, lida: boolean) => {
    setItens((antes) =>
      antes.map((i) => (i.id === item.id ? { ...i, read: lida } : i)),
    );
    setNaoLidas((n) => Math.max(0, n + (lida ? -1 : 1)));
    try {
      await api.markNotification(item.id, lida);
    } catch (e) {
      onError?.((e as Error).message);
      void carregar();
    }
  };

  const abrirOrigem = (item: Notification) => {
    setAberto(false);
    if (!item.read) void marcar(item, true);
    onGo(item.target);
  };

  return (
    <div className="sino" ref={caixa}>
      <button
        className="header-icon-btn sino-btn"
        onClick={() => setAberto((v) => !v)}
        aria-label={
          naoLidas > 0
            ? `Notificações: ${naoLidas} não ${naoLidas === 1 ? "lida" : "lidas"}`
            : "Notificações"
        }
        aria-expanded={aberto}
        title="Notificações"
      >
        <NavIcon name="bell" />
        {naoLidas > 0 && (
          <span className="sino-contador" aria-hidden="true">
            {naoLidas > 99 ? "99+" : naoLidas}
          </span>
        )}
      </button>

      {aberto && (
        <div className="sino-painel" role="dialog" aria-label="Notificações">
          <div className="sino-topo">
            <strong>Notificações</strong>
            <span className="spacer" />
            <button
              className="sino-acao"
              disabled={naoLidas === 0}
              onClick={() => {
                void (async () => {
                  const ids = itens.filter((i) => !i.read).map((i) => i.id);
                  setItens((a) => a.map((i) => ({ ...i, read: true })));
                  setNaoLidas(0);
                  try {
                    await api.markAllNotifications(ids);
                  } catch (e) {
                    onError?.((e as Error).message);
                    void carregar();
                  }
                })();
              }}
            >
              Marcar todas como lidas
            </button>
            <button
              className="sino-acao"
              disabled={itens.length === 0}
              onClick={() => {
                void (async () => {
                  try {
                    await api.clearNotifications();
                    setItens([]);
                    setNaoLidas(0);
                  } catch (e) {
                    onError?.((e as Error).message);
                  }
                })();
              }}
            >
              Limpar
            </button>
          </div>

          {itens.length === 0 ? (
            <p className="sino-vazio">
              Nada para avisar. Esta lista é o estado de agora — quando um
              problema é resolvido, ele sai daqui sozinho.
            </p>
          ) : (
            <ul className="sino-lista">
              {itens.map((item) => {
                const marca = ROTULO[item.kind] ?? ROTULO.info;
                return (
                  <li
                    key={item.id}
                    className={`sino-item ${item.read ? "sino-lida" : ""}`.trim()}
                  >
                    <button
                      type="button"
                      className="sino-corpo"
                      onClick={() => abrirOrigem(item)}
                      title="Ir para a origem"
                    >
                      <span className="sino-linha1">
                        <span className={`status-dot ${marca.dot} caption`}>
                          {marca.label}
                        </span>
                        <span className="sino-quando caption muted">
                          {quando(item.at)}
                        </span>
                      </span>
                      <span className="sino-texto">
                        {/* O nome do arquivo/card em destaque, e separado da
                            frase: destacar por regex dentro da mensagem erra
                            na primeira mensagem de formato diferente. */}
                        {item.subject && (
                          <span className="sino-assunto mono" title={item.subject_full}>
                            {item.subject}
                          </span>
                        )}
                        {item.message}
                      </span>
                    </button>
                    <button
                      type="button"
                      className="sino-acao sino-marcar"
                      onClick={() => void marcar(item, !item.read)}
                    >
                      {item.read ? "não lida" : "lida"}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
