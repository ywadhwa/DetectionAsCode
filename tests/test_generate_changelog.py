from __future__ import annotations

from datetime import UTC, datetime

from scripts.generate_changelog import bucket_start, change_log_to_markdown, classify_rule_diff


def test_classify_rule_diff_detects_key_rule_changes() -> None:
    diff = """
+title: Updated Title
-description: old
+description: new
-level: low
+level: medium
-detection:
+detection:
"""
    changes = classify_rule_diff(diff)
    assert "Title updated" in changes
    assert "Description updated" in changes
    assert "Severity changed" in changes
    assert "Detection logic updated" in changes


def test_classify_rule_diff_falls_back_when_no_patterns_match() -> None:
    assert classify_rule_diff("@@ metadata shuffle @@") == ["Misc rule metadata updated"]


def test_bucket_start_month_normalizes_to_month_boundary() -> None:
    dt = datetime(2026, 3, 27, 15, 30, tzinfo=UTC)
    assert bucket_start(dt, "month") == datetime(2026, 3, 1, 0, 0, tzinfo=UTC)


def test_change_log_to_markdown_renders_status_and_commit_links() -> None:
    payload = [
        {
            "datetime": "2026-03-27T12:00:00+00:00",
            "commit": "abcdef1234567890",
            "message": "Update rule",
            "author": "Yatin",
            "file": "sigma-rules/endpoint/example.yml",
            "filename": "example.yml",
            "filepath": "sigma-rules/endpoint",
            "status": "Modified",
            "change": "Detection logic updated",
        }
    ]
    markdown = change_log_to_markdown(payload, repo_url="https://github.com/example/repo", bucket="month")
    assert "Rule Changelog" in markdown
    assert "### Modified" in markdown
    assert "`sigma-rules/endpoint/example.yml` - Detection logic updated" in markdown
    assert "[abcdef1](https://github.com/example/repo/commit/abcdef1234567890)" in markdown
