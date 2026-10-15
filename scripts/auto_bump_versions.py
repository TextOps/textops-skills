#!/usr/bin/env python3
"""
Bumps the version of every skill that changed between two commits without a
version bump of its own. Used by the release workflow on each push to main, so
a merged PR that forgot to bump still ships as a new version (installed copies
only see an update when the version moves).

Usage: python auto_bump_versions.py <before_sha> <after_sha>
Prints the SKILL.md files it bumped, one per line (nothing if none).
A skill is a top-level folder with a SKILL.md. New skills are left alone.
"""

import os
import re
import subprocess
import sys

VERSION_RE = re.compile(r'version:\s*["\']?(\d+\.\d+\.\d+)')
ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)


def version_at(sha, path):
    res = git("show", f"{sha}:{path}")
    if res.returncode != 0:
        return None
    m = VERSION_RE.search(res.stdout)
    return m.group(1) if m else None


def main():
    if len(sys.argv) != 3:
        print("Usage: auto_bump_versions.py <before_sha> <after_sha>", file=sys.stderr)
        sys.exit(1)
    before, after = sys.argv[1], sys.argv[2]

    changed = git("diff", "--name-only", before, after)
    if changed.returncode != 0:
        print(f"git diff failed: {changed.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    skills = sorted({p.split("/", 1)[0] for p in changed.stdout.splitlines() if "/" in p})
    for skill in skills:
        skill_md = f"{skill}/SKILL.md"
        if not os.path.exists(os.path.join(ROOT, skill_md)):
            continue
        old, new = version_at(before, skill_md), version_at(after, skill_md)
        if old is None or new is None or old != new:
            continue  # new skill, no version field, or already bumped
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "bump_version.py"),
                        os.path.join(ROOT, skill_md)], check=True, stdout=sys.stderr)
        print(skill_md)


if __name__ == "__main__":
    main()
