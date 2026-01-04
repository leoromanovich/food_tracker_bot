from datetime import datetime

import yaml

from bot.services.markdown_helpers import build_log_filename, render_frontmatter


def test_build_log_filename_matches_expected_format():
    timestamp = datetime(2025, 3, 12, 19, 30, 5)
    assert build_log_filename(timestamp, "cafebabe") == "2025-03-12_19-30-05_cafebabe.md"


def test_render_frontmatter_matches_yaml_output():
    payload = {
        "date": "2025-03-12",
        "time": "19:30",
        "foods": ["[[Паста]]", "[[Сыр]]"],
    }
    yaml_body = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False).strip()
    assert render_frontmatter(payload) == f"---\n{yaml_body}\n---\n\n#foodtracker\n"
