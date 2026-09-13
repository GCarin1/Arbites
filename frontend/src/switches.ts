/**
 * Canal de "os interruptores mudaram" (change 0143).
 *
 * O painel de administração e a casca do app são componentes irmãos: o
 * painel liga e desliga um módulo, a casca é quem decide o menu e a rota.
 * Sem um canal entre os dois, o admin desligava um módulo e o menu só
 * mudava no recarregamento seguinte — com o item ainda clicável nesse
 * meio-tempo, levando a uma tela que o servidor já recusava.
 *
 * O evento NÃO carrega estado: ele só diz "releia". A verdade continua
 * sendo a resposta do servidor, que é a mesma lista que gera o bloqueio no
 * gate — assim o que a UI esconde e o que a API recusa não divergem.
 */
export const SWITCHES_CHANGED = "arbites:switches-changed";

export function notifySwitchesChanged(): void {
  window.dispatchEvent(new Event(SWITCHES_CHANGED));
}
