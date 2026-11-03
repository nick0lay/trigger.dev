import json
from types import SimpleNamespace

import pytest

import railway_client
from config import Config
from railway_client import RailwayClient


@pytest.fixture
def client_with(monkeypatch):
    def make(deployments=(), logs=None, upsert_fails=False):
        logs = logs or {}
        calls = SimpleNamespace(graphql=[], upserts=[])

        def fake_request(self, query, variables=None):
            variables = variables or {}
            calls.graphql.append(query)
            if "variableCollectionUpsert" in query:
                if upsert_fails:
                    raise Exception("boom")
                calls.upserts.append(variables["input"]["variables"])
                return {"variableCollectionUpsert": True}
            if "deploymentLogs" in query:
                text = logs.get(variables["deploymentId"], "")
                return {"deploymentLogs": [{"message": line} for line in text.splitlines()]}
            if "deployments(" in query:
                # API order is not trusted: return oldest first on purpose.
                nodes = sorted(deployments, key=lambda d: d[2])
                return {"deployments": {"edges": [
                    {"node": {"id": i, "status": s, "createdAt": t}} for i, s, t in nodes]}}
            if "services" in query or "service" in query:
                return {"project": {"services": {"edges": [
                    {"node": {"id": "svc-web", "name": Config.WEBAPP_SERVICE_NAME}}]}}}
            raise AssertionError(f"unexpected query: {query[:80]}")

        monkeypatch.setattr(RailwayClient, "_graphql_request", fake_request)
        monkeypatch.setattr(RailwayClient, "get_service_id", lambda self, name: "svc-web")
        monkeypatch.setattr(Config, "TRIGGER_WORKER_TOKEN", "")
        monkeypatch.setattr(Config, "RAILWAY_SERVICE_ID", "svc-ops")
        return RailwayClient(), calls
    return make


DEPLOYS = [("d3", "SUCCESS", "2026-11-01T20:40:00Z"),
           ("d2", "FAILED", "2026-11-01T20:29:00Z"),
           ("d1", "REMOVED", "2026-11-01T20:22:00Z")]


def test_list_deployment_ids_newest_first(client_with):
    c, _ = client_with(deployments=DEPLOYS)
    assert c.list_deployment_ids(Config.WEBAPP_SERVICE_NAME, 20) == ["d3", "d2", "d1"]


def test_token_found_in_removed_deployment(client_with):
    c, calls = client_with(deployments=DEPLOYS, logs={"d1": "worker token tr_wgt_abc123"})
    assert c.extract_worker_token() == "tr_wgt_abc123"
    assert calls.upserts == [{"TRIGGER_WORKER_TOKEN": "tr_wgt_abc123"}]


def test_newest_deployment_wins(client_with):
    c, _ = client_with(deployments=DEPLOYS,
                       logs={"d3": "tr_wgt_new", "d1": "tr_wgt_old"})
    assert c.extract_worker_token() == "tr_wgt_new"


def test_no_token_in_any_deployment(client_with):
    c, calls = client_with(deployments=DEPLOYS, logs={"d2": "nothing here"})
    assert c.extract_worker_token() is None
    assert calls.upserts == []


def test_persist_skipped_without_service_id(monkeypatch, client_with):
    c, calls = client_with()
    monkeypatch.setattr(Config, "RAILWAY_SERVICE_ID", "")
    assert c.persist_worker_token("tr_wgt_x") is False
    assert calls.upserts == []


def test_persist_failure_does_not_raise(client_with):
    c, _ = client_with(upsert_fails=True)
    assert c.persist_worker_token("tr_wgt_x") is False


def test_env_token_not_persisted(monkeypatch, client_with):
    c, calls = client_with(deployments=DEPLOYS, logs={"d1": "tr_wgt_abc123"})
    monkeypatch.setattr(Config, "TRIGGER_WORKER_TOKEN", "tr_wgt_env")
    assert c.extract_worker_token() == "tr_wgt_env"
    assert calls.graphql == []


def test_token_never_logged_in_full(capsys, client_with):
    c, _ = client_with(deployments=DEPLOYS, logs={"d1": "tr_wgt_abc123"})
    c.extract_worker_token()
    assert "tr_wgt_abc123" not in capsys.readouterr().out
