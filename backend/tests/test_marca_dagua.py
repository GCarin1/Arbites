"""A marca d'água da ingestão é só o documento do run (change 0177).

"O que já ingeri" é respondido pelo DISCO — e daí caem de graça a
idempotência e a retomada. Mas a varredura era `ci/**/*.md`, que entra também
na pasta de anexos do run (`ci/<ano>/<chave>/`), onde mora o `analysis.md`
que o pipeline publica. A marca d'água nascia poluída; e um pipeline que
nomeie a análise pela chave do run faria esse run ser pulado para sempre.
"""

from datetime import datetime, timezone

import pytest

from arbites.ci_ingest import CIIngestor, escrever_run


def _run(chave, quando="2026-09-10T03:00:00+00:00"):
    return {"key": chave, "provider": "github", "repo": "org/repo",
            "workflow": "w.yml", "run_id": chave.split("-")[-1],
            "conclusion": "success", "started_at": quando, "ingested_at": quando}


def test_so_o_documento_do_run_conta(ws):
    """O `analysis.md` do anexo não é um run ingerido."""
    manifesto = {"version": 2,
                 "attachments": [{"kind": "analysis", "path": "analysis.md"}]}
    escrever_run(ws.root, _run("github-9001"), manifesto,
                 {"analysis.md": b"# analise\n"}, None)
    ingestor = CIIngestor(ws, None, None)
    assert ingestor.ja_ingeridos() == {"github-9001"}


def test_anexo_nomeado_como_a_chave_nao_pula_o_run(ws):
    """O caso que faria o run 9002 nunca mais ser ingerido."""
    manifesto = {"version": 2,
                 "attachments": [{"kind": "analysis", "path": "github-9002.md"}]}
    escrever_run(ws.root, _run("github-9001"), manifesto,
                 {"github-9002.md": b"# analise do run vizinho\n"}, None)
    assert CIIngestor(ws, None, None).ja_ingeridos() == {"github-9001"}


def test_varios_anos_entram(ws):
    """A pasta é por ano; a marca d'água atravessa a virada."""
    for chave, quando in [("github-8001", "2025-12-30T03:00:00+00:00"),
                          ("github-9001", "2026-01-02T03:00:00+00:00")]:
        escrever_run(ws.root, _run(chave, quando), {"version": 2}, {}, None)
    assert CIIngestor(ws, None, None).ja_ingeridos() == {"github-8001", "github-9001"}


def test_workspace_sem_ci_responde_vazio(ws):
    assert CIIngestor(ws, None, None).ja_ingeridos() == set()


def test_o_texto_da_quebra_concorda_no_singular():
    """"1 execução verde seguidas" era o que saía com o plural só no nome."""
    from arbites.ci_ingest import _o_que_mudou

    def runs(n, conclusao, inicio=0):
        return [{"id": f"github-{i}", "workflow": "w.yml",
                 "conclusion": conclusao,
                 "started_at": f"2026-09-{10 + i:02d}T03:00:00+00:00"}
                for i in range(inicio, inicio + n)]

    atuais = runs(1, "success") + runs(1, "failure", 1)
    saude = {"runs": 2, "runs_previous": 0, "success_rate": 50.0,
             "success_rate_previous": None, "days_since_last_run": 0,
             "last_run_at": None, "goal": None}
    mudancas = _o_que_mudou(atuais, [], [], saude, [])
    quebra = next(m for m in mudancas if "quebrou" in m["text"])
    assert "1 execução verde seguida" in quebra["text"]
    assert "seguidas" not in quebra["text"]
