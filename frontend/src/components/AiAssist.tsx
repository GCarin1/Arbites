import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { DocBody } from "./ReadView";
import type {
  AiProvider,
  AiProvidersInfo,
  GeneratedTestcase,
  ReviewResponse,
  TestCase,
} from "../types";

const KINDS = [
  "openai_compatible",
  "openai",
  "anthropic",
  "gemini",
  "openrouter",
  "ollama",
  "lmstudio",
  "vllm",
];

export function AiAssist({
  onChanged,
  onError,
}: {
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [info, setInfo] = useState<AiProvidersInfo | null>(null);

  const load = useCallback(() => {
    api
      .aiProviders()
      .then(setInfo)
      .catch((e) => onError(e.message));
  }, [onError]);

  useEffect(() => {
    load();
  }, [load]);

  const enabled = !!info?.default_provider;

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Assistente de IA</h1>
        <span className="spacer" />
        <span className={`status-dot ${enabled ? "dot-active" : "dot-draft"}`}>
          {enabled ? `ativo · ${info?.default_provider}` : "desabilitada"}
        </span>
      </div>

      <ProvidersCard info={info} onSaved={load} onError={onError} />

      {!enabled && (
        <div className="empty-state" style={{ marginBottom: 24 }}>
          <div className="empty-title">IA desabilitada</div>
          <div className="empty-body">
            A plataforma é 100% funcional sem IA. Configure ao menos um provider
            e defina o padrão acima para habilitar geração, revisão e casos
            negativos.
          </div>
        </div>
      )}

      {enabled && info && (
        <>
          <GenerateCard
            defaultProvider={info.default_provider}
            providers={info.providers}
            onChanged={onChanged}
            onError={onError}
          />
          <ReviewCard
            defaultProvider={info.default_provider}
            providers={info.providers}
            onChanged={onChanged}
            onError={onError}
          />
        </>
      )}
    </div>
  );
}

// ------------------------------------------------------------ providers

function ProvidersCard({
  info,
  onSaved,
  onError,
}: {
  info: AiProvidersInfo | null;
  onSaved: () => void;
  onError: (message: string) => void;
}) {
  const [providers, setProviders] = useState<AiProvider[]>([]);
  const [defaultProvider, setDefaultProvider] = useState<string | null>(null);
  const [keys, setKeys] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  // form de novo provider
  const [name, setName] = useState("");
  const [kind, setKind] = useState("openai_compatible");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [newKey, setNewKey] = useState("");

  useEffect(() => {
    if (info) {
      setProviders(info.providers);
      setDefaultProvider(info.default_provider);
    }
  }, [info]);

  function addProvider() {
    if (!name.trim()) return;
    const provider: AiProvider = {
      name: name.trim(),
      kind,
      model: model.trim(),
      base_url: baseUrl.trim() || null,
      key_configured: false,
    };
    setProviders((old) => [...old.filter((p) => p.name !== provider.name), provider]);
    if (newKey.trim()) setKeys((old) => ({ ...old, [provider.name]: newKey.trim() }));
    if (!defaultProvider) setDefaultProvider(provider.name);
    setName("");
    setModel("");
    setBaseUrl("");
    setNewKey("");
  }

  function removeProvider(target: string) {
    setProviders((old) => old.filter((p) => p.name !== target));
    if (defaultProvider === target) setDefaultProvider(null);
  }

  async function save() {
    setSaving(true);
    try {
      const updated = await api.putAiProviders({
        default_provider: defaultProvider,
        providers: providers.map((p) => ({
          name: p.name,
          kind: p.kind,
          model: p.model,
          base_url: p.base_url,
        })),
        keys,
      });
      setKeys({});
      onSaved();
      setProviders(updated.providers);
      setDefaultProvider(updated.default_provider);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div className="card-head">
        <h3>Providers</h3>
        <span className="spacer" />
        <span className="caption">chaves no keyring do SO — nunca no YAML</span>
      </div>

      {providers.length > 0 && (
        <div className="table-wrap" style={{ marginBottom: 16 }}>
          <table className="dense">
            <thead>
              <tr>
                <th>Padrão</th>
                <th>Nome</th>
                <th>Kind</th>
                <th>Modelo</th>
                <th>Base URL</th>
                <th>Chave</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {providers.map((p) => (
                <tr key={p.name}>
                  <td>
                    <input
                      type="radio"
                      name="default-provider"
                      checked={defaultProvider === p.name}
                      onChange={() => setDefaultProvider(p.name)}
                      aria-label={`Definir ${p.name} como padrão`}
                    />
                  </td>
                  <td className="mono">{p.name}</td>
                  <td>{p.kind}</td>
                  <td className="mono">{p.model || "—"}</td>
                  <td className="mono muted">{p.base_url || "—"}</td>
                  <td>
                    <span
                      className={`status-dot ${
                        p.key_configured || keys[p.name] ? "dot-active" : "dot-draft"
                      }`}
                    >
                      {p.key_configured || keys[p.name] ? "ok" : "sem chave"}
                    </span>
                  </td>
                  <td>
                    <button className="btn-sm danger" onClick={() => removeProvider(p.name)}>
                      Remover
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h4 className="section-title" style={{ marginTop: 0 }}>
        Adicionar provider
      </h4>
      <div className="field-grid">
        <div className="field col-3">
          <label>Nome</label>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="ex.: openai" />
        </div>
        <div className="field col-3">
          <label>Kind</label>
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            {KINDS.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
        </div>
        <div className="field col-3">
          <label>Modelo</label>
          <input
            className="mono"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="gpt-4o-mini"
          />
        </div>
        <div className="field col-3">
          <label>Base URL (opcional)</label>
          <input
            className="mono"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="http://localhost:1234/v1"
          />
        </div>
        <div className="field col-6">
          <label>Chave de API (opcional — endpoints locais dispensam)</label>
          <input
            type="password"
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
            placeholder="sk-…"
          />
        </div>
        <div className="field col-6" style={{ justifyContent: "flex-end" }}>
          <label>&nbsp;</label>
          <button onClick={addProvider} disabled={!name.trim()}>
            Adicionar à lista
          </button>
        </div>
      </div>

      <div className="toolbar">
        <button className="primary" onClick={() => void save()} disabled={saving}>
          {saving ? "Salvando…" : "Salvar configuração"}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------- provider select

function ProviderSelect({
  providers,
  value,
  onChange,
}: {
  providers: AiProvider[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{ maxWidth: 220, flex: "0 0 auto" }}
      aria-label="Provider"
    >
      {providers.map((p) => (
        <option key={p.name} value={p.name}>
          {p.name}
        </option>
      ))}
    </select>
  );
}

// ------------------------------------------------------------- generate

function GenerateCard({
  defaultProvider,
  providers,
  onChanged,
  onError,
}: {
  defaultProvider: string | null;
  providers: AiProvider[];
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [source, setSource] = useState("");
  const [provider, setProvider] = useState(defaultProvider ?? "");
  const [busy, setBusy] = useState(false);
  const [items, setItems] = useState<GeneratedTestcase[] | null>(null);

  async function generate() {
    if (!source.trim()) return;
    setBusy(true);
    try {
      const data = await api.aiGenerate({ source: source.trim(), provider });
      setItems(data.testcases);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div className="card-head">
        <h3>Gerar test cases</h3>
        <span className="spacer" />
        <span className="caption">a partir de uma story (ST-XXXX) ou texto livre</span>
      </div>

      <div className="field wide" style={{ marginBottom: 16 }}>
        <label>Story ID ou descrição</label>
        <textarea
          value={source}
          onChange={(e) => setSource(e.target.value)}
          placeholder="ST-0001  —  ou cole os critérios de aceite / descrição da story"
          style={{ minHeight: 120 }}
          spellCheck={false}
        />
      </div>
      <div className="step-row">
        <ProviderSelect providers={providers} value={provider} onChange={setProvider} />
        <button className="primary" onClick={() => void generate()} disabled={busy || !source.trim()}>
          {busy ? "Gerando…" : "Gerar preview"}
        </button>
      </div>

      {items && (
        <PreviewList
          items={items}
          setItems={setItems}
          onChanged={onChanged}
          onError={onError}
        />
      )}
    </div>
  );
}

// ------------------------------------------------------- preview + accept

function PreviewList({
  items,
  setItems,
  onChanged,
  onError,
}: {
  items: GeneratedTestcase[];
  setItems: (items: GeneratedTestcase[]) => void;
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [folder, setFolder] = useState("ia");

  async function accept(item: GeneratedTestcase) {
    try {
      await api.createTestcase({
        title: item.title,
        type: item.type,
        priority: item.priority,
        tags: item.tags,
        folder,
        body: item.body,
      });
      setItems(items.filter((i) => i !== item));
      onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  function reject(item: GeneratedTestcase) {
    setItems(items.filter((i) => i !== item));
  }

  if (items.length === 0) {
    return (
      <p className="muted" style={{ marginTop: 16 }}>
        Nenhum item pendente — os aceitos viraram test cases; os rejeitados
        foram descartados (nada é gravado sem aceite).
      </p>
    );
  }

  return (
    <>
      <div className="step-row" style={{ marginTop: 16 }}>
        <span className="caption">
          {items.length} item(ns) em preview — nada foi gravado ainda
        </span>
        <span className="spacer" />
        <label className="caption">Pasta de destino</label>
        <input
          className="mono"
          value={folder}
          onChange={(e) => setFolder(e.target.value)}
          style={{ maxWidth: 160 }}
        />
      </div>
      {items.map((item, i) => (
        <div key={i} className="card" style={{ marginTop: 12, background: "var(--bg)" }}>
          <div className="card-head" style={{ marginBottom: 8 }}>
            <strong>{item.title}</strong>
            <span className="spacer" />
            <span className="caption mono">
              {item.type} · {item.priority}
              {item.tags.length > 0 ? ` · ${item.tags.join(", ")}` : ""}
            </span>
          </div>
          <DocBody text={item.body} />
          <div className="toolbar">
            <button className="primary" onClick={() => void accept(item)}>
              Aceitar (criar CT)
            </button>
            <button onClick={() => reject(item)}>Rejeitar</button>
          </div>
        </div>
      ))}
    </>
  );
}

// --------------------------------------------------------- review / negative

function ReviewCard({
  defaultProvider,
  providers,
  onChanged,
  onError,
}: {
  defaultProvider: string | null;
  providers: AiProvider[];
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [testcases, setTestcases] = useState<TestCase[]>([]);
  const [ctId, setCtId] = useState("");
  const [provider, setProvider] = useState(defaultProvider ?? "");
  const [busy, setBusy] = useState<"review" | "negative" | null>(null);
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [negatives, setNegatives] = useState<GeneratedTestcase[] | null>(null);

  useEffect(() => {
    api
      .testcases()
      .then((tcs) => {
        setTestcases(tcs);
        setCtId((old) => old || tcs[0]?.id || "");
      })
      .catch((e) => onError(e.message));
  }, [onError]);

  async function doReview() {
    if (!ctId) return;
    setBusy("review");
    setNegatives(null);
    try {
      setReview(await api.aiReview(ctId, { provider }));
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  async function doNegatives() {
    if (!ctId) return;
    setBusy("negative");
    setReview(null);
    try {
      const data = await api.aiNegativeCases(ctId, { provider });
      setNegatives(data.testcases);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div className="card-head">
        <h3>Revisar / casos negativos</h3>
        <span className="spacer" />
        <span className="caption">sobre um test case existente</span>
      </div>

      {testcases.length === 0 ? (
        <p className="muted">Nenhum test case no workspace para revisar.</p>
      ) : (
        <div className="step-row">
          <select
            value={ctId}
            onChange={(e) => setCtId(e.target.value)}
            style={{ maxWidth: 320, flex: "0 0 auto" }}
            aria-label="Test case"
          >
            {testcases.map((tc) => (
              <option key={tc.id} value={tc.id}>
                {tc.id} — {tc.title}
              </option>
            ))}
          </select>
          <ProviderSelect providers={providers} value={provider} onChange={setProvider} />
          <button onClick={() => void doReview()} disabled={busy !== null}>
            {busy === "review" ? "Revisando…" : "Revisar"}
          </button>
          <button onClick={() => void doNegatives()} disabled={busy !== null}>
            {busy === "negative" ? "Gerando…" : "Casos negativos"}
          </button>
        </div>
      )}

      {review && (
        <div style={{ marginTop: 16 }}>
          {review.summary && <p style={{ marginBottom: 8 }}>{review.summary}</p>}
          {review.issues.length === 0 ? (
            <div className="status-dot dot-active">Nenhum problema apontado.</div>
          ) : (
            <div className="table-wrap">
              <table className="dense">
                <thead>
                  <tr>
                    <th>Tipo</th>
                    <th>Passo</th>
                    <th>Mensagem</th>
                  </tr>
                </thead>
                <tbody>
                  {review.issues.map((issue, i) => (
                    <tr key={i}>
                      <td className="mono">{issue.kind}</td>
                      <td>{issue.step_index ?? "—"}</td>
                      <td>{issue.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {review.similar_considered.length > 0 && (
            <p className="caption" style={{ marginTop: 8 }}>
              Candidatos a duplicata considerados:{" "}
              {review.similar_considered.map((s) => s.id).join(", ")}
            </p>
          )}
        </div>
      )}

      {negatives && (
        <PreviewList
          items={negatives}
          setItems={setNegatives}
          onChanged={onChanged}
          onError={onError}
        />
      )}
    </div>
  );
}
