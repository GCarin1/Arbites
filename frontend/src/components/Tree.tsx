import type { TreeNode } from "../types";

export function Tree({
  root,
  selected,
  onSelect,
}: {
  root: TreeNode;
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="tree">
      <ul>
        <TreeLevel node={root} selected={selected} onSelect={onSelect} isRoot />
      </ul>
    </div>
  );
}

function TreeLevel({
  node,
  selected,
  onSelect,
  isRoot = false,
}: {
  node: TreeNode;
  selected: string | null;
  onSelect: (id: string) => void;
  isRoot?: boolean;
}) {
  return (
    <li>
      {!isRoot && <div className="dir mono">{node.name}/</div>}
      <ul>
        {node.dirs.map((dir) => (
          <TreeLevel key={dir.path} node={dir} selected={selected} onSelect={onSelect} />
        ))}
        {node.files.map((file) => (
          <li key={file.path}>
            <button
              className={`file ${file.id === selected ? "selected" : ""}`}
              onClick={() => file.id && onSelect(file.id)}
              disabled={!file.id}
              title={file.path}
            >
              <span className="mono muted">{file.id ?? "?"}</span>
              <span>{file.title}</span>
            </button>
          </li>
        ))}
      </ul>
    </li>
  );
}
