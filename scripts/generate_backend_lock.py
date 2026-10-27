"""Write a transitive exact-version lock for the installed Python 3.12 env."""
from __future__ import annotations

import platform
import sys
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "backend/requirements.txt"
target = ROOT / "backend/requirements.lock"
pending: list[tuple[Requirement, set[str]]] = []
for raw in source.read_text(encoding="utf-8").splitlines():
    raw = raw.split("#", 1)[0].strip()
    if raw:
        req = Requirement(raw)
        pending.append((req, set(req.extras)))

locked: dict[str, tuple[str, str]] = {}
while pending:
    requirement, requested_extras = pending.pop()
    name = canonicalize_name(requirement.name)
    if name in locked:
        continue
    dist = metadata.distribution(requirement.name)
    version = dist.version
    if requirement.specifier and version not in requirement.specifier:
        raise SystemExit(f"Installed {name}=={version} does not satisfy {requirement}")
    locked[name] = (dist.metadata["Name"] or name, version)
    for raw_dependency in dist.requires or []:
        dependency = Requirement(raw_dependency)
        if dependency.marker and not any(
            dependency.marker.evaluate({"extra": extra}) for extra in (requested_extras or {""})
        ):
            continue
        if canonicalize_name(dependency.name) not in locked:
            pending.append((dependency, set(dependency.extras)))

header = (
    "# Exact transitive lock generated from backend/requirements.txt.\n"
    f"# Environment: Python {sys.version_info.major}.{sys.version_info.minor} / {platform.system()} {platform.machine()}.\n"
    "# Regenerate with: .venv/bin/python scripts/generate_backend_lock.py\n"
)
lines = [f"{display_name}=={version}" for _, (display_name, version) in sorted(locked.items())]
target.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {len(lines)} exact packages to {target.relative_to(ROOT)}")
