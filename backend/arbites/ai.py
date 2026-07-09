"""IA opcional (M5) — providers, schemas e funções de geração/revisão.

Princípio 4 do intake: a plataforma é 100% funcional sem nenhum provider.
Toda saída de IA é preview — este módulo NUNCA escreve no workspace; o
aceite de um item é o POST /testcases normal, disparado pelo usuário.

Três classes cobrem os 7 providers do intake §12: OpenAICompatible
(OpenAI, OpenRouter, Ollama, LM Studio, vLLM — muda só a base_url),
AnthropicProvider e GeminiProvider. Chaves no keyring (ADR 0008).
"""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

AI_KEYRING_SERVICE = "arbites-ai"


class AIProviderError(Exception):
    def __init__(self, code: str, message: str, status: int = 502):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


# ---------------------------------------------------------------------------
# Chaves (keyring do SO)


class AIKeyStore:
    def set(self, provider: str, key: str) -> None:
        import keyring

        keyring.set_password(AI_KEYRING_SERVICE, provider, key)

    def get(self, provider: str) -> str | None:
        import keyring

        return keyring.get_password(AI_KEYRING_SERVICE, provider)

    def configured(self, provider: str) -> bool:
        return self.get(provider) is not None


# ---------------------------------------------------------------------------
# Schemas de saída (validação Pydantic antes de qualquer preview)


class GeneratedTestcase(BaseModel):
    title: str
    type: str = Field(default="manual", pattern="^(manual|automated|hybrid)$")
    priority: str = Field(default="medium", pattern="^(critical|high|medium|low)$")
    tags: list[str] = []
    objetivo: str = ""
    pre_condicoes: list[str] = []
    passos: list[str]
    resultado_esperado: str


class GeneratedTestcases(BaseModel):
    testcases: list[GeneratedTestcase]


class ReviewIssue(BaseModel):
    kind: str = Field(pattern="^(passo_ambiguo|duplicidade|resultado_vago|outro)$")
    message: str
    step_index: int | None = None


class ReviewResult(BaseModel):
    issues: list[ReviewIssue]
    summary: str = ""


class DailyDigest(BaseModel):
    summary: str  # resumo executivo do dia
    impediments: list[str] = []  # impedimentos
    progress: str = ""  # andamento
    action_items: list[str] = []  # viram todos com confirmação


class MeetingSummary(BaseModel):
    summary: str  # resumo executivo da reunião
    decisions: list[str] = []  # decisões tomadas
    action_items: list[str] = []  # próximos passos


class ImportConversion(BaseModel):
    folder: str = "importados"  # pasta sugerida pelo contexto do arquivo
    testcases: list[GeneratedTestcase]


def testcase_body_bdd(item: GeneratedTestcase, feature: str = "") -> str:
    """Renderiza o item gerado no formato BDD canônico (doc §1.1)."""
    lines = [f"Feature: {feature or item.title}", ""]
    lines.append(f"  Scenario: {item.title}")
    pre = item.pre_condicoes or ["que o sistema está disponível"]
    lines.append(f"    Given {pre[0]}")
    lines += [f"    And {p}" for p in pre[1:]]
    passos = item.passos or ["executar a ação principal"]
    lines.append(f"    When {passos[0]}")
    lines += [f"    And {p}" for p in passos[1:]]
    lines.append(f"    Then {item.resultado_esperado}")
    lines.append("")
    return "\n".join(lines)


def testcase_body(item: GeneratedTestcase) -> str:
    """Converte o item gerado no corpo .md canônico (âncoras do parser)."""
    lines = ["## Objetivo", "", item.objetivo or "-", "", "## Pré-condições", ""]
    lines += [f"- {p}" for p in item.pre_condicoes] or ["-"]
    lines += ["", "## Passos", ""]
    lines += [f"{i}. {passo}" for i, passo in enumerate(item.passos, 1)]
    lines += ["", "## Resultado esperado", "", item.resultado_esperado, ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Providers


def _extract_json(text: str) -> Any:
    """Extrai o primeiro bloco JSON da resposta (modelos põem texto ao redor)."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    if start == -1:
        raise AIProviderError("invalid_output", "resposta sem JSON", 422)
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except ValueError as exc:
                    raise AIProviderError(
                        "invalid_output", f"JSON ilegível na resposta: {exc}", 422
                    ) from exc
    raise AIProviderError("invalid_output", "JSON truncado na resposta", 422)


class _BaseProvider:
    def __init__(self, name: str, model: str, keys: AIKeyStore,
                 transport: httpx.BaseTransport | None = None):
        self.name = name
        self.model = model
        self.keys = keys
        self.transport = transport

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=120, transport=self.transport)

    def _post(self, url: str, headers: dict, payload: dict) -> dict:
        with self._client() as client:
            resp = client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise AIProviderError(
                "provider_error",
                f"{self.name} {resp.status_code}: {resp.text[:300]}",
            )
        return resp.json()

    def _raw_complete(self, system: str, user: str) -> str:
        raise NotImplementedError

    def complete(self, system: str, user: str,
                 schema: type[BaseModel] | None = None) -> str | BaseModel:
        if schema is not None:
            system = (
                f"{system}\n\nResponda APENAS com um objeto JSON válido no schema:"
                f"\n{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
                "\nSem texto fora do JSON."
            )
        text = self._raw_complete(system, user)
        if schema is None:
            return text
        data = _extract_json(text)
        try:
            return schema.model_validate(data)
        except ValidationError as exc:
            raise AIProviderError(
                "schema_mismatch",
                f"saída do modelo fora do schema {schema.__name__}: {exc.errors()[:3]}",
                422,
            ) from exc


class OpenAICompatible(_BaseProvider):
    """OpenAI, OpenRouter, Ollama, LM Studio, vLLM — só muda a base_url."""

    def __init__(self, name: str, model: str, keys: AIKeyStore,
                 base_url: str = "https://api.openai.com/v1",
                 transport: httpx.BaseTransport | None = None):
        super().__init__(name, model, keys, transport)
        self.base_url = base_url.rstrip("/")

    def _raw_complete(self, system: str, user: str) -> str:
        headers = {}
        key = self.keys.get(self.name)
        if key:  # endpoints locais (LM Studio) dispensam chave
            headers["Authorization"] = f"Bearer {key}"
        data = self._post(
            f"{self.base_url}/chat/completions",
            headers,
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
            },
        )
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise AIProviderError(
                "provider_error", f"{self.name}: resposta sem choices"
            ) from exc


class AnthropicProvider(_BaseProvider):
    def _raw_complete(self, system: str, user: str) -> str:
        key = self.keys.get(self.name)
        if not key:
            raise AIProviderError("no_key", f"chave do provider '{self.name}'"
                                  " não configurada", 409)
        data = self._post(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": key, "anthropic-version": "2023-06-01"},
            {
                "model": self.model,
                "max_tokens": 4096,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        try:
            return data["content"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise AIProviderError(
                "provider_error", f"{self.name}: resposta sem content"
            ) from exc


class GeminiProvider(_BaseProvider):
    def _raw_complete(self, system: str, user: str) -> str:
        key = self.keys.get(self.name)
        if not key:
            raise AIProviderError("no_key", f"chave do provider '{self.name}'"
                                  " não configurada", 409)
        data = self._post(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent",
            {"x-goog-api-key": key},
            {
                "system_instruction": {"parts": [{"text": system}]},
                "contents": [{"parts": [{"text": user}]}],
            },
        )
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise AIProviderError(
                "provider_error", f"{self.name}: resposta sem candidates"
            ) from exc


# base_url default por tipo — endpoints locais NÃO devem cair no OpenAI quando
# o usuário omite a URL (senão o modelo local é silenciosamente roteado p/ nuvem).
_DEFAULT_BASE_URL = {
    "lmstudio": "http://localhost:1234/v1",
    "ollama": "http://localhost:11434/v1",
    "vllm": "http://localhost:8000/v1",
}


def build_provider(config: dict[str, Any], keys: AIKeyStore,
                   transport: httpx.BaseTransport | None = None) -> _BaseProvider:
    name = str(config.get("name"))
    kind = str(config.get("kind", "openai_compatible"))
    model = str(config.get("model", ""))
    if kind in ("openai", "openai_compatible", "openrouter", "ollama",
                "lmstudio", "vllm"):
        base = config.get("base_url") or _DEFAULT_BASE_URL.get(
            kind, "https://api.openai.com/v1"
        )
        return OpenAICompatible(name, model, keys, base_url=str(base),
                                transport=transport)
    if kind == "anthropic":
        return AnthropicProvider(name, model, keys, transport)
    if kind == "gemini":
        return GeminiProvider(name, model, keys, transport)
    raise AIProviderError("unknown_kind", f"kind de provider desconhecido: {kind}", 422)


# ---------------------------------------------------------------------------
# Funções (todas devolvem PREVIEW — nunca escrevem)


_GENERATE_SYSTEM = (
    "Você é um analista de testes sênior. A partir da story fornecida "
    "(critérios de aceite em EARS quando presentes), gere casos de teste "
    "objetivos, com passos numerados acionáveis e resultado esperado "
    "verificável. Português do Brasil."
)


def generate_testcases(provider: _BaseProvider, story_md: str) -> GeneratedTestcases:
    result = provider.complete(_GENERATE_SYSTEM, story_md, GeneratedTestcases)
    assert isinstance(result, GeneratedTestcases)
    return result


_REVIEW_SYSTEM = (
    "Você revisa casos de teste. Aponte: passos ambíguos (passo_ambiguo), "
    "possível duplicidade com os CTs candidatos listados (duplicidade) e "
    "resultado esperado vago (resultado_vago). Seja específico e cite o "
    "índice do passo quando aplicável."
)


def review_testcase(provider: _BaseProvider, ct_md: str,
                    similar: list[dict[str, Any]]) -> ReviewResult:
    similar_txt = "\n".join(
        f"- {s['id']}: {s['title']} (tags: {s.get('tags', '')})" for s in similar
    ) or "(nenhum candidato)"
    user = f"CT em revisão:\n\n{ct_md}\n\nCandidatos a duplicata no índice:\n{similar_txt}"
    result = provider.complete(_REVIEW_SYSTEM, user, ReviewResult)
    assert isinstance(result, ReviewResult)
    return result


_NEGATIVE_SYSTEM = (
    "A partir do caso de teste positivo fornecido, proponha variações "
    "negativas: campos vazios, caracteres especiais, limites, estados "
    "inválidos. Mesmo formato de saída da geração."
)


def negative_cases(provider: _BaseProvider, ct_md: str) -> GeneratedTestcases:
    result = provider.complete(_NEGATIVE_SYSTEM, ct_md, GeneratedTestcases)
    assert isinstance(result, GeneratedTestcases)
    return result


_DAILY_SYSTEM = (
    "Você é um QA sênior preparando sua daily standup. A partir do contexto "
    "do dia (afazeres, atividade de testes, variação das métricas e defeitos), "
    "escreva o que deve ser dito na daily: um resumo executivo objetivo do que "
    "andou, os impedimentos (se houver), o andamento, e os action items "
    "concretos para hoje. Seja direto e factual, em português do Brasil."
)


def generate_daily(provider: _BaseProvider, context_md: str) -> DailyDigest:
    result = provider.complete(_DAILY_SYSTEM, context_md, DailyDigest)
    assert isinstance(result, DailyDigest)
    return result


_MEETING_SYSTEM = (
    "Você resume reuniões para um QA. A partir da descrição/transcrição "
    "fornecida, produza um resumo executivo objetivo, as decisões tomadas e "
    "os próximos passos (action items). Português do Brasil, sem enrolação."
)


def summarize_meeting(provider: _BaseProvider, body: str) -> MeetingSummary:
    result = provider.complete(_MEETING_SYSTEM, body, MeetingSummary)
    assert isinstance(result, MeetingSummary)
    return result


# Prompt curto de propósito: a importação precisa rodar bem em modelos de
# até 9B (doc §1.1 — baixo consumo de tokens, sem exemplos longos).
_IMPORT_SYSTEM = (
    "Extraia os casos de teste do texto (formato livre). Para cada caso: "
    "title, passos (lista de ações) e resultado_esperado; infira "
    "pre_condicoes quando houver. Sugira 'folder' (kebab-case) pelo contexto "
    "do arquivo. Não invente casos que não estão no texto. PT-BR."
)


def convert_import(provider: _BaseProvider, filename: str, text: str,
                   max_chars: int = 24000) -> ImportConversion:
    """Converte um arquivo livre (txt/md/xml) em CTs BDD — preview apenas."""
    clipped = text[:max_chars]
    user = f"Arquivo: {filename}\n\n{clipped}"
    result = provider.complete(_IMPORT_SYSTEM, user, ImportConversion)
    assert isinstance(result, ImportConversion)
    return result


def find_similar(conn: sqlite3.Connection, title: str, tags: list[str],
                 exclude_id: str | None = None, limit: int = 5) -> list[dict]:
    """Candidatos a duplicata por título/tags similares (insumo da revisão)."""
    words = [w for w in re.findall(r"\w{4,}", title.lower())][:4]
    candidates: dict[str, dict] = {}
    for word in words:
        for row in conn.execute(
            "SELECT id, title FROM testcases WHERE LOWER(title) LIKE ? LIMIT 10",
            (f"%{word}%",),
        ):
            candidates[row["id"]] = dict(row)
    for tag in tags:
        for row in conn.execute(
            "SELECT t.id, t.title FROM testcases t JOIN tc_tags g"
            " ON g.testcase_id = t.id WHERE g.tag = ? LIMIT 10",
            (tag,),
        ):
            candidates[row["id"]] = dict(row)
    if exclude_id:
        candidates.pop(exclude_id, None)
    return list(candidates.values())[:limit]
