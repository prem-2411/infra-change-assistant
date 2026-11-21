import app.agent as agent_module
from conftest import REQUEST_BODY, FakeClient, good_plan


def create(client, hdr, who="eng", **over):
    r = client.post("/requests", json={**REQUEST_BODY, **over}, headers=hdr(who))
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_input_validation(client, hdr):
    for bad in ({"type": "delete_everything"}, {"justification": "short"}, {"target": ""},
                {"risk_level": "extreme"}, {"target": "x" * 201}, {"extra": "field"}):
        r = client.post("/requests", json={**REQUEST_BODY, **bad}, headers=hdr("eng"))
        assert r.status_code == 422, bad


def test_sql_injection_text_is_stored_literally(client, hdr):
    rid = create(client, hdr, target="x'; DROP TABLE requests;--")
    assert client.get(f"/requests/{rid}", headers=hdr("eng")).json()["target"] == "x'; DROP TABLE requests;--"


def test_engineers_only_see_their_own_requests(client, hdr):
    rid = create(client, hdr, "eng")
    assert [r["id"] for r in client.get("/requests", headers=hdr("eng")).json()] == [rid]
    assert client.get("/requests", headers=hdr("eng2")).json() == []
    assert client.get(f"/requests/{rid}", headers=hdr("eng2")).status_code == 404
    assert client.get(f"/requests/{rid}", headers=hdr("appr")).status_code == 200


def test_role_checks(client, hdr):
    assert client.post("/requests", json=REQUEST_BODY, headers=hdr("appr")).status_code == 403
    rid = create(client, hdr)
    body = {"decision": "approved", "comment": "ok"}
    assert client.post(f"/requests/{rid}/decision", json=body, headers=hdr("eng")).status_code == 403
    assert client.post(f"/requests/{rid}/decision", json=body, headers=hdr("admin")).status_code == 403
    assert client.get("/audit", headers=hdr("eng")).status_code == 403
    assert client.get("/metrics", headers=hdr("appr")).status_code == 403
    assert client.post("/policies", json={"title": "t", "rule_text": "r", "category": "c"},
                       headers=hdr("appr")).status_code == 403


def test_cannot_decide_before_review(client, hdr):
    rid = create(client, hdr)
    r = client.post(f"/requests/{rid}/decision", json={"decision": "approved", "comment": "ok"}, headers=hdr("appr"))
    assert r.status_code == 409


def test_full_flow_with_llm_fallback(client, hdr):
    rid = create(client, hdr)
    reviewed = client.post(f"/requests/{rid}/review", headers=hdr("eng")).json()  # no API key configured
    assert reviewed["status"] == "manual_review"
    assert reviewed["reviews"][0]["status"] == "failed" and reviewed["reviews"][0]["recommendation"] == "escalate"
    assert reviewed["reviews"][0]["risk_assessment"] == "high"

    decided = client.post(f"/requests/{rid}/decision", json={"decision": "rejected", "comment": "Violates policy"},
                          headers=hdr("appr")).json()
    assert decided["status"] == "rejected" and decided["decisions"][0]["comment"] == "Violates policy"
    # a decided request is final
    again = client.post(f"/requests/{rid}/decision", json={"decision": "approved", "comment": "x"}, headers=hdr("appr"))
    assert again.status_code == 409
    assert client.post(f"/requests/{rid}/review", headers=hdr("eng")).status_code == 409

    actions = [e["action"] for e in client.get("/audit", headers=hdr("admin")).json()]
    for expected in ("request_submitted", "ai_review", "request_rejected"):
        assert expected in actions


def test_full_flow_with_llm_success(client, hdr, monkeypatch):
    rid = create(client, hdr, type="add_server", target="dev-vm-1", risk_level="low",
                 justification="Dev VM from the hardened image for feature testing.")
    fake = FakeClient([good_plan(rid)])
    monkeypatch.setattr(agent_module, "get_client", lambda: fake)
    reviewed = client.post(f"/requests/{rid}/review", headers=hdr("eng")).json()
    assert reviewed["status"] == "reviewed" and reviewed["reviews"][0]["status"] == "ok"
    done = client.post(f"/requests/{rid}/decision", json={"decision": "approved", "comment": "Looks fine"},
                       headers=hdr("appr")).json()
    assert done["status"] == "approved"


def test_dashboard(client, hdr):
    rid = create(client, hdr)
    client.post(f"/requests/{rid}/review", headers=hdr("eng"))
    client.post(f"/requests/{rid}/decision", json={"decision": "approved", "comment": "ok"}, headers=hdr("appr"))
    data = client.get("/dashboard", headers=hdr("appr")).json()
    assert data["total"] == 1 and data["by_status"] == {"approved": 1} and data["avg_review_seconds"] is not None
    assert client.get("/dashboard", headers=hdr("eng")).status_code == 403


def test_health_is_public(client):
    assert client.get("/health").json() == {"status": "ok"}
