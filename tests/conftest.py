import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "plugins" / "dh-strumenti" / "skills" / "crea-skill" / "scripts"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


check_skills = _load("check_skills")
scaffold = _load("scaffold")


@pytest.fixture
def market(tmp_path):
    """Copia del marketplace reale, da modificare nei test."""
    dst = tmp_path / "market"
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", ".pytest_cache"))
    return dst
