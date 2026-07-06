"""Critérios de aceite da spec segmentation (SC9) — squad na cadeia."""

TC_BODY = "## Passos\n\n1. Abrir\n2. Agir\n\n## Resultado esperado\n\nok\n"


def make_epic(client, title, squad=None):
    body = {"kind": "epic", "title": title}
    if squad:
        body["squad"] = squad
    return client.post("/api/v1/requirements", json=body).json()


def make_story(client, title, epic=None, squad=None):
    body = {"kind": "story", "title": title, "epic": epic}
    if squad:
        body["squad"] = squad
    return client.post("/api/v1/requirements", json=body).json()


def make_ct(client, title, story=None, squad=None, status="ready"):
    body = {"title": title, "body": TC_BODY, "status": status}
    if story:
        body["story"] = story
    if squad:
        body["squad"] = squad
    return client.post("/api/v1/testcases", json=body).json()


def test_effective_squad_inherits_and_overrides(client):
    """SC9.1: CT herda o squad da story; squad explícito no CT prevalece."""
    epic = make_epic(client, "Pagamentos", squad="pagamentos")
    story = make_story(client, "Pix", epic=epic["id"])  # sem squad → herda do epic
    ct_inherited = make_ct(client, "Pix ok", story=story["id"])  # herda via story→epic
    ct_own = make_ct(client, "Pix especial", story=story["id"], squad="tesouraria")

    # herança epic→story→CT
    inh = client.get(f"/api/v1/testcases/{ct_inherited['id']}").json()
    assert inh["squad"] is None
    assert inh["squad_effective"] == "pagamentos"

    # override explícito no CT prevalece
    own = client.get(f"/api/v1/testcases/{ct_own['id']}").json()
    assert own["squad_effective"] == "tesouraria"

    # story com squad próprio sobrepõe o epic para os CTs que dela herdam
    story2 = make_story(client, "Boleto", epic=epic["id"], squad="cobranca")
    ct2 = make_ct(client, "Boleto ok", story=story2["id"])
    assert client.get(f"/api/v1/testcases/{ct2['id']}").json()["squad_effective"] == "cobranca"


def test_filter_testcases_by_squad(client):
    """SC9.2 (base do board): /testcases?squad filtra pelo squad efetivo."""
    epic = make_epic(client, "Pagamentos", squad="pagamentos")
    story = make_story(client, "Pix", epic=epic["id"])
    make_ct(client, "Pix ok", story=story["id"])  # efetivo: pagamentos
    make_ct(client, "Avulso", squad="risco")  # efetivo: risco

    pagamentos = client.get("/api/v1/testcases", params={"squad": "pagamentos"}).json()
    assert [t["title"] for t in pagamentos] == ["Pix ok"]
    risco = client.get("/api/v1/testcases", params={"squad": "risco"}).json()
    assert [t["title"] for t in risco] == ["Avulso"]


def test_board_results_carry_effective_squad(client):
    """SC9.2: uma execução com CTs de squads diferentes é filtrável por squad
    (o front cruza result.testcase_id → testcases.squad_effective)."""
    ct_a = make_ct(client, "A", squad="alpha")
    ct_b = make_ct(client, "B", squad="beta")
    execution = client.post(
        "/api/v1/executions",
        json={"name": "Mista", "testcase_ids": [ct_a["id"], ct_b["id"]]},
    ).json()
    # o mapa CT→squad vem da lista de testcases (efetivo)
    by_id = {t["id"]: t["squad_effective"] for t in client.get("/api/v1/testcases").json()}
    in_board = [r["testcase_id"] for r in execution["results"]]
    alpha_only = [cid for cid in in_board if by_id[cid] == "alpha"]
    assert alpha_only == [ct_a["id"]]


def test_squads_endpoint_lists_known_squads(client):
    make_epic(client, "Pagamentos", squad="pagamentos")
    make_ct(client, "Avulso", squad="risco")
    squads = client.get("/api/v1/squads").json()["squads"]
    assert "pagamentos" in squads and "risco" in squads


def test_dashboard_filtered_by_squad(client):
    """SC9.3: métricas recalculam sobre o subconjunto do squad."""
    story_a = make_story(client, "SA", squad="alpha")
    story_b = make_story(client, "SB", squad="beta")
    ct_a = make_ct(client, "A ok", story=story_a["id"])
    ct_b = make_ct(client, "B ok", story=story_b["id"])
    execution = client.post(
        "/api/v1/executions",
        json={"name": "Reg", "testcase_ids": [ct_a["id"], ct_b["id"]]},
    ).json()
    for ct_id, status in ((ct_a["id"], "passed"), (ct_b["id"], "failed")):
        client.post(
            f"/api/v1/executions/{execution['id']}/results/{ct_id}/status",
            json={"status": status},
        )

    full = client.get("/api/v1/metrics/summary").json()
    assert full["pass_rate"]["denominator"] == 2  # A passed + B failed

    alpha = client.get("/api/v1/metrics/summary", params={"squad": "alpha"}).json()
    assert (alpha["pass_rate"]["numerator"], alpha["pass_rate"]["denominator"]) == (1, 1)
    assert alpha["execution_coverage"]["denominator"] == 1  # só o CT ready do alpha


def test_workspace_without_squads_is_unaffected(client):
    """SC9.4: retrocompatibilidade — sem nenhuma squad tudo segue funcional."""
    ct = make_ct(client, "Sem squad")
    fetched = client.get(f"/api/v1/testcases/{ct['id']}").json()
    assert fetched["squad"] is None and fetched["squad_effective"] is None
    assert client.get("/api/v1/squads").json()["squads"] == []
    summary = client.get("/api/v1/metrics/summary").json()
    assert summary["pass_rate"]["value"] is None  # sem execução, denominador explícito
