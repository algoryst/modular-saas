#!/bin/sh
# Per-layer coverage gates from CLAUDE.md. Run after `coverage run -m pytest`.
# A layer with no files yet reports "No data to report."; that passes until
# the first file of that layer exists, then the threshold applies.
set -u

status=0

gate() {
    name=$1 include=$2 threshold=$3
    out=$(coverage report --include="$include" --fail-under="$threshold" 2>&1)
    rc=$?
    if echo "$out" | grep -q "No data to report"; then
        echo "coverage $name: no files yet"
        return
    fi
    echo "coverage $name (min $threshold%): $(echo "$out" | tail -1)"
    if [ "$rc" -ne 0 ]; then
        echo "$out"
        status=1
    fi
}

gate "services+repositories" "*/services.py,*/repositories.py" 90
gate "models+forms" "*/models.py,*/forms.py" 80
gate "views+api" "*/views.py,*/api/*" 80

exit $status
