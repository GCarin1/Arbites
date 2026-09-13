import { useEffect, useRef, useState } from "react";
import { ActivityHeatmap } from "./ActivityHeatmap";
import { AccountAvatar, bumpAvatarVersion } from "./AccountMenu";
import {
  DENSITIES,
  DENSITY_LABELS,
  loadDensity,
  saveDensity,
  type Density,
} from "../density";
import { api } from "../api";
import type { SessionUser } from "../types";

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

export function Profile({
  user,
  onError,
}: {
  user: SessionUser;
  onError: (message: string) => void;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [avatarBusy, setAvatarBusy] = useState(false);
  const [density, setDensity] = useState<Density>(loadDensity);
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

  async function pickAvatar(file: File | undefined) {
    if (!file) return;
    setAvatarBusy(true);
    try {
      await api.putAvatar(file);
      bumpAvatarVersion();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setAvatarBusy(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function removeAvatar() {
    setAvatarBusy(true);
    try {
      await api.deleteAvatar();
      bumpAvatarVersion();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setAvatarBusy(false);
    }
  }

  return (
    <div className="content-narrow">
      <div className="page-head">
        <h1 className="page-title">Perfil</h1>
        <span className="spacer" />
        {saved && <span className="status-dot dot-active">salvo</span>}
      </div>

      <div className="card block">
        <div className="card-head">
          <h3>Informações pessoais</h3>
        </div>
        <div className="avatar-editor">
          <AccountAvatar user={user} size={72} />
          <div>
            <p className="caption muted">
              Sem foto, a conta usa um identicon desenhado a partir do e-mail —
              determinístico e gerado aqui mesmo, sem chamar serviço externo.
              PNG, JPEG ou WebP de até 1 MB.
            </p>
            <div className="toolbar">
              <input
                ref={fileInput}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                style={{ display: "none" }}
                onChange={(e) => void pickAvatar(e.target.files?.[0])}
              />
              <button
                onClick={() => fileInput.current?.click()}
                disabled={avatarBusy}
              >
                {avatarBusy ? "Enviando…" : "Trocar foto"}
              </button>
              <button onClick={() => void removeAvatar()} disabled={avatarBusy}>
                Voltar ao identicon
              </button>
            </div>
          </div>
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

      <div className="card block">
        <div className="card-head">
          <h3>Densidade de leitura</h3>
          <span className="spacer" />
          <span className="caption muted">
            vale neste navegador — é como você lê, não como o time trabalha
          </span>
        </div>
        <p className="caption muted" style={{ marginBottom: "var(--s1)" }}>
          Muda o respiro das linhas e a altura dos controles nas telas de
          lista, árvore e quadro. A separação entre seções não muda: encolhê-la
          não faz caber mais nada.
        </p>
        <div className="toolbar" role="radiogroup" aria-label="Densidade de leitura">
          {DENSITIES.map((option) => (
            <button
              key={option}
              className={option === density ? "primary" : ""}
              role="radio"
              aria-checked={option === density}
              onClick={() => {
                setDensity(option);
                saveDensity(option);
              }}
            >
              {DENSITY_LABELS[option]}
            </button>
          ))}
        </div>
      </div>

      <ActivityHeatmap onError={onError} />

      <div className="card block">
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
