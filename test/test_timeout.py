import pytest
import requests
from werkzeug.exceptions import InternalServerError

import app


def test_actual_http_read_timeout(api_server):
    host, _ = api_server
    with pytest.raises(requests.exceptions.ReadTimeout):
        requests.get(host + "/slow", timeout=(1, 0.01))


@pytest.mark.parametrize("error_type", [requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError])
def test_application_reports_transport_error(monkeypatch, api_server, error_type):
    host, _ = api_server
    attempts = []

    def fail(url, **kwargs):
        attempts.append((url, kwargs))
        raise error_type("controlled transport failure")

    monkeypatch.setattr(app, "api_host", lambda: host)
    monkeypatch.setattr(app.requests, "get", fail)
    with app.app.test_request_context("/", base_url="http://explorer.moveonlibra.com"):
        with pytest.raises(InternalServerError):
            app.move_on_libra_api("/v1/libra/about")
    assert len(attempts) == 1
    assert attempts[0][0] == host + "/v1/libra/about"
    assert attempts[0][1]["timeout"] == 10
