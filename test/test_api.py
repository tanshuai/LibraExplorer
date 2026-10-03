import os
import requests, json
import pytest
import pdb

import app


def test_mol_api(api_server):
    host, observed = api_server
    url = "/v1/libra/about"
    params = {}
    headers = app.gen_api_header(False, "explorer.moveonlibra.com")
    assert len(headers.items()) == 1
    assert bool(headers.get("Authorization"))
    headers["Authorization"] = "Bearer unit-only-synthetic"
    response = requests.get(host+url, params=params, headers=headers, timeout=1)
    assert observed[-1]["Authorization"] == "Bearer unit-only-synthetic"
    assert response.status_code == 200
    assert response.headers["API-Server"] == "MoveOnLibra-API"
    assert response.headers['Access-Control-Allow-Origin'] == "*"
    assert response.headers["Libra-network"] == "testnet"
    assert int(response.headers["Latest-Version"]) >= 0
    data = json.loads(response.content.decode('utf-8-sig'))
    assert data['network_name'] == "Libra TESTNET"
    assert data["url"] == "https://client.testnet.libra.org"
    assert data["core_code_address"] == "0"*31 + "1"
    assert data["start_time"] <= data["latest_time"]
    assert data["total_transactions"] >= 1


def test_mol_api_proxy(api_server):
    host, observed = api_server
    url = "/v1/libra/about"
    params = {}
    headers = app.gen_api_header(False, "47.254.29.109-33333.explorer.moveonlibra.com")
    assert headers["RealSwarm"] == "47.254.29.109-33333"
    assert bool(headers.get("Authorization"))
    headers["Authorization"] = "Bearer unit-only-synthetic"
    response = requests.get(host+url, params=params, headers=headers, timeout=1)
    assert observed[-1]["Authorization"] == "Bearer unit-only-synthetic"
    assert response.status_code == 200
    assert response.headers["API-Server"] == "MoveOnLibra-API"
    assert response.headers['Access-Control-Allow-Origin'] == "*"
    assert observed[-1]["RealSwarm"] == "47.254.29.109-33333"
    assert response.headers["Libra-Network"] == "47.254.29.109-33333"
    assert int(response.headers["Latest-Version"]) >= 0
    data = json.loads(response.content.decode('utf-8-sig'))
    assert data['network_name'] == "Anonymous network"
    assert data["url"] == "http://47.254.29.109:33333"
    assert data["start_time"] <= data["latest_time"]
    assert data["total_transactions"] >= 1


@pytest.mark.parametrize("status, expected_attempts", [("200", 1), ("500-then-200", 2)])
def test_actual_client_parses_http_response(monkeypatch, api_server, status, expected_attempts):
    host, observed = api_server
    totals = []
    monkeypatch.setattr(app, "api_host", lambda: host)
    monkeypatch.setattr(app, "jwt_header", lambda: {"Authorization": "Bearer unit-only-synthetic", "X-Fixture-Status": status})
    monkeypatch.setattr(app, "update_total", totals.append)
    with app.app.test_request_context("/"):
        data = app.move_on_libra_api("/v1/libra/about")
    assert data["network_name"] == "Libra TESTNET"
    assert totals == [2]
    assert len(observed) == expected_attempts
    assert all(h["Authorization"] == "Bearer unit-only-synthetic" for h in observed)


def test_actual_client_reports_missing_resource(monkeypatch, api_server):
    host, observed = api_server
    monkeypatch.setattr(app, "api_host", lambda: host)
    monkeypatch.setattr(app, "jwt_header", lambda: {"Authorization": "Bearer unit-only-synthetic", "X-Fixture-Status": "404"})
    with app.app.test_request_context("/"):
        assert app.move_on_libra_api("/missing") is None
    assert len(observed) == 1


@pytest.mark.parametrize("status, expected_attempts", [("403", 1), ("500", 2)])
def test_actual_client_rejects_bad_http_status(monkeypatch, api_server, status, expected_attempts):
    from werkzeug.exceptions import InternalServerError

    host, observed = api_server
    monkeypatch.setattr(app, "api_host", lambda: host)
    monkeypatch.setattr(app, "jwt_header", lambda: {"Authorization": "Bearer unit-only-synthetic", "X-Fixture-Status": status})
    with app.app.test_request_context("/"):
        with pytest.raises(InternalServerError):
            app.move_on_libra_api("/v1/libra/about")
    assert len(observed) == expected_attempts
