#!/usr/bin/env python3
import json, re, subprocess, sys

data = json.load(sys.stdin)
path = (data.get("tool_input") or {}).get("file_path", "")
if not path:
    sys.exit(0)

def block(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(2)

def tracked(p: str) -> bool:
    return subprocess.run(["git", "ls-files", "--error-unmatch", p],
                          capture_output=True).returncode == 0

if re.search(r"/migrations/\d{4}_.*\.py$", path) and tracked(path):
    block("Blocked: committed migrations are immutable. Create a new migration instead.")

if re.search(r"(^|/)\.claude/(settings\.json|hooks/)", path):
    block("Blocked: Claude guardrails cannot be edited by Claude. Ask the user to change them.")

if re.search(r"(^|/)docs/(ARCHITECTURE|PRODUCTS|LEGAL|ENFORCEMENT)\.md$", path):
    block("Blocked: locked plan documents. Propose the change to the user instead.")

if re.search(r"(^|/)\.env(\..*)?$", path):
    block("Blocked: environment files are managed by the user.")

sys.exit(0)
