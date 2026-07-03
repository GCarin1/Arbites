import type { Warning } from "../types";

export function WarningsView({ warnings }: { warnings: Warning[] }) {
  if (warnings.length === 0) {
    return <p className="empty">Nenhum problema de integridade no workspace.</p>;
  }
  return (
    <div>
      <h2 style={{ fontSize: 16, marginBottom: 12 }}>
        Problemas ({warnings.length})
      </h2>
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
  );
}
