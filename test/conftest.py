import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


@pytest.fixture
def api_server():
    observed = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            observed.append(dict(self.headers.items()))
            if self.path.startswith("/slow"):
                time.sleep(0.1)
            proxy = self.headers.get("RealSwarm")
            data = {
                "network_name": "Anonymous network" if proxy else "Libra TESTNET",
                "url": "http://47.254.29.109:33333" if proxy else "https://client.testnet.libra.org",
                "core_code_address": "0" * 31 + "1",
                "start_time": 1,
                "latest_time": 2,
                "total_transactions": 1,
            }
            body = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("API-Server", "MoveOnLibra-API")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Libra-network", proxy or "testnet")
            self.send_header("Latest-Version", "1")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass  # The read-timeout test intentionally closes its connection.

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:{}".format(server.server_port), observed
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()
