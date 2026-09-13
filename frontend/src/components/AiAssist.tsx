import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { SingleRefInput } from "./Autocomplete";
import { DocBody } from "./ReadView";
import { useToast } from "./Toast";
import type {
  AiProvider,
  AiProvidersInfo,
  Criterion,
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

type AiTab = "gerar" | "revisar" | "pack" | "config";

const AI_TABS: [AiTab, string][] = [
  ["gerar", "Gerar"],
  ["revisar", "Revisar"],
  ["pack", "Context Pack"],
  ["config", "Configuração"],
];

export function AiAssist({
  onChanged,
  onError,
}: {
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [info, setInfo] = useState<AiProvidersInfo | null>(null);
  // Reformulação (0078): sub-abas Gerar · Revisar · Context Pack ·
  // Configuração (config deixa de dividir espaço com o trabalho) + seletor de
  // provider ÚNICO no cabeçalho, usado por gerar/revisar/negativos.
  const [tab, setTab] = useState<AiTab>("gerar");
  const [provider, setProvider] = useState("");

  const load = useCallback(() => {
    api
      .aiProviders()
      .then(setInfo)
      .catch((e) => onError(e.message));
  }, [onError]);

  useEffect(() => {
    load();
  }, [load]);

  // provider global segue o padrão até o usuário trocar
  useEffect(() => {
    if (info?.default_provider) setProvider((old) => old || info.default_provider!);
  }, [info]);

  const enabled = !!info?.default_provider;
  const work = tab === "gerar" || tab === "revisar";

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Assistente de IA</h1>
        <span className="spacer" />
        <span className={`status-dot ${enabled ? "dot-active" : "dot-draft"}`}>
          {enabled ? `ativo · ${info?.default_provider}` : "desabilitada"}
        </span>
        {enabled && info && work && (
          <ProviderSelect providers={info.providers} value={provider} onChange={setProvider} />
        )}
      </div>

      <div className="tab-bar block" role="tablist">
        {AI_TABS.map(([key, label]) => (
          <button
            key={key}
            role="tab"
            aria-selected={tab === key}
            className={`tab-btn ${tab === key ? "active" : ""}`}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {!enabled && work && (
        <div className="empty-state block">
          <div className="empty-title">IA desabilitada</div>
          <div className="empty-body">
            A plataforma é 100% funcional sem IA. Configure ao menos um provider
            na aba{" "}
            <button type="button" className="link-chip link-chip-btn" onClick={() => setTab("config")}>
              Configuração
            </button>{" "}
            para habilitar geração, revisão e casos negativos. O Context Pack
            funciona sem provider.
          </div>
        </div>
      )}

      {enabled && work && <AssistContextCard />}

      {tab === "gerar" && enabled && (
        <GenerateCard provider={provider} onChanged={onChanged} onError={onError} />
      )}
      {tab === "revisar" && enabled && (
        <ReviewCard provider={provider} onChanged={onChanged} onError={onError} />
      )}
      {tab === "pack" && <ContextPackCard />}
      {tab === "config" && <ProvidersCard info={info} onSaved={load} onError={onError} />}

      {enabled && work && <AssistHistoryCard />}
    </div>
  );
}

// -------------------------------------------------- contexto ativo (0066)

/** Remove comentários HTML, headings e itens vazios — sobra texto real? */
function memoryFilled(memory: string): boolean {
  return (
    memory
      .replace(/<!--[\s\S]*?-->/g, "")
      .replace(/^#+ .*$/gm, "")
      .replace(/^\s*-\s*$/gm, "")
      .trim().length > 0
  );
}

/**
 * O que a IA vai receber junto do próximo pedido (0066): memória do perfil,
 * recap de decisões aceitas + lições recentes (capability project-memory) e
 * lições por similaridade quando o pedido casa. O usuário vê POR QUE a IA
 * responde melhor conforme o projeto cresce.
 */
function AssistContextCard() {
  const [profileOn, setProfileOn] = useState<boolean | null>(null);
  const [decisionCount, setDecisionCount] = useState<number | null>(null);
  const [lessonCount, setLessonCount] = useState<number | null>(null);

  useEffect(() => {
    let alive = true;
    api.profile().then((p) => alive && setProfileOn(memoryFilled(p.memory))).catch(() => {});
    api
      .decisions("?status=accepted")
      .then((d) => alive && setDecisionCount(d.length))
      .catch(() => {});
    api
      .defects("?has_lesson=true")
      .then((d) => alive && setLessonCount(d.length))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

  const dot = (on: boolean | null) =>
    on === null ? "dot-col-pending" : on ? "dot-col-passed" : "dot-col-pending";

  return (
    <div className="card block">
      <div className="card-head">
        <h3>Contexto ativo</h3>
        <span className="spacer" />
        <span className="caption muted">o que acompanha cada pedido à IA</span>
      </div>
      <div className="assist-context">
        <span className={`status-dot ${dot(profileOn)}`}>
          memória do perfil {profileOn ? "preenchida" : "vazia (aba Perfil)"}
        </span>
        <span className={`status-dot ${dot((decisionCount ?? 0) > 0)}`}>
          {decisionCount ?? "…"} decisão{decisionCount === 1 ? "" : "ões"} aceita
          {decisionCount === 1 ? "" : "s"} no recap
        </span>
        <span className={`status-dot ${dot((lessonCount ?? 0) > 0)}`}>
          {lessonCount ?? "…"} lição{lessonCount === 1 ? "" : "ões"} aprendida
          {lessonCount === 1 ? "" : "s"} (injetadas por similaridade)
        </span>
      </div>
    </div>
  );
}

/** Histórico de interações de IA — reutiliza os agent_events da capability
 * project-memory (`GET /memory/timeline?kinds=agent`), sem endpoint novo. */
function AssistHistoryCard() {
  const [events, setEvents] = useState<
    { at: string; id: string; title: string; summary: string }[]
  >([]);

  useEffect(() => {
    let alive = true;
    api
      .memoryTimeline("agent", 10)
      .then((rows) => alive && setEvents(rows))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

  if (events.length === 0) return null;

  return (
    <div className="card block">
      <div className="card-head">
        <h3>Histórico de interações</h3>
        <span className="spacer" />
        <span className="caption muted">o que a IA gerou/revisou (Memória do Projeto)</span>
      </div>
      {events.map((e, i) => (
        <div key={`${e.id}-${i}`} className="exec-item">
          <span className="caption mono muted">
            {(() => {
              try {
                return new Date(e.at).toLocaleString();
              } catch {
                return e.at;
              }
            })()}
          </span>
          <span className="exec-item-msg">{e.summary}</span>
          {e.title && <span className="caption muted">{e.title}</span>}
        </div>
      ))}
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
  // resultado do teste por provider (0085): "busy" | {ok, error}
  const [tests, setTests] = useState<Record<string, "busy" | { ok: boolean; error: string | null }>>({});

  // form de novo provider
  const [name, setName] = useState("");
  const [kind, setKind] = useState("openai_compatible");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [newKey, setNewKey] = useState("");

  async function testSaved(pName: string) {
    setTests((t) => ({ ...t, [pName]: "busy" }));
    try {
      // se o usuário digitou uma chave nova ainda não salva, testa inline
      const pending = keys[pName];
      const p = providers.find((x) => x.name === pName);
      const body = pending && p
        ? { kind: p.kind, model: p.model, base_url: p.base_url, key: pending }
        : { name: pName };
      const r = await api.aiProviderTest(body);
      setTests((t) => ({ ...t, [pName]: r }));
    } catch (e) {
      setTests((t) => ({ ...t, [pName]: { ok: false, error: e instanceof Error ? e.message : String(e) } }));
    }
  }

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
    // Inclui o provider digitado no formulário mesmo sem clicar "Adicionar à
    // lista" — senão o usuário preenche, salva e nada persiste.
    let effProviders = providers;
    let effKeys = keys;
    let effDefault = defaultProvider;
    if (name.trim()) {
      const pending: AiProvider = {
        name: name.trim(),
        kind,
        model: model.trim(),
        base_url: baseUrl.trim() || null,
        key_configured: false,
      };
      effProviders = [...providers.filter((p) => p.name !== pending.name), pending];
      if (newKey.trim()) effKeys = { ...keys, [pending.name]: newKey.trim() };
      if (!effDefault) effDefault = pending.name;
    }
    try {
      const updated = await api.putAiProviders({
        default_provider: effDefault,
        providers: effProviders.map((p) => ({
          name: p.name,
          kind: p.kind,
          model: p.model,
          base_url: p.base_url,
        })),
        keys: effKeys,
      });
      setKeys({});
      setName("");
      setModel("");
      setBaseUrl("");
      setNewKey("");
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
    <div className="card block">
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
                    <div className="step-row" style={{ gap: 6 }}>
                      <button
                        className="btn-sm"
                        onClick={() => void testSaved(p.name)}
                        disabled={tests[p.name] === "busy"}
                      >
                        {tests[p.name] === "busy" ? "Testando…" : "Testar"}
                      </button>
                      {tests[p.name] && tests[p.name] !== "busy" && (
                        <span
                          className={`status-dot ${
                            (tests[p.name] as { ok: boolean }).ok ? "dot-active" : "dot-draft"
                          } caption`}
                          title={(tests[p.name] as { error: string | null }).error ?? "respondeu ok"}
                        >
                          {(tests[p.name] as { ok: boolean }).ok ? "ok" : "falhou"}
                        </span>
                      )}
                      <button className="btn-sm danger" onClick={() => removeProvider(p.name)}>
                        Remover
                      </button>
                    </div>
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
        <span className="caption muted">
          preencha acima e salve — o provider é incluído automaticamente
        </span>
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
  provider,
  onChanged,
  onError,
}: {
  provider: string;
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [source, setSource] = useState("");
  const [busy, setBusy] = useState(false);
  const [items, setItems] = useState<GeneratedTestcase[] | null>(null);
  const [previewStory, setPreviewStory] = useState<string | null>(null);
  const [lessonsUsed, setLessonsUsed] = useState<{ id: string; title: string }[]>([]);
  // geração por critério (0093): se `source` é uma story com critérios EARS
  const [criteria, setCriteria] = useState<Criterion[]>([]);
  const [selCrit, setSelCrit] = useState<Set<string>>(new Set());

  // detecta um ID de story digitado e busca seus critérios EARS
  const storyId = /^\s*(ST-\d+)\s*$/i.exec(source)?.[1]?.toUpperCase() ?? null;
  useEffect(() => {
    if (!storyId) {
      setCriteria([]);
      setSelCrit(new Set());
      return;
    }
    let alive = true;
    api
      .requirementCriteria(storyId)
      .then((c) => alive && setCriteria(c))
      .catch(() => alive && setCriteria([]));
    return () => {
      alive = false;
    };
  }, [storyId]);

  async function generate(useCriteria: boolean) {
    if (!source.trim()) return;
    setBusy(true);
    try {
      const data = await api.aiGenerate({
        source: source.trim(),
        provider,
        ...(useCriteria ? { criteria: [...selCrit] } : {}),
      });
      setItems(data.testcases);
      setPreviewStory(data.story ?? null);
      setLessonsUsed(data.lessons_used ?? []);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card block">
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
        {!source.trim() && (
          <p className="caption muted" style={{ marginTop: 4 }}>
            Ex.: digite o ID de uma story (o corpo dela vira o insumo) —{" "}
            <button
              type="button"
              className="link-chip link-chip-btn"
              onClick={() =>
                setSource(
                  "Como usuário quero recuperar minha senha por e-mail.\n\n" +
                    "Critérios de aceite:\n" +
                    "- Informar e-mail cadastrado envia link de redefinição\n" +
                    "- Link expira em 30 minutos\n" +
                    "- E-mail não cadastrado mostra mensagem genérica",
                )
              }
            >
              usar exemplo
            </button>
          </p>
        )}
      </div>
      {criteria.length > 0 && (
        <div className="field wide" style={{ marginBottom: 12 }}>
          <label>Critérios EARS da story — gerar CTs por critério (vínculo automático)</label>
          <div className="criteria-picker">
            {criteria.map((c) => {
              const checked = selCrit.has(c.ears_id);
              return (
                <label key={c.ears_id} className="check-inline caption">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() =>
                      setSelCrit((old) => {
                        const next = new Set(old);
                        if (next.has(c.ears_id)) next.delete(c.ears_id);
                        else next.add(c.ears_id);
                        return next;
                      })
                    }
                  />
                  <span className="mono">{c.ears_id}</span>
                  <span className="muted">{c.text}</span>
                </label>
              );
            })}
          </div>
        </div>
      )}
      <div className="step-row">
        <button className="primary" onClick={() => void generate(false)} disabled={busy || !source.trim()}>
          {busy ? "Gerando…" : "Gerar preview"}
        </button>
        {criteria.length > 0 && (
          <button
            onClick={() => void generate(true)}
            disabled={busy || selCrit.size === 0}
            title="Um CT por critério selecionado, com o vínculo já preenchido"
          >
            {busy ? "Gerando…" : `Gerar por critério (${selCrit.size})`}
          </button>
        )}
      </div>

      {lessonsUsed.length > 0 && (
        <p className="caption muted" style={{ marginTop: 12 }}>
          Considerou {lessonsUsed.length} lição{lessonsUsed.length === 1 ? "" : "ões"} aprendida
          {lessonsUsed.length === 1 ? "" : "s"} de defeitos anteriores:{" "}
          {lessonsUsed.map((l) => l.id).join(", ")}
        </p>
      )}

      {items && (
        <PreviewList
          items={items}
          setItems={setItems}
          story={previewStory}
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
  story,
  onChanged,
  onError,
}: {
  items: GeneratedTestcase[];
  setItems: (items: GeneratedTestcase[]) => void;
  story?: string | null;
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
        // vínculo fino quando gerado por critério (0093)
        ...(story ? { story } : {}),
        ...(item.criteria?.length ? { criteria: item.criteria } : {}),
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
        <span className="status-dot dot-col-in_progress caption">
          {items.length} item(ns) em PREVIEW — nada foi gravado; aceite item a item
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
            {item.criteria?.length ? (
              <span className="status-dot dot-col-passed caption" style={{ marginLeft: 8 }}>
                {item.criteria.join(", ")}
              </span>
            ) : null}
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
  provider,
  onChanged,
  onError,
}: {
  provider: string;
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [testcases, setTestcases] = useState<TestCase[]>([]);
  const [ctId, setCtId] = useState("");
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
    <div className="card block">
      <div className="card-head">
        <h3>Revisar / casos negativos</h3>
        <span className="spacer" />
        <span className="caption">sobre um test case existente</span>
      </div>

      {testcases.length === 0 ? (
        <p className="muted">Nenhum test case no workspace para revisar.</p>
      ) : (
        <div className="step-row">
          <div style={{ maxWidth: 320, flex: "0 0 auto" }}>
            <SingleRefInput
              value={ctId}
              onChange={setCtId}
              kinds="testcase"
              placeholder="CT-… (digite id ou título)"
            />
          </div>
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

// ------------------------------------------------------------ context pack

interface PackPreview {
  counts: { requirements: number; testcases: number; defects: number; decisions: number };
  bytes: number;
  markdown: string;
}

/**
 * Context Pack — bundle Markdown único (requisitos + CTs + defeitos +
 * decisões de um escopo) pronto para colar num agente de IA externo
 * (Cursor, Claude Code, Codex, Roo Code, Aider, etc.). Não depende de um
 * provider de IA configurado no Arbites — é um export, não uma chamada.
 *
 * Reformulado (0079): escopo obrigatório, mas os campos LISTAM os itens
 * reais (datalist filtra ao digitar); toggles de seção; preview com
 * contagens + Copiar/Baixar (download client-side do markdown buscado).
 */
function ContextPackCard() {
  const { toast } = useToast();
  const [squads, setSquads] = useState<string[]>([]);
  const [epic, setEpic] = useState("");
  const [story, setStory] = useState("");
  const [squad, setSquad] = useState("");
  const [inclTc, setInclTc] = useState(true);
  const [inclLast, setInclLast] = useState(false);
  const [inclDef, setInclDef] = useState(true);
  const [inclDec, setInclDec] = useState(true);
  const [pack, setPack] = useState<PackPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [layout, setLayout] = useState("agents-md"); // Pacote de Agente (0094)

  useEffect(() => {
    api.squads().then((d) => setSquads(d.squads)).catch(() => {});
  }, []);

  const hasScope = !!(epic.trim() || story.trim() || squad.trim());

  const params = useMemo(() => {
    const p: Record<string, string> = {};
    if (epic.trim()) p.epic = epic.trim();
    if (story.trim()) p.story = story.trim();
    if (squad.trim()) p.squad = squad.trim();
    p.testcases = String(inclTc);
    p.defects = String(inclDef);
    p.decisions = String(inclDec);
    p.last_result = String(inclTc && inclLast);
    return p;
  }, [epic, story, squad, inclTc, inclLast, inclDef, inclDec]);

  // preview debounced — só quando há escopo (o backend exige ao menos um)
  useEffect(() => {
    if (!hasScope) {
      setPack(null);
      return;
    }
    let alive = true;
    setLoading(true);
    const timer = setTimeout(() => {
      api
        .contextPack(params)
        .then((d) => alive && setPack(d))
        .catch(() => alive && setPack(null))
        .finally(() => alive && setLoading(false));
    }, 300);
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [params, hasScope]);

  function download() {
    if (!pack) return;
    const blob = new Blob([pack.markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "context-pack.md";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function copy() {
    if (!pack) return;
    try {
      await navigator.clipboard.writeText(pack.markdown);
      toast("Context Pack copiado", "success");
    } catch {
      toast("Não foi possível copiar", "error");
    }
  }

  const counts = pack?.counts;
  const kb = pack ? (pack.bytes / 1024).toFixed(1) : "0";
  const empty = !!counts && counts.requirements === 0;

  return (
    <div className="card block">
      <div className="card-head">
        <h3>Context Pack</h3>
        <span className="spacer" />
        <span className="caption">bundle para agentes de IA externos (Cursor, Claude Code, etc.)</span>
      </div>
      <p className="muted caption">
        Exporta requisitos, casos de teste, defeitos (com causa raiz/correção)
        e decisões arquiteturais de um escopo, num único Markdown para colar
        num agente externo. Escolha ao menos um escopo — epic, story ou squad.
      </p>
      <div className="field-grid">
        <div className="field col-4">
          <label htmlFor="cp-epic">Epic</label>
          <SingleRefInput
            id="cp-epic"
            value={epic}
            onChange={setEpic}
            kinds="requirement"
            placeholder="EP-… (digite id ou título)"
          />
        </div>
        <div className="field col-4">
          <label htmlFor="cp-story">Story</label>
          <SingleRefInput
            id="cp-story"
            value={story}
            onChange={setStory}
            kinds="requirement"
            placeholder="ST-… (digite id ou título)"
          />
        </div>
        <div className="field col-4">
          <label htmlFor="cp-squad">Squad</label>
          <input
            id="cp-squad"
            list="cp-squads"
            value={squad}
            onChange={(e) => setSquad(e.target.value)}
            placeholder="squad (digite para filtrar)"
          />
          <datalist id="cp-squads">
            {squads.map((s) => (
              <option key={s} value={s} />
            ))}
          </datalist>
        </div>
      </div>

      <div className="step-row" style={{ flexWrap: "wrap" }}>
        <span className="caption muted">Incluir:</span>
        <label className="check-inline caption">
          <input type="checkbox" checked={inclTc} onChange={() => setInclTc((v) => !v)} />
          Casos de teste
        </label>
        <label className="check-inline caption" style={{ opacity: inclTc ? 1 : 0.5 }}>
          <input
            type="checkbox"
            checked={inclTc && inclLast}
            disabled={!inclTc}
            onChange={() => setInclLast((v) => !v)}
          />
          Último resultado por CT
        </label>
        <label className="check-inline caption">
          <input type="checkbox" checked={inclDef} onChange={() => setInclDef((v) => !v)} />
          Defeitos
        </label>
        <label className="check-inline caption">
          <input type="checkbox" checked={inclDec} onChange={() => setInclDec((v) => !v)} />
          Decisões
        </label>
      </div>

      {!hasScope ? (
        <p className="field-error caption" style={{ marginTop: 8 }}>
          Escolha ao menos um escopo (epic, story ou squad) para montar o pack.
        </p>
      ) : loading ? (
        <p className="empty">Montando preview…</p>
      ) : pack && counts ? (
        <>
          <div className="step-row" style={{ marginTop: 8 }}>
            <span className="caption">
              Inclui: {counts.requirements} requisito(s) · {counts.testcases} CT(s) ·{" "}
              {counts.defects} defeito(s) · {counts.decisions} decisão(ões) · ~{kb} KB
            </span>
            <span className="spacer" />
            <button onClick={() => void copy()} disabled={empty}>
              Copiar
            </button>
            <button className="primary" onClick={download} disabled={empty}>
              Baixar .md
            </button>
          </div>
          {empty ? (
            <p className="muted caption">
              Nenhum requisito nesse escopo — ajuste o filtro.
            </p>
          ) : (
            <pre className="run-log" style={{ maxHeight: 260 }}>{pack.markdown}</pre>
          )}
        </>
      ) : null}

      {/* Pacote de Agente (0094): mesmo escopo, saída em formato REPOSITÓRIO */}
      <div className="block" style={{ borderTop: "1px solid var(--border)", paddingTop: "var(--s2)" }}>
        <div className="card-head">
          <h4 className="section-title" style={{ margin: 0 }}>Pacote de Agente</h4>
          <span className="spacer" />
          <span className="caption muted">
            AGENTS.md + skills + specs do escopo, pronto para colar num repositório
          </span>
        </div>
        <p className="muted caption">
          Gera um .zip com <span className="mono">AGENTS.md</span> (convenções =
          decisões aceitas), <span className="mono">skills/</span> (uma por lição
          de defeito com causa raiz) e <span className="mono">specs/</span> (story
          + CTs BDD).
        </p>
        <div className="step-row" style={{ flexWrap: "wrap" }}>
          <label className="caption memory-filter">
            Layout
            <select value={layout} onChange={(e) => setLayout(e.target.value)}>
              <option value="agents-md">AGENTS.md (padrão aberto)</option>
              <option value="claude">Claude (.claude/skills)</option>
            </select>
          </label>
          <span className="spacer" />
          {hasScope ? (
            <a
              className="button-link"
              href={api.agentPackUrl({
                ...(epic.trim() ? { epic: epic.trim() } : {}),
                ...(story.trim() ? { story: story.trim() } : {}),
                ...(squad.trim() ? { squad: squad.trim() } : {}),
                layout,
              })}
              download
            >
              Baixar pacote .zip
            </a>
          ) : (
            <button disabled title="Escolha ao menos um escopo acima">
              Baixar pacote .zip
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
