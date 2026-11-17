#!/usr/bin/env python3
"""Install the fleet's shared skills for Codex, Claude Code, and shared agents."""

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile


def manifest(directory):
    result = {}
    for entry in sorted(directory.rglob("*")):
        if entry.is_symlink():
            raise ValueError(f"Unexpected symlink inside skill: {entry}")
        if entry.is_file():
            result[str(entry.relative_to(directory))] = hashlib.sha256(entry.read_bytes()).hexdigest()
    return result


def linked_to(link, target):
    return link.is_symlink() and Path(os.path.abspath(link.parent / os.readlink(link))) == target


def publish_link(link, target):
    if linked_to(link, target):
        return
    link.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".fleet-skill-", dir=link.parent) as temp:
        staged = Path(temp) / "link"
        staged.symlink_to(target, target_is_directory=True)
        os.replace(staged, link)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "apply", "doctor"), nargs="?", default="plan")
    args = parser.parse_args()
    source_root = Path(__file__).resolve().parent / "skills"
    home = Path.home()
    fleet_root = Path(os.environ.get("FLEET_HOME", str(home / ".local/share/fleet"))).expanduser()
    if not fleet_root.is_absolute():
        parser.error("FLEET_HOME must be an absolute path")
    installed_root = fleet_root / "skills"
    discovery_roots = (home / ".codex/skills", home / ".claude/skills", home / ".agents/skills")
    missing = False
    try:
        skills = sorted(source_root.iterdir())
        if not skills:
            raise ValueError("No shared skills in this checkout")
        for source in skills:
            if source.is_symlink() or not source.is_dir() or not (source / "SKILL.md").is_file():
                raise ValueError(f"Invalid source skill: {source}")
            expected = manifest(source)
            fingerprint = hashlib.sha256(repr(sorted(expected.items())).encode()).hexdigest()
            version = installed_root / ".versions" / source.name / fingerprint
            canonical = installed_root / source.name
            links = [root / source.name for root in discovery_roots]
            if canonical.exists() or canonical.is_symlink():
                if not canonical.is_symlink() or canonical.resolve().parent != version.parent.resolve():
                    raise ValueError(f"Existing skill is outside this installer's version directory: {canonical}")
            for link in links:
                if (link.exists() or link.is_symlink()) and not linked_to(link, canonical):
                    raise ValueError(f"Existing skill requires review before installation: {link}")
            version_ok = version.is_dir() and not version.is_symlink() and manifest(version) == expected
            ready = version_ok and linked_to(canonical, version) and all(linked_to(p, canonical) for p in links)
            print(f"{source.name} {fingerprint[:12]} {'installed' if ready else 'needs installation'}")
            if args.action == "plan":
                for link in links:
                    print(f"  {link}")
            elif args.action == "apply":
                if not version_ok:
                    if version.exists() or version.is_symlink():
                        raise ValueError(f"Installed version has local changes: {version}")
                    version.parent.mkdir(parents=True, exist_ok=True)
                    with tempfile.TemporaryDirectory(prefix=".stage-", dir=version.parent) as temp:
                        staged = Path(temp) / source.name
                        shutil.copytree(source, staged)
                        if manifest(staged) != expected:
                            raise ValueError(f"Source changed during installation: {source}")
                        staged.rename(version)
                publish_link(canonical, version)
                for link in links:
                    publish_link(link, canonical)
                print("  Verified shared version and published all three discovery links")
            else:
                missing = missing or not ready
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return int(missing)


if __name__ == "__main__":
    sys.exit(main())
