import { useEffect, useState } from "react";

const BASE = "/api/v1";

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data?.error?.message ?? `${resp.status}`);
  return data as T;
}

interface ProfileData {
  name: string;
  memory: string;
}

export function Profile({ onError }: { onError: (message: string) => void }) {
  const [name, setName] = useState("");
  const [memory, setMemory] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    json<ProfileData>(`${BASE}/profile`)
      .then((p) => {
        setName(p.name);
        setMemory(p.memory);
      })
      .catch((e) => onError(e.message));
  }, [onError]);

  async function save() {
    setSaving(true);
    try {
      await json(`${BASE}/profile`, {
        method: "PUT",
        body: JSON.stringify({ name, memory }),
      });
      setSaved(true);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Perfil</h1>
        <span className="spacer" />
        {saved && <span className="status-dot dot-active">salvo</span>}
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-head">
          <h3>Informações pessoais</h3>
        </div>
        <div className="field-grid">
          <div className="field col-6">
            <label>Nome</label>
            <input
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setSaved(false);
              }}
              placeholder="Seu nome"
            />
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-head">
          <h3>Memória de longo prazo para IA</h3>
          <span className="spacer" />
          <span className="caption">
            injetada em toda interação com IA, independente do modelo
          </span>
        </div>
        <p className="caption muted" style={{ marginBottom: 8 }}>
          Duas seções: <strong>Preferências &amp; Estilo</strong> (como você quer
          que a IA interaja) e <strong>Contexto Ativo</strong> (o que está em
          andamento). Mantenha vivo — o conteúdo é salvo em{" "}
          <span className="mono">profile.md</span> no seu workspace.
        </p>
        <textarea
          className="raw"
          style={{ minHeight: 320 }}
          value={memory}
          onChange={(e) => {
            setMemory(e.target.value);
            setSaved(false);
          }}
          spellCheck={false}
        />
      </div>

      <div className="toolbar">
        <button className="primary" onClick={() => void save()} disabled={saving}>
          {saving ? "Salvando…" : "Salvar perfil"}
        </button>
      </div>
    </div>
  );
}
