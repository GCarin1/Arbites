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
import typing
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


_REASONING_TAGS = ("think", "thinking", "thought", "reasoning", "scratchpad")


def _strip_reasoning(text: str) -> str:
    """Remove blocos de raciocínio (<think>…</think>) que modelos locais vazam."""
    for tag in _REASONING_TAGS:
        text = re.sub(rf"<{tag}>.*?</{tag}>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text


def _balanced_objects(text: str) -> list[Any]:
    """Todos os objetos JSON `{…}` de nível superior que fazem parse (string-aware)."""
    out: list[Any] = []
    i, n = 0, len(text)
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        depth = 0
        in_str = esc = False
        j = i
        while j < n:
            c = text[j]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        out.append(json.loads(text[i : j + 1]))
                    except ValueError:
                        pass
                    break
            j += 1
        i = j + 1
    return out


def _json_candidates(text: str) -> list[Any]:
    """Objetos JSON candidatos, priorizando blocos cercados e a resposta final.

    Modelos pequenos costumam raciocinar/reconstruir o schema antes de emitir
    os dados; o objeto útil tende a estar no fim ou dentro de uma cerca ```json.
    """
    text = _strip_reasoning(text)
    fenced: list[Any] = []
    for m in re.finditer(r"```(?:json)?\s*(.*?)```", text, re.DOTALL):
        fenced.extend(_balanced_objects(m.group(1)))
    whole = _balanced_objects(text)
    # cercados primeiro (sinal forte de "resposta"); depois o texto do fim p/ o início.
    return fenced + list(reversed(whole))


def _extract_json(text: str) -> Any:
    """Compat: primeiro objeto JSON legível da resposta."""
    cands = _json_candidates(text)
    if not cands:
        raise AIProviderError("invalid_output", "resposta sem JSON", 422)
    return cands[0]


def _example_for(annotation: Any, field: Any) -> Any:
    """Valor-exemplo concreto para uma anotação de tipo (prompt guiado por exemplo)."""
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin in (list, tuple, set):
        inner = args[0] if args else str
        return [_example_for(inner, None)]
    if origin is typing.Union:  # Optional[X] / X | None
        non_none = [a for a in args if a is not type(None)]
        return _example_for(non_none[0], None) if non_none else None
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return _example_from_model(annotation)
    if annotation is bool:
        return True
    if annotation is int:
        return 0
    if annotation is float:
        return 0.0
    # str e afins: usa o default textual (ex.: "manual", "importados") quando houver.
    if field is not None:
        default = getattr(field, "default", None)
        if isinstance(default, str) and default:
            return default
    return "texto"


def _example_from_model(model_cls: type[BaseModel]) -> dict[str, Any]:
    """Exemplo compacto e concreto do JSON esperado — substitui o dump do JSON Schema.

    Modelos ≤ 9B entram em loop ao receber JSON Schema ($defs/properties/required);
    um exemplo preenchível é seguido de forma muito mais confiável.
    """
    return {
        name: _example_for(field.annotation, field)
        for name, field in model_cls.model_fields.items()
    }


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

    def _raw_complete(self, system: str, user: str,
                      json_mode: bool = False) -> str:
        raise NotImplementedError

    def complete(self, system: str, user: str,
                 schema: type[BaseModel] | None = None) -> str | BaseModel:
        if schema is not None:
            example = json.dumps(_example_from_model(schema), ensure_ascii=False)
            system = (
                f"{system}\n\nResponda SOMENTE com um objeto JSON exatamente neste"
                f" formato, preenchido com os dados reais (um objeto por item, sem"
                f" abreviar com 'repita'/'...'):\n{example}\n"
                "Não escreva schema, comentários, explicações nem raciocínio — só o JSON."
            )
        text = self._raw_complete(system, user, json_mode=schema is not None)
        if schema is None:
            return text
        # Escolhe, dentre os objetos JSON candidatos, o primeiro que valida no
        # schema — descarta raciocínio/reconstruções de schema que o modelo vaze.
        last_err: ValidationError | None = None
        for cand in _json_candidates(text):
            try:
                return schema.model_validate(cand)
            except ValidationError as exc:
                last_err = exc
        if last_err is None:
            raise AIProviderError("invalid_output", "resposta sem JSON", 422)
        raise AIProviderError(
            "schema_mismatch",
            f"saída do modelo fora do schema {schema.__name__}: {last_err.errors()[:3]}",
            422,
        ) from last_err


class OpenAICompatible(_BaseProvider):
    """OpenAI, OpenRouter, Ollama, LM Studio, vLLM — só muda a base_url."""

    def __init__(self, name: str, model: str, keys: AIKeyStore,
                 base_url: str = "https://api.openai.com/v1",
                 transport: httpx.BaseTransport | None = None):
        super().__init__(name, model, keys, transport)
        self.base_url = base_url.rstrip("/")

    def _raw_complete(self, system: str, user: str,
                      json_mode: bool = False) -> str:
        headers = {}
        key = self.keys.get(self.name)
        if key:  # endpoints locais (LM Studio) dispensam chave
            headers["Authorization"] = f"Bearer {key}"
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        if json_mode:
            # força saída 100% JSON — corta loops de raciocínio de modelos locais.
            payload["response_format"] = {"type": "json_object"}
        try:
            data = self._post(url, headers, payload)
        except AIProviderError:
            if not json_mode:
                raise
            # servidor não suporta response_format → tenta sem (prompt já guia o JSON).
            payload.pop("response_format", None)
            data = self._post(url, headers, payload)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise AIProviderError(
                "provider_error", f"{self.name}: resposta sem choices"
            ) from exc


class AnthropicProvider(_BaseProvider):
    def _raw_complete(self, system: str, user: str,
                      json_mode: bool = False) -> str:
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
    def _raw_complete(self, system: str, user: str,
                      json_mode: bool = False) -> str:
        key = self.keys.get(self.name)
        if not key:
            raise AIProviderError("no_key", f"chave do provider '{self.name}'"
                                  " não configurada", 409)
        payload: dict[str, Any] = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": user}]}],
        }
        if json_mode:
            payload["generationConfig"] = {"responseMimeType": "application/json"}
        data = self._post(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent",
            {"x-goog-api-key": key},
            payload,
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
    "Extraia TODOS os casos de teste do texto (formato livre ou BDD/Gherkin). "
    "Mapeamento BDD: Given/Dado → pre_condicoes; When/And/Quando → passos; "
    "Then/Então → resultado_esperado. Um objeto por caso — gere todos (CT01..CTnn), "
    "nunca abrevie com 'repita para os demais' ou '...'. Sugira 'folder' "
    "(kebab-case) pelo contexto do arquivo. Não invente casos fora do texto. PT-BR."
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
