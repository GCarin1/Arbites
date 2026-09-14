"""Workspace service — estrutura de pastas, arbites.yaml, contadores, trash.

O filesystem é a fonte de verdade (ADR 0001). Este módulo nunca toca o
índice SQLite; ele só lê e escreve arquivos do workspace.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    "workspace": {
        "name": "Arbites",
        "id_prefixes": {
            "epic": "EP",
            "story": "ST",
            "testcase": "CT",
            "execution": "EXEC",
            "defect": "DF",
            "todo": "TD",
            "todolist": "TDL",
            "meeting": "MTG",
            "decision": "DEC",
            "audit": "AUD",
            "agent_event": "AGT",
        },
    },
    "automation_targets": [],
    "risk_repos": [],
    "squads": [],
    "ai": {"default_provider": None, "providers": []},
    # Observabilidade (ADR 0016): de onde puxar execução de CI que o Arbites
    # não disparou. Vazio = ninguém é vigiado; ingestão não inventa origem.
    "observability": {"sources": [], "max_runs_per_poll": 50},
    "audit": {},
    "requirements": {},
    "metric_thresholds": {},
    "health_score": {},
    "ci_monitoring": {},
}

# O arquivo ESCRITO na primeira execução (change 0167).
#
# Um `yaml.safe_dump` do dicionário acima produz um arquivo mudo: cinco chaves
# sem uma linha de explicação, enquanto o produto lê ONZE. Seis funcionalidades
# existiam e ninguém descobria — configuração que não aparece é configuração
# que não existe.
#
# Por isso o arquivo nasce de um template com comentários, e não de um dump.
# O risco de template e default divergirem é real: `test_config_padrao.py`
# compara os dois a cada execução da suíte.
CONFIG_TEMPLATE = """\
# Arbites — configuração do workspace.
#
# SEGREDO NÃO ENTRA AQUI. Este arquivo é versionável e feito para ser
# compartilhado com o time: chave de IA e token do GitHub vão para o cofre do
# sistema operacional ou para o `.env` do processo (ADRs 0008 e 0017).
#
# Tudo abaixo é opcional: um bloco vazio ou ausente usa o default indicado.

workspace:
  name: Arbites
  # Prefixo de ID por tipo de artefato. Mudar depois NÃO renomeia o que já
  # existe — o ID mora no frontmatter de cada arquivo (ADR 0002).
  id_prefixes:
    epic: EP
    story: ST
    testcase: CT
    execution: EXEC
    defect: DF
    todo: TD
    todolist: TDL
    meeting: MTG
    decision: DEC
    audit: AUD
    agent_event: AGT

# Squads declarados. A lista alimenta os filtros; um squad usado num artefato
# e não declarado aqui continua funcionando, só não aparece como sugestão.
squads: []

# Projetos de automação que esta instância roda ou acompanha.
# O bloco `github` é lido pelo disparo e pela coleta por artifact.
automation_targets: []
#   - name: frontend-web
#     kind: behave
#     local_path: /home/voce/repos/qa-automation
#     features_glob: features/**/*.feature
#     github:
#       repo: org/qa-automation
#       workflow: qa-nightly.yml
#       ref: main
#       artifact_name: cucumber-report

# Repositórios para o mapa de risco (quais casos um diff afeta por
# correlação). Vazio = a correlação por risco não é oferecida.
risk_repos: []

# Provedores de IA. A CHAVE de cada um vai para o cofre do SO pela tela
# IA → Providers, nunca para este arquivo.
ai:
  default_provider: null
  providers: []
#   - name: openai
#     kind: openai_compatible
#     model: gpt-4o-mini
#   - name: local
#     kind: openai_compatible
#     model: llama3
#     base_url: http://127.0.0.1:11434/v1

# Observabilidade (ADR 0016): de onde PUXAR execução de CI que o Arbites não
# disparou. Vazio = ninguém é vigiado; a ingestão não inventa origem.
observability:
  sources: []
#     - provider: github
#       repo: org/qa-automation
#       workflow: qa-nightly.yml
#       artifact: observabilidade
  max_runs_per_poll: 50
  # Direção e meta de cada sinal. Sem isto o Arbites diz que o sinal SUBIU,
  # nunca que piorou: ele não sabe que lcp_ms maior é pior.
#   goals:
#     lcp_ms: { direction: lower, goal: 2500 }
#     success_rate: { goal: 95 }
  # Sinal é barato e faz a série; anexo é caro e só interessa perto do
  # evento. Defaults: 730 e 90 dias.
#   retention:
#     signals_days: 730
#     attachments_days: 90

# Rodadas de auditoria. Uma nova é disparada quando a última passou deste
# intervalo — inclusive só por alguém abrir a aba. Default: 24.
audit: {}
#   auto_interval_hours: 24

# Lint de critérios EARS. Sem `vague_terms`, vale a lista embutida
# ("rápido", "adequado", "fácil"...).
requirements: {}
#   vague_terms: [rápido, adequado, fácil]

# Semáforo das métricas do dashboard: {warn, bad, direction}.
# `direction: up` = maior é melhor (default); `down` = menor é melhor.
metric_thresholds: {}
#   pass_rate: { warn: 90, bad: 75 }
#   blocked_rate: { warn: 5, bad: 15, direction: down }

# Pesos da nota de saúde. São renormalizados para somar 1.0.
# Defaults: coverage 0.30, defects 0.25, automation 0.25, debt 0.20.
health_score: {}
#   weights:
#     coverage: 0.30
#     defects: 0.25
#     automation: 0.25
#     debt: 0.20

# Como reconhecer uma execução vinda de CI pelo NOME, para separá-la das
# manuais nos relatórios. Vazio = nenhuma separação.
ci_monitoring: {}
#   name_pattern: "^CI "
"""

SUBDIRS = [
    "requirements", "testcases", "executions", "defects", "todos",
    "dailies", "metrics", "meetings", "decisions", "audits", "agent_log",
    "todolists", "ci", ".arbites",
]

# Sidecar da lixeira (0081): guarda a origem para o restore devolver ao lugar.
_TRASH_META_SUFFIX = ".arbtrash"
# Fallback de pasta por prefixo de ID quando a origem não foi registrada
# (itens da lixeira anteriores ao 0081).
_PREFIX_FOLDER = {
    "CT": "testcases", "EP": "requirements", "ST": "requirements",
    "DF": "defects", "TD": "todos", "TDL": "todolists",
    "DEC": "decisions", "AUD": "audits",
    "AGT": "agent_log", "EXEC": "executions", "MTG": "meetings",
}


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "sem-titulo"


class Workspace:
    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(root).resolve()

    # -- bootstrap -----------------------------------------------------

    def ensure(self) -> None:
        """Garante a estrutura mínima; primeira execução sem fricção."""
        self.root.mkdir(parents=True, exist_ok=True)
        for sub in SUBDIRS:
            (self.root / sub).mkdir(exist_ok=True)
        if not self.config_path.exists():
            # O template comentado, não um dump mudo do dicionário: o arquivo
            # é a única documentação que a pessoa encontra sem procurar.
            self.config_path.write_text(CONFIG_TEMPLATE, encoding="utf-8")
        if not self.counters_path.exists():
            self._write_counters({})

    # -- paths ---------------------------------------------------------

    @property
    def config_path(self) -> Path:
        return self.root / "arbites.yaml"

    @property
    def arbites_dir(self) -> Path:
        return self.root / ".arbites"

    @property
    def counters_path(self) -> Path:
        return self.arbites_dir / "counters.json"

    @property
    def index_db_path(self) -> Path:
        return self.arbites_dir / "index.db"

    @property
    def trash_dir(self) -> Path:
        return self.arbites_dir / "trash"

    def relpath(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.resolve().relative_to(self.root).as_posix()

    # -- config --------------------------------------------------------

    def config(self) -> dict[str, Any]:
        return yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}

    def id_prefixes(self) -> dict[str, str]:
        cfg = self.config()
        prefixes = dict(DEFAULT_CONFIG["workspace"]["id_prefixes"])
        prefixes.update((cfg.get("workspace") or {}).get("id_prefixes") or {})
        return prefixes

    # -- counters (IDs sequenciais por prefixo) -------------------------

    def _read_counters(self) -> dict[str, int]:
        try:
            return json.loads(self.counters_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _write_counters(self, counters: dict[str, int]) -> None:
        self.counters_path.parent.mkdir(parents=True, exist_ok=True)
        self.counters_path.write_text(
            json.dumps(counters, indent=2), encoding="utf-8"
        )

    def next_id(self, kind: str) -> str:
        """Consome o contador do prefixo e devolve o próximo ID (ex.: CT-0007)."""
        prefix = self.id_prefixes()[kind]
        counters = self._read_counters()
        n = counters.get(prefix, 1)
        counters[prefix] = n + 1
        self._write_counters(counters)
        return f"{prefix}-{n:04d}"

    def bump_counter_to(self, prefix: str, seen_max: int) -> None:
        """Ajusta o contador para max(existente)+1 (arquivos criados à mão)."""
        counters = self._read_counters()
        if counters.get(prefix, 1) <= seen_max:
            counters[prefix] = seen_max + 1
            self._write_counters(counters)

    # -- trash ----------------------------------------------------------

    def trash(self, path: Path) -> Path:
        """Move um arquivo/pasta para .arbites/trash/ — nunca apaga direto.

        Registra um sidecar `<nome>.arbtrash` com a origem (caminho relativo)
        e a data de moção, para o restore devolver ao lugar certo (0081)."""
        self.trash_dir.mkdir(parents=True, exist_ok=True)
        origin = self.relpath(path)
        dest = self.trash_dir / path.name
        i = 1
        while dest.exists():
            dest = self.trash_dir / f"{path.stem}-{i}{path.suffix}"
            i += 1
        shutil.move(str(path), str(dest))
        (self.trash_dir / (dest.name + _TRASH_META_SUFFIX)).write_text(
            json.dumps({
                "origin": origin,
                "trashed_at": datetime.now(timezone.utc).isoformat(),
            }),
            encoding="utf-8",
        )
        return dest

    def _trash_meta(self, entry: Path) -> dict:
        side = self.trash_dir / (entry.name + _TRASH_META_SUFFIX)
        if side.exists():
            try:
                return json.loads(side.read_text(encoding="utf-8"))
            except ValueError:
                return {}
        return {}

    def list_trash(self) -> list[dict]:
        """Itens na lixeira, mais recentes primeiro — nome, origem, data,
        tipo (inferido da origem ou do prefixo do ID)."""
        if not self.trash_dir.exists():
            return []
        out = []
        for entry in self.trash_dir.iterdir():
            if entry.name.endswith(_TRASH_META_SUFFIX):
                continue
            meta = self._trash_meta(entry)
            origin = meta.get("origin")
            kind = (origin.split("/", 1)[0] if origin
                    else _PREFIX_FOLDER.get(entry.name.split("-", 1)[0], "?"))
            out.append({
                "name": entry.name,
                "origin": origin,
                "trashed_at": meta.get("trashed_at"),
                "kind": kind,
                "is_dir": entry.is_dir(),
            })
        out.sort(key=lambda e: e.get("trashed_at") or "", reverse=True)
        return out

    def restore(self, name: str) -> Path:
        """Devolve o item ao caminho de origem (ou à pasta do tipo, se a
        origem não foi registrada). Sufixa em caso de colisão; nunca
        sobrescreve. Retorna o caminho restaurado."""
        entry = self.trash_dir / name
        if not entry.exists() or name.endswith(_TRASH_META_SUFFIX):
            raise FileNotFoundError(name)
        origin = self._trash_meta(entry).get("origin")
        if origin:
            target = self.root / origin
        else:
            folder = _PREFIX_FOLDER.get(name.split("-", 1)[0], "")
            target = self.root / folder / name if folder else self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        final = target
        i = 1
        while final.exists():
            final = target.with_name(f"{target.stem}-{i}{target.suffix}")
            i += 1
        shutil.move(str(entry), str(final))
        side = self.trash_dir / (name + _TRASH_META_SUFFIX)
        if side.exists():
            side.unlink()
        return final

    def empty_trash(self) -> int:
        """Esvazia a lixeira (apaga de vez). Retorna quantos itens removeu."""
        if not self.trash_dir.exists():
            return 0
        removed = 0
        for entry in list(self.trash_dir.iterdir()):
            if entry.name.endswith(_TRASH_META_SUFFIX):
                entry.unlink(missing_ok=True)
                continue
            if entry.is_dir():
                shutil.rmtree(entry, ignore_errors=True)
            else:
                entry.unlink(missing_ok=True)
            removed += 1
        return removed
