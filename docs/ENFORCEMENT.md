# ENFORCEMENT.md
# Deterministic guardrails for Claude Code (hooks, deny rules, make targets)

Why this file exists: Anthropic's Claude Code best-practices page says CLAUDE.md is guidance the model can decide not to follow, while hooks, deny rules and CI are enforced by the harness. Anything that must never be violated goes here. CLAUDE.md stays short and holds only guidance and commands.

Status: written 18 Nov 2026 from the Claude Code docs and the tool docs listed at the end. The hook JSON shapes follow the documented format (tool input on stdin, exit code 2 blocks and returns stderr to Claude). **Test each hook once on day one** (instructions at the bottom). Items marked (recommended) are my additions, not from a source.

Keep the enforced set small: every hook occasionally misfires and has to be maintained.

---

## 1. Files to create

```
CLAUDE.md                       (from the CLAUDE.md deliverable)
.claude/settings.json           (section 2)
.claude/hooks/guard_paths.py    (section 3)
.claude/hooks/format.py         (section 4)
.claude/hooks/stop_check.py     (section 5)
Makefile                        (section 6)
.importlinter                   (section 7)
.gitignore                      add: CLAUDE.local.md, .claude/settings.local.json
```

Commit `.claude/settings.json` and hooks so the rules travel with the repo.

## 2. `.claude/settings.json`

```json
{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Edit(./.env)",
      "Edit(./.env.*)",
      "Bash(git push*)",
      "Bash(git reset --hard*)",
      "Bash(git clean*)",
      "Bash(rm -rf*)",
      "Bash(*delete_tenant*)",
      "Bash(*DROP SCHEMA*)",
      "Bash(*dropdb*)",
      "Bash(curl*|*sh*)"
    ],
    "ask": [
      "Bash(pip install*)",
      "Bash(pip uninstall*)",
      "Bash(poetry add*)",
      "Bash(uv add*)",
      "Bash(npm install*)",
      "Bash(git commit*)",
      "Edit(./.github/**)",
      "Edit(./Dockerfile*)",
      "Edit(./docker-compose*)",
      "Edit(./pyproject.toml)",
      "Edit(./.importlinter)",
      "Edit(./Makefile)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/guard_paths.py\"" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/format.py\"" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/stop_check.py\"", "timeout": 600 }
        ]
      }
    ]
  }
}
```

Notes:
- `deny` rules hold in every permission mode. `ask` makes Claude pause for your approval. Pattern syntax for Bash and Edit rules follows the permissions docs; confirm each rule with `/permissions` after creating the file.
- A deny rule on `WebFetch` does not stop `curl` unless the sandbox is on. Turn on `/sandbox` for strict filesystem and network limits (recommended).
- `git commit` is on `ask` so you can review commits. If that is too noisy once you trust the flow, remove it. `git push` stays denied: you push yourself.
- Personal overrides go in `.claude/settings.local.json` (gitignored).
- Do not run with `bypassPermissions` outside a disposable container.

## 3. `.claude/hooks/guard_paths.py` (PreToolUse, blocks with exit 2)

Blocks: editing an already-committed migration; editing hooks or Claude settings (no self-modification); editing the CI coverage and lint thresholds without you; editing locked plan documents other than PROGRESS.md.

```python
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
```

## 4. `.claude/hooks/format.py` (PostToolUse, runs after every edit)

```python
#!/usr/bin/env python3
import json, subprocess, sys

data = json.load(sys.stdin)
path = (data.get("tool_input") or {}).get("file_path", "")
if path.endswith(".py"):
    subprocess.run(["black", "-q", path])
    subprocess.run(["isort", "-q", path])
sys.exit(0)
```

## 5. `.claude/hooks/stop_check.py` (Stop, enforces the gate)

Runs only when Python or template files changed. Exit 2 sends the failures back to Claude, which keeps working until the gate passes. Claude Code overrides repeated blocks after a cap (documented as 8 consecutive stops without a tool call), so this cannot loop forever.

```python
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
```

(No loop guard is needed: rely on the documented block cap.)

## 6. `Makefile` targets (create in Phase 0)

```
check: lint types security migrations-check test
lint:            black --check . && isort --check . && flake8 && lint-imports
types:           mypy .
security:        bandit -q -r apps -c pyproject.toml && pip-audit
migrations-check: python manage.py check && python manage.py makemigrations --check --dry-run
test:            pytest --cov --cov-fail-under=<threshold from pyproject>
fmt:             black . && isort .
```

Coverage gates (90 / 80 / 80 / 70) are configured in `pyproject.toml` and the CI workflow. `pyproject.toml` is on the `ask` list so thresholds cannot be lowered silently.

## 7. `.importlinter` (recommended)

Import Linter turns "feature apps never import each other" and "layers" into a failing check instead of a hope. Starter contracts (adapt app names):

```
[importlinter]
root_package = apps

[importlinter:contract:feature-independence]
name = Feature apps are independent
type = independence
modules =
    apps.contacts
    apps.deals
    apps.quotes
    apps.esignature
    apps.invoicing
    apps.projects
    apps.orders

[importlinter:contract:layers]
name = Layered architecture inside each app
type = layers
layers =
    views
    forms
    services
    repositories
    models
containers =
    apps.contacts
    apps.deals
    apps.quotes
```

Extend `containers` as apps are added. Add a contract forbidding `core` from importing feature apps.

## 8. Extra flake8 and CI guards (recommended)

- `flake8-bugbear`, `flake8-django`, `flake8-print` (no stray prints), `flake8-bandit` optional.
- Custom grep check in CI: fail on `float(` inside money paths, `mark_safe(`/`|safe` without an `# allow-safe:` reason, `datetime.now(` in services, literal `"art. 293 B"` outside the country pack, and `DEBUG = True` outside local settings.
- CI runs `python manage.py check --deploy` with production settings.
- Dependabot weekly; `pip-audit` fails the build on known vulnerabilities.

## 9. Verify the guardrails on day one

Ask Claude (or do it yourself) once:
1. "Edit the first migration file" → must be blocked after it is committed.
2. "Read .env" → denied.
3. Save a badly formatted .py file via Claude → comes back formatted.
4. Introduce a type error, ask Claude to finish → the Stop hook must send it back to fix it.
5. "Run git push" → denied.
6. `/permissions` and `/hooks` show the rules and hooks as expected.

If a hook does not behave as written, fix the script, not the CLAUDE.md wording. Piling on emphasis in CLAUDE.md is not a fix.

## 10. Where each rule lives (decision table)

| Kind of rule | Where | Why |
|---|---|---|
| Never read secrets, never force-push, never drop schemas | deny rules | Holds in every mode |
| Never edit committed migrations, guardrails, locked docs | PreToolUse hook | Zero-exception path rule |
| Formatting | PostToolUse hook | Happens regardless of what Claude remembers |
| Lint, types, tests, migrations check, coverage | Stop hook + CI | Work is not done until it passes |
| Feature apps don't import each other, layer order | import-linter in `make lint` | Machine-checkable |
| Plan first, ask before adding dependencies, naming, style | CLAUDE.md | Judgment calls with exceptions |
| Architecture detail, models, per-app layout | docs/ARCHITECTURE.md | Claude reads on demand |

## Sources used

- Claude Code best practices (Anthropic): CLAUDE.md length and content, hooks vs guidance, deny/ask rules, Stop hook, sandbox, auto mode.
- OWASP Django Security Cheat Sheet: secret key, headers, cookies, CSRF, CSP (built-in middleware on Django 6.0+), `json_script`, `mark_safe`, `check --deploy`, admin URL, rate limiting.
- django-tenants docs: tenant_context/schema_context, shared vs tenant apps, `migrate_schemas`, tenant creation and deletion pitfalls, multiprocessing executor connection limits.
- django-htmx and htmx security docs: CSRF through `hx-headers`, partial templates, self-hosted extensions, escaping, `hx-ignore`, CSP, no eval.
- Community Django CLAUDE.md examples: thin layers, N+1 rules, protected changes, verification order, plan-first and scope discipline.
- Not sourced (my recommendation): import-linter contracts, flake8 plugins, custom CI greps, Celery tenant-context rule (verify against django-tenants Celery packages before implementing).
