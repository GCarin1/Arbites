import type { Warning } from "../types";

export function WarningsView({ warnings }: { warnings: Warning[] }) {
  if (warnings.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-title">Tudo consistente</div>
        <div className="empty-body">
          Nenhum problema de integridade no workspace.
        </div>
      </div>
    );
  }
  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Problemas ({warnings.length})</h1>
      </div>
      <div className="table-wrap">
      <table className="dense">
        <thead>
          <tr>
            <th>Arquivo</th>
            <th>Código</th>
            <th>Mensagem</th>
          </tr>
        </thead>
        <tbody>
          {warnings.map((warning, i) => (
            <tr key={i}>
              <td className="mono">{warning.source_path}</td>
              <td className="mono">{warning.code}</td>
              <td>{warning.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}
