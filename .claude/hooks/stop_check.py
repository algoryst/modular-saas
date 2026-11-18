#!/usr/bin/env python3
import json, subprocess, sys

json.load(sys.stdin)  # consume hook input

changed = subprocess.run(["git", "status", "--porcelain"],
                         capture_output=True, text=True).stdout
if not any(ext in changed for ext in (".py", ".html", ".po", "pyproject.toml")):
    sys.exit(0)

result = subprocess.run(["make", "check"], capture_output=True, text=True)
if result.returncode != 0:
    tail = (result.stdout + result.stderr)[-3500:]
    print("make check failed. Fix these before finishing:\n" + tail, file=sys.stderr)
    sys.exit(2)
sys.exit(0)
