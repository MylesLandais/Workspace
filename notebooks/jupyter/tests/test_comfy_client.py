from typing import Optional, Dict, Any

from comfy.client import ComfyClient


class FakeResp:
    def __init__(self, status_code: int = 200, json_data: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"HTTP {self.status_code}")


class FakeSession:
    """A tiny fake requests-like session for unit tests.

    It records calls and returns preset responses based on the URL.
    """

    def __init__(self):
        self._responses = {}
        self.calls = []

    def add_response(self, method: str, url: str, status: int = 200, json_data: Optional[Dict[str, Any]] = None):
        self._responses[(method.upper(), url)] = FakeResp(status, json_data)

    def post(self, url: str, json=None, timeout: Optional[float] = None):
        self.calls.append(("POST", url, json))
        return self._responses.get(("POST", url), FakeResp(500, {}))

    def get(self, url: str, timeout: Optional[float] = None):
        self.calls.append(("GET", url))
        return self._responses.get(("GET", url), FakeResp(404, {}))


def test_submit_and_poll_success():
    fs = FakeSession()
    client = ComfyClient(host="http://testserver", port=80, session=fs)

    wf = client.build_tryon_workflow("/in/p.png", "/in/g.png", "/out/o.png", prompt="hello")
    run_id = "r-1"
    result_path = "/out/o.png"

    fs.add_response("POST", "http://testserver:80/run_workflow", status=200, json_data={"run_id": run_id})
    fs.add_response("GET", f"http://testserver:80/results/{run_id}", status=200, json_data={"result_path": result_path})

    assert client.submit_workflow(wf) == run_id
    assert client.poll_result(run_id, timeout=1, poll_interval=0.01) == result_path


def test_poll_timeout_returns_none():
    fs = FakeSession()
    client = ComfyClient(host="http://testserver", port=80, session=fs)
    run_id = "r-timeout"

    # No GET response added -> default is 404 from FakeSession
    got = client.poll_result(run_id, timeout=0.05, poll_interval=0.01)
    assert got is None
import json
import time

import responses
from comfy.client import ComfyClient


def test_submit_and_poll_success():
    client = ComfyClient(host="http://testserver", port=80, session=None)

    # Prepare a workflow and expected run_id/result
    workflow = client.build_tryon_workflow("/in/person.png", "/in/garment.png", "/out/out.png", prompt="hi")
    run_id = "run-xyz"
    result_path = "/out/out.png"

    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, "http://testserver:80/run_workflow", json={"run_id": run_id}, status=200)

        # First GET returns 404 (not ready), second returns 200
        rsps.add(responses.GET, f"http://testserver:80/results/{run_id}", status=404)
        rsps.add(responses.GET, f"http://testserver:80/results/{run_id}", json={"result_path": result_path}, status=200)

        returned_run = client.submit_workflow(workflow)
        assert returned_run == run_id

        # poll_result should retry and eventually return the result_path
        got = client.poll_result(run_id, timeout=5, poll_interval=0.01)
        assert got == result_path


def test_poll_timeout():
    client = ComfyClient(host="http://testserver", port=80)
    run_id = "run-timeout"

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f"http://testserver:80/results/{run_id}", status=404)

        # Should time out and return None
        got = client.poll_result(run_id, timeout=0.1, poll_interval=0.01)
        assert got is None
