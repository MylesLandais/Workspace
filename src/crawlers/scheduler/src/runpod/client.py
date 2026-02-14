import shlex
import subprocess
from typing import List, Optional, Tuple


class RunpodClient:
    """Minimal wrapper to call `runpodctl` from Python.

    Methods:
    - favorite_template(template_name)
    - create_deployment(template_name, gpu_type, name, extra_args)
    - delete_deployment(name)

    All methods accept `dry_run=True` to only print the command instead of executing it.
    """

    def __init__(self, runpodctl_path: str = "runpodctl"):
        self.runpodctl = runpodctl_path

    def _run(self, args: List[str], dry_run: bool = True) -> Tuple[int, str, str]:
        cmd = [self.runpodctl] + args
        cmd_s = " ".join(shlex.quote(p) for p in cmd)
        if dry_run:
            msg = f"DRY_RUN: {cmd_s}"
            print(msg)
            return 0, msg, ""
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate()
        return proc.returncode, out, err

    def favorite_template(self, template_name: str, dry_run: bool = True) -> Tuple[int, str, str]:
        return self._run(["template", "favorite", template_name], dry_run=dry_run)

    def create_deployment(self, template_name: str, gpu_type: str = "3090", name: Optional[str] = None, extra_args: Optional[List[str]] = None, dry_run: bool = True) -> Tuple[int, str, str]:
        args = ["deployment", "create", template_name]
        if name:
            args += ["--name", name]
        if gpu_type:
            args += ["--gpu", gpu_type]
        if extra_args:
            args += extra_args
        return self._run(args, dry_run=dry_run)

    def delete_deployment(self, name: str, dry_run: bool = True) -> Tuple[int, str, str]:
        return self._run(["deployment", "delete", name], dry_run=dry_run)
