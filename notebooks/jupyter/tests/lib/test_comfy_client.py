"""Tests for lib.comfy.client module."""

from lib.comfy.client import ComfyClient


class TestComfyClient:
    """Test ComfyClient interface."""

    def test_init_default_url(self):
        client = ComfyClient()
        assert "127.0.0.1" in client.base_url
        assert "8188" in client.base_url

    def test_init_custom_url(self):
        client = ComfyClient(host="http://gpu-server", port=9000)
        assert "gpu-server" in client.base_url
        assert "9000" in client.base_url

    def test_build_tryon_workflow_returns_dict(self):
        client = ComfyClient()
        wf = client.build_tryon_workflow("/img/person.png", "/img/garment.png", "/out/result.png")
        assert isinstance(wf, dict)
        assert "nodes" in wf

    def test_build_tryon_workflow_with_kwargs(self):
        client = ComfyClient()
        wf = client.build_tryon_workflow(
            "/img/p.png", "/img/g.png", "/out/r.png",
            prompt="red dress", steps=16
        )
        nodes = wf["nodes"]
        assert any(n.get("args", {}).get("steps") == 16 for n in nodes)

    def test_submit_workflow_returns_string(self):
        client = ComfyClient()
        wf = {"nodes": []}
        run_id = client.submit_workflow(wf)
        assert isinstance(run_id, str)

    def test_poll_result_returns_string(self):
        client = ComfyClient()
        result = client.poll_result("run-1234")
        assert isinstance(result, str)
