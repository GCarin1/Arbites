"""Run local que não chega a executar (change 0170).

`python_path` é o executável do Python, mas o nome sugere `PYTHONPATH` e quem
preenche costuma pôr ali a pasta do projeto ou o `.env`. O valor errado ia
direto para o `create_subprocess_exec`: a execution nascia vazia, a tela dizia
"sem resultados" e o motivo morria no log do run.
"""

import os
import sys
from pathlib import Path

import pytest
from conftest import logged_in_client

from arbites import executions as exec_ops
from arbites.runner import PythonPathError, resolver_python


def test_sem_valor_usa_o_python_do_arbites():
    assert resolver_python(None) == sys.executable
    assert resolver_python("   ") == sys.executable


def test_pasta_de_virtualenv_e_resolvida(tmp_path):
    """Apontar para a pasta do venv é comum demais para virar recusa."""
    venv = tmp_path / ".venv"
    (venv / "bin").mkdir(parents=True)
    python = venv / "bin" / "python"
    python.write_text("#!/bin/sh\n")
    python.chmod(0o755)
    assert resolver_python(str(venv)) == str(python)


def test_arquivo_de_configuracao_e_recusado_dizendo_o_que_fazer(tmp_path):
    """O caso relatado: `python_path` apontando para o `.env` do projeto."""
    dotenv = tmp_path / ".env"
    dotenv.write_text("BASE_URL=http://x\n")
    with pytest.raises(PythonPathError) as exc:
        resolver_python(str(dotenv))
    mensagem = str(exc.value)
    assert "não é executável" in mensagem
    assert "python.exe" in mensagem  # diz o que o campo quer


def test_pasta_sem_interpretador_e_recusada(tmp_path):
    with pytest.raises(PythonPathError) as exc:
        resolver_python(str(tmp_path))
    assert "Scripts/python.exe" in str(exc.value)


def test_caminho_inexistente_e_recusado(tmp_path):
    with pytest.raises(PythonPathError):
        resolver_python(str(tmp_path / "nao-existe"))


def test_salvar_o_alvo_ja_recusa_o_caminho_errado(ws, tmp_path):
    """A viagem inteira é poupada: a recusa acontece ao configurar."""
    dotenv = tmp_path / ".env"
    dotenv.write_text("X=1\n")
    with logged_in_client(ws) as client:
        r = client.put("/api/v1/targets", json={"targets": [{
            "name": "Teste", "kind": "behave",
            "local_path": str(tmp_path), "python_path": str(dotenv),
        }]})
        assert r.status_code == 422, r.text
        assert r.json()["error"]["code"] == "bad_python_path"
        assert "Teste" in r.json()["error"]["message"]


def test_alvo_valido_continua_salvando(ws, tmp_path):
    with logged_in_client(ws) as client:
        r = client.put("/api/v1/targets", json={"targets": [{
            "name": "Teste", "kind": "behave", "local_path": str(tmp_path),
        }]})
        assert r.status_code == 200, r.text


def test_o_aborto_fica_na_execution_mesmo_sem_nenhum_CT(ws):
    """O ponto do defeito: execution sem CT vinculado perdia o motivo inteiro.

    Rodar um `.feature` sem CT espelho é legítimo desde a 0067 — vínculo é
    rastreabilidade, não pré-requisito. O que não pode é o run morrer em
    silêncio.
    """
    from arbites.indexer import connect, reindex_full
    from arbites.runner import RunManager

    conn = connect(ws)
    reindex_full(ws, conn)
    execution = exec_ops.create(
        ws, name="Run local Teste", owner="behave", sprint=None,
        environment="Teste", testcases=[], origin="local_run",
    )
    exec_ops.save(ws, execution)
    gerente = RunManager(ws, conn)

    class _Run:
        exec_id = execution["id"]

    gerente._mark_pending(_Run(), "blocked", "python_path '/x/.env' não é executável")

    salva = exec_ops.load(ws, execution["id"])
    assert salva["aborted"]["reason"].startswith("python_path")
    assert salva["history"][-1]["event"] == "run_aborted"
    # e o índice carrega o motivo, que é por onde a tela o lê
    linha = conn.execute(
        "SELECT abort_reason FROM executions WHERE id = ?", (execution["id"],)
    ).fetchone()
    assert linha["abort_reason"].startswith("python_path")
