#!/usr/bin/env python3
import json, subprocess, sys

data = json.load(sys.stdin)
path = (data.get("tool_input") or {}).get("file_path", "")
if path.endswith(".py"):
    subprocess.run(["black", "-q", path])
    subprocess.run(["isort", "-q", path])
sys.exit(0)
