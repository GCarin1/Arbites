import { Component, type ErrorInfo, type ReactNode } from "react";

/**
 * Impede que um erro de render de UMA view derrube o app inteiro (tela preta).
 * Sem isso, uma exceção não tratada durante o render propaga até a raiz e o
 * React 18 desmonta tudo — e como é erro de runtime do browser, não aparece
 * em nenhum log de servidor. Aqui mostramos a mensagem e o resto do app
 * (menu, outras abas) segue utilizável.
 *
 * Use com `key={algoQueMudaAoTrocarDeView}` para que trocar de aba limpe o
 * estado de erro (remonta o boundary).
 */
export class ErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // vai para o console do browser (onde erros de render aparecem)
    console.error("ErrorBoundary capturou um erro de render:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="empty-state">
          <div className="empty-title">Algo quebrou nesta tela</div>
          <div className="empty-body">
            Um erro impediu a renderização desta aba. As outras seguem
            funcionando — troque de aba e volte, ou recarregue a página.
            <br />
            <span className="mono caption">{this.state.error.message}</span>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
