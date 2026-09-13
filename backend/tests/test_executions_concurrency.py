"""Critério de aceite da concorrência em execução (change 0123).

O cliente de teste síncrono serializa as requisições e nunca reproduziria a
corrida — por isso este arquivo fala com o app por ASGI, disparando os
uploads de verdade ao mesmo tempo.

A janela existia porque a rota carregava a execution, esperava o arquivo
chegar e só então gravava: um upload grande o bastante para ir para disco
suspende a requisição no meio do ciclo carregar-alterar-gravar.
"""

import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from arbites.api import create_app
from arbites.workspace import Workspace
from conftest import login_admin

TC_BODY = (
    "## Objetivo\n\nValidar.\n\n## Passos\n\n1. Abrir\n2. Agir\n\n"
    "## Resultado esperado\n\nOk.\n"
)
QUANTOS = 6
# Acima do limite em que o upload deixa de caber em memória e vai para
# disco — é o que faz a leitura suspender a requisição de verdade.
GRANDE = b"\x89PNG\r\n\x1a\n" + b"\0" * (2 * 1024 * 1024)


@pytest.fixture()
def ciclo(tmp_path):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        login_admin(client)
        ct = client.post(
            "/api/v1/testcases", json={"title": "Login", "body": TC_BODY}
        ).json()
        execution = client.post(
            "/api/v1/executions",
            json={"name": "Regressão", "testcase_ids": [ct["id"]]},
        ).json()
        yield client, ws, app, execution["id"], ct["id"], dict(client.cookies)


def test_uploads_simultaneos_sao_todos_registrados(ciclo):
    """Medido antes da correção: seis respostas 201, seis arquivos no disco e
    TRÊS registros no execution.json. A pior combinação possível — a pessoa
    recebe confirmação, o arquivo ocupa espaço, e nem o produto nem a trilha
    de auditoria sabem que ele existe."""
    client, ws, app, exec_id, ct_id, cookies = ciclo

    async def dispara():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://teste", cookies=cookies
        ) as ac:
            async def envia(i: int):
                return await ac.post(
                    f"/api/v1/executions/{exec_id}/results/{ct_id}/evidences",
                    files={"file": (f"tela{i}.png", GRANDE + bytes([i]), "image/png")},
                )

            return await asyncio.gather(*[envia(i) for i in range(QUANTOS)])

    respostas = asyncio.run(dispara())
    assert [r.status_code for r in respostas] == [201] * QUANTOS

    final = client.get(f"/api/v1/executions/{exec_id}").json()
    registradas = final["results"][0]["evidences"]
    assert len(registradas) == QUANTOS

    # e cada registro aponta para um arquivo que existe: confirmação e disco
    # contando a mesma história
    pasta = next(ws.root.glob(f"executions/*/{exec_id}"))
    for evidencia in registradas:
        assert (pasta / evidencia["path"]).is_file()
    assert len(list(pasta.rglob("evidences/*/*.png"))) == QUANTOS


def test_o_history_registra_uma_entrada_por_evidencia(ciclo):
    """A trilha também não pode perder nenhuma: é ela que responde quem
    anexou o quê."""
    client, _, app, exec_id, ct_id, cookies = ciclo

    async def dispara():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://teste", cookies=cookies
        ) as ac:
            return await asyncio.gather(*[
                ac.post(
                    f"/api/v1/executions/{exec_id}/results/{ct_id}/evidences",
                    files={"file": (f"t{i}.png", GRANDE + bytes([i]), "image/png")},
                )
                for i in range(QUANTOS)
            ])

    asyncio.run(dispara())
    final = client.get(f"/api/v1/executions/{exec_id}").json()
    eventos = [h for h in final["history"] if h["event"] == "evidence"]
    assert len(eventos) == QUANTOS
