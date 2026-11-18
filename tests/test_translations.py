"""Every user-facing string ships translated: no empty, fuzzy or broken entries."""

import re
import shutil
import subprocess  # nosec B404: runs gettext's msgfmt on our own catalogue
from pathlib import Path

import pytest
from django.conf import settings

FRENCH_PO = Path(settings.BASE_DIR) / "locale" / "fr_FR" / "LC_MESSAGES" / "django.po"


@pytest.fixture(scope="module")
def french_statistics() -> str:
    msgfmt = shutil.which("msgfmt")
    assert msgfmt, "gettext's msgfmt is required (make messages uses it too)"
    result = subprocess.run(  # nosec B603: fixed arguments, no shell
        [msgfmt, "--check", "--statistics", "-o", "/dev/null", str(FRENCH_PO)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stderr


def test_french_catalogue_has_no_untranslated_entries(french_statistics):
    assert "untranslated" not in french_statistics, french_statistics


def test_french_catalogue_has_no_fuzzy_entries(french_statistics):
    assert "fuzzy" not in french_statistics, french_statistics


def test_french_catalogue_is_not_empty(french_statistics):
    match = re.search(r"(\d+) translated message", french_statistics)
    assert match and int(match.group(1)) > 0, french_statistics
