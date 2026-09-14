"""O sino de notificações (change 0161).

A decisão que estes testes fixam: a lista é DERIVADA do estado vivo, e só o
que cada pessoa leu/limpou é gravado. A consequência — problema resolvido some
do sino mesmo sem ter sido lido — é deliberada: caixa de entrada gravada cria
um segundo estado, e o segundo diverge do primeiro.
"""

import pytest
from conftest import ADMIN_EMAIL, login_admin

CORPO_CT = "## Passos\n\n1. abrir\n\n## Resultado esperado\n\nabre\n"
CT_QUEBRADO = "## Passos\n\n1. sem o heading obrigatório de resultado\n"


def _notificacoes(client) -> dict:
    r = client.get("/api/v1/notifications")
    assert r.status_code == 200, r.text
    return r.json()


def _por_tipo(dados: dict, kind: str) -> list[dict]:
    return [i for i in dados["items"] if i["kind"] == kind]


def _segunda_conta(client, email: str, senha: str, papel: str = "editor"):
    """Uma segunda pessoa, pelo fluxo real: cadastro → aprovação com papel."""
    novo = client.post("/api/v1/auth/register", json={
        "email": email, "password": senha, "name": "Outra pessoa"})
    assert novo.status_code == 201, novo.text
    user_id = novo.json()["user"]["id"]
    aprovado = client.post(f"/api/v1/admin/users/{user_id}/approve",
                           json={"role": papel})
    assert aprovado.status_code == 200, aprovado.text

    outro = client.__class__(client.app)
    entrada = outro.post("/api/v1/auth/login",
                         json={"email": email, "password": senha})
    assert entrada.status_code == 200, entrada.text
    return outro



# -- derivada do estado vivo -------------------------------------------------


def test_problema_do_indice_vira_notificacao(client):
    client.post("/api/v1/testcases",
                json={"title": "Sem resultado esperado", "body": CT_QUEBRADO})

    problemas = _por_tipo(_notificacoes(client), "problema")
    assert problemas, "aviso do índice precisa aparecer no sino"
    assert any("Resultado esperado" in p["message"] for p in problemas)


def test_problema_resolvido_some_do_sino_mesmo_sem_ter_sido_lido(client):
    """A consequência deliberada do modelo derivado. Uma caixa de entrada
    gravada deixaria o aviso corrigido na lista, e quem clicasse não acharia
    nada — informação que parece informação e não é."""
    ct = client.post("/api/v1/testcases",
                     json={"title": "Vai ser corrigido",
                           "body": CT_QUEBRADO}).json()["id"]
    assert _por_tipo(_notificacoes(client), "problema")

    client.put(f"/api/v1/testcases/{ct}", json={"body": CORPO_CT})

    restantes = _por_tipo(_notificacoes(client), "problema")
    assert not any(ct in (p["subject_full"] or "") for p in restantes)


def test_o_sino_e_a_aba_problemas_leem_a_mesma_lista(client):
    """Duas listas montadas em lugares diferentes divergiriam no primeiro
    aviso novo, e o sino mostraria o que a aba não mostra."""
    client.post("/api/v1/testcases",
                json={"title": "Quebrado", "body": CT_QUEBRADO})

    da_aba = {w["message"] for w in client.get("/api/v1/warnings").json()}
    do_sino = {n["message"] for n in _por_tipo(_notificacoes(client), "problema")}
    assert do_sino == da_aba


# -- ações do sistema --------------------------------------------------------


def test_ciclo_fechado_vira_notificacao_de_concluido(client):
    ct = client.post("/api/v1/testcases",
                     json={"title": "No ciclo", "body": CORPO_CT}).json()["id"]
    execucao = client.post("/api/v1/executions", json={
        "name": "Regressão de setembro", "owner": "qa",
        "testcase_ids": [ct]}).json()["id"]
    client.post(f"/api/v1/executions/{execucao}/results/{ct}/status",
                json={"status": "passed"})
    client.post(f"/api/v1/executions/{execucao}/close")

    feitos = _por_tipo(_notificacoes(client), "feito")
    aviso = next(f for f in feitos if f["subject"] == execucao)
    assert "Regressão de setembro" in aviso["message"]
    assert aviso["target"] == {"tab": "executions", "id": execucao}


def test_auditoria_concluida_vira_notificacao(client):
    client.post("/api/v1/audit/run")
    feitos = _por_tipo(_notificacoes(client), "feito")
    assert any("auditoria" in f["message"] for f in feitos)


# -- clicar leva à origem ----------------------------------------------------


def test_a_notificacao_leva_ao_ITEM_e_nao_so_a_lista(client):
    """Cair na lista e ter de procurar de novo é metade de um link."""
    ct = client.post("/api/v1/testcases",
                     json={"title": "Com problema", "body": CT_QUEBRADO}).json()["id"]

    problema = next(p for p in _por_tipo(_notificacoes(client), "problema")
                    if ct in (p["subject_full"] or ""))
    assert problema["target"]["tab"] == "testcases"
    assert problema["target"]["id"] == ct


def test_o_nome_do_arquivo_vem_separado_da_frase(client):
    """Para poder ir em destaque na tela. Destacar por regex dentro da
    mensagem erraria na primeira mensagem de formato diferente."""
    client.post("/api/v1/testcases",
                json={"title": "Destaque", "body": CT_QUEBRADO})

    problema = _por_tipo(_notificacoes(client), "problema")[0]
    assert problema["subject"]
    assert "/" not in problema["subject"]          # só o nome do arquivo
    assert problema["subject_full"].endswith(".md")  # o caminho inteiro no title


# -- lido, não lido, limpar --------------------------------------------------


def test_marcar_como_lida_e_desmarcar(client):
    client.post("/api/v1/testcases",
                json={"title": "Para ler", "body": CT_QUEBRADO})
    antes = _notificacoes(client)
    alvo = antes["items"][0]
    assert alvo["read"] is False

    client.post(f"/api/v1/notifications/{alvo['id']}/read")
    depois = _notificacoes(client)
    assert next(i for i in depois["items"] if i["id"] == alvo["id"])["read"] is True
    assert depois["unread"] == antes["unread"] - 1

    client.delete(f"/api/v1/notifications/{alvo['id']}/read")
    assert next(i for i in _notificacoes(client)["items"]
                if i["id"] == alvo["id"])["read"] is False


def test_o_id_e_estavel_entre_recalculos(client):
    """Se o id mudasse a cada recontagem, "lido" se perderia e o sino voltaria
    a piscar sozinho — que é o jeito mais rápido de alguém parar de olhar."""
    client.post("/api/v1/testcases",
                json={"title": "Estável", "body": CT_QUEBRADO})
    primeiro = {i["id"] for i in _notificacoes(client)["items"]}
    segundo = {i["id"] for i in _notificacoes(client)["items"]}
    assert primeiro == segundo


def test_marcar_todas_como_lidas(client):
    for i in range(3):
        client.post("/api/v1/testcases",
                    json={"title": f"Quebrado {i}", "body": CT_QUEBRADO})
    dados = _notificacoes(client)
    assert dados["unread"] > 0

    client.post("/api/v1/notifications/read-all",
                json={"ids": [i["id"] for i in dados["items"]]})
    assert _notificacoes(client)["unread"] == 0


def test_limpar_e_marca_dagua_e_nao_apaga_o_motivo(client):
    """Não há o que apagar: a lista é derivada. Limpar grava "vi tudo até
    aqui" — e o motivo que continua valendo volta quando voltar a acontecer."""
    client.post("/api/v1/testcases",
                json={"title": "Persistente", "body": CT_QUEBRADO})
    assert _notificacoes(client)["items"]

    client.post("/api/v1/notifications/clear")
    assert _notificacoes(client)["items"] == []

    # o aviso do índice CONTINUA existindo — limpar o sino não conserta nada
    assert client.get("/api/v1/warnings").json()


# -- o log de atividade é opcional e só de admin -----------------------------


def test_log_de_atividade_nao_entra_por_padrao(client):
    """O único volume capaz de inundar o sino nasce desligado."""
    switches = {s["name"]: s for s in
                client.get("/api/v1/admin/switches").json()["switches"]}
    assert switches["notifications_info"]["enabled"] is False
    assert _por_tipo(_notificacoes(client), "info") == []


def test_log_de_atividade_entra_com_o_interruptor_ligado(client):
    client.put("/api/v1/admin/switches/notifications_info",
               json={"enabled": True})
    client.post("/api/v1/testcases", json={"title": "Gera log", "body": CORPO_CT})

    info = _por_tipo(_notificacoes(client), "info")
    assert info
    assert any(ADMIN_EMAIL in i["message"] for i in info)


def test_log_de_atividade_nao_alcanca_quem_nao_e_admin(client, ws):
    """Ligado ou não: o log é de quem administra a instância."""
    client.put("/api/v1/admin/switches/notifications_info",
               json={"enabled": True})
    outro = _segunda_conta(client, "qa@arbites.test", "senha-de-teste-longa-2")
    dados = outro.get("/api/v1/notifications").json()
    assert [i for i in dados["items"] if i["kind"] == "info"] == []


def test_lido_e_por_pessoa(client):
    """Marcar como lida é sobre VOCÊ; a de outra pessoa não pode mudar."""
    client.post("/api/v1/testcases",
                json={"title": "Compartilhado", "body": CT_QUEBRADO})
    alvo = _notificacoes(client)["items"][0]
    client.post(f"/api/v1/notifications/{alvo['id']}/read")

    outro = _segunda_conta(client, "outro@arbites.test", "senha-de-teste-longa-3")
    dele = outro.get("/api/v1/notifications").json()
    mesma = next((i for i in dele["items"] if i["id"] == alvo["id"]), None)
    assert mesma is not None
    assert mesma["read"] is False


def test_limpar_realmente_limpa_a_observabilidade(client, ws, monkeypatch):
    """Defeito encontrado medindo: se a mudança de observabilidade carregasse
    "agora" como instante, a marca d'água de limpar nunca a alcançaria — na
    chamada seguinte o novo "agora" já seria maior, e o item voltaria na hora.

    O instante correto é o da última execução, que é o que faz o período ser
    o que é.
    """
    import yaml

    from arbites import notifications as notif_ops

    painel = {
        "health": {"last_run_at": "2026-09-01T03:00:00+00:00"},
        "period": {"since": "2026-08-15T00:00:00+00:00",
                   "until": "2026-09-14T00:00:00+00:00"},
        "changes": [{"kind": "broke", "text": "qa-nightly quebrou",
                     "run_id": "github-1"}],
    }
    itens = notif_ops._da_observabilidade(painel)
    assert itens[0]["at"] == "2026-09-01T03:00:00+00:00"
    # e NÃO o fim do período, que é sempre "agora"
    assert itens[0]["at"] != painel["period"]["until"]


def test_o_assunto_nao_aparece_duas_vezes_seguidas(client):
    """O nome vai no destaque; repeti-lo no começo da frase o diz duas vezes
    ("`lcp_ms` lcp_ms piorou 23%") e empurra o resto para fora da linha."""
    from arbites import notifications as notif_ops

    itens = notif_ops._da_observabilidade({
        "health": {"last_run_at": "2026-09-01T03:00:00+00:00"},
        "period": {"since": "2026-08-15T00:00:00+00:00"},
        "changes": [{"kind": "signal", "signal": "lcp_ms",
                     "text": "lcp_ms piorou 23.4% contra o período anterior"}],
    })
    assert itens[0]["subject"] == "lcp_ms"
    assert itens[0]["message"] == "piorou 23.4% contra o período anterior"


def test_mensagem_que_nao_comeca_pelo_assunto_fica_intacta(client):
    from arbites import notifications as notif_ops

    assert notif_ops._sem_repetir(
        "Credencial do GitHub", "a credencial expira em 5 dias"
    ) == "a credencial expira em 5 dias"
