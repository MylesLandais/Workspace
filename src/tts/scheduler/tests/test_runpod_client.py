import pytest
from src.runpod.client import RunpodClient


class DummyProc:
    def __init__(self, returncode=0, out="ok", err=""):
        self.returncode = returncode
        self._out = out
        self._err = err

    def communicate(self):
        return (self._out, self._err)


def test_dry_run_favorite(capsys):
    c = RunpodClient(runpodctl_path="/usr/local/bin/runpodctl")
    rc, out, err = c.favorite_template("comfy-template", dry_run=True)
    assert rc == 0
    assert "DRY_RUN:" in out


def test_create_and_delete_dry_run(capsys):
    c = RunpodClient()
    rc, out, err = c.create_deployment("comfy-template", gpu_type="3090", name="test-deploy", extra_args=["--scale", "1"], dry_run=True)
    assert rc == 0
    assert "--gpu" in out
    rc2, out2, err2 = c.delete_deployment("test-deploy", dry_run=True)
    assert rc2 == 0
    assert "deployment delete test-deploy" in out2


def test_real_run_subprocess(monkeypatch):
    # Ensure subprocess is called when dry_run=False by monkeypatching Popen
    def fake_popen(cmd, stdout, stderr, text):
        assert cmd[0] == "runpodctl"
        return DummyProc(returncode=0, out="created", err="")

    monkeypatch.setattr("subprocess.Popen", fake_popen)
    c = RunpodClient()
    rc, out, err = c.create_deployment("comfy-template", name="rtest", dry_run=False)
    assert rc == 0
    assert "created" in out
