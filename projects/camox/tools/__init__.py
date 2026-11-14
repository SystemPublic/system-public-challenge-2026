"""Every public function defined in a module of this package is a tool, collected in TOOLS.
Adding a tool = adding a function. Loads the project's .env first so tools see their keys."""
import importlib
import os
import pkgutil
from pathlib import Path

_env = Path(__file__).resolve().parents[1] / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        if "=" in _line and not _line.lstrip().startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip("'\""))

TOOLS = [fn for m in pkgutil.iter_modules(__path__) if not m.name.startswith("_")
         for mod in [importlib.import_module(f"{__name__}.{m.name}")]
         for name, fn in vars(mod).items()
         if callable(fn) and not name.startswith("_") and getattr(fn, "__module__", None) == mod.__name__]
