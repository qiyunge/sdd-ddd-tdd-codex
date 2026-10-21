"""Validate the built, non-editable wheel from outside the checkout."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_installed_wheel_resources(tmp_path):
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV")
    }

    def run(*cmd, cwd=tmp_path):
        result = subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True)
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    wheel_dir = tmp_path / "wheels"
    run("uv", "build", "--wheel", "--out-dir", str(wheel_dir), cwd=ROOT)
    wheels = list(wheel_dir.glob("*.whl"))
    assert len(wheels) == 1
    isolated = tmp_path / "isolated"
    run("uv", "venv", "--python", sys.executable, str(isolated))
    python = isolated / "bin/python"
    run("uv", "pip", "install", "--python", str(python), "--no-deps", str(wheels[0]))
    script = """
import json
from pathlib import Path
from importlib.resources import files
import enrollment
resources={}
for package,name in [('enrollment.adapters.graphql','schema.graphqls'),('enrollment.adapters.persistence','schema.sql')]:
    path=files(package).joinpath(name)
    resources[name]={'origin':str(path),'content':path.read_text()}
print(json.dumps({'package':enrollment.__file__,'resources':resources}))
"""
    state = json.loads(run(str(python), "-I", "-c", script))
    assert Path(state["package"]).is_relative_to(isolated)
    assert not Path(state["package"]).is_relative_to(ROOT)
    for name, package in [
        ("schema.graphqls", "graphql"),
        ("schema.sql", "persistence"),
    ]:
        resource = state["resources"][name]
        assert Path(resource["origin"]).is_relative_to(isolated)
        assert (
            resource["content"]
            == (ROOT / f"src/enrollment/adapters/{package}/{name}").read_text()
        )
