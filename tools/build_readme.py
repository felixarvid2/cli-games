#!/usr/bin/env python3
"""Regenerate README.md with screenshots taken from the real UI.

Run after changing the layout or the starting economy:
    python3 tools/build_readme.py
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER = os.path.join(ROOT, "tools", "render.py")

SHOTS = {
    "flight": ["--keys", "\\n~R~E", "--contacts", "2"],
    "chart": ["--keys", "\\n"],
    "docked": ["--keys", "\\n", "--start-docked"],
    "buy": ["--keys", "\\n~E", "--start-docked"],
    "flight100": ["--rows", "32", "--cols", "100", "--keys", "\\n~R~E",
                  "--contacts", "3"],
}

TEMPLATE = open(os.path.join(ROOT, "tools", "readme_template.md")).read()


def shoot(name):
    out = subprocess.run([sys.executable, RENDER] + SHOTS[name], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    lines = out.split("\n")
    assert lines and lines[0].startswith("# "), lines[:1]
    return "\n".join(lines[1:]).rstrip("\n")


if __name__ == "__main__":
    shots = {name: shoot(name) for name in SHOTS}
    open(os.path.join(ROOT, "README.md"), "w").write(TEMPLATE.format(**shots))
    print("README.md written", shots.keys())
