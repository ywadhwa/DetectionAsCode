from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dac.services import conversion
from dac.services.query_validation import validate_queries


def test_sigma_cli_target_maps_elasticsearch_to_lucene() -> None:
    assert conversion.sigma_cli_target("elasticsearch") == "lucene"


def test_convert_sigma_rule_elasticsearch_bundle_mode_suppresses_sidecars(
    tmp_path, monkeypatch
) -> None:
    commands = []

    def fake_run(cmd, capture_output, text, timeout):
        commands.append(cmd)
        return SimpleNamespace(returncode=0, stdout="QueryName:*ufile.io*\n", stderr="")

    monkeypatch.setattr(conversion.subprocess, "run", fake_run)

    rule = (
        Path(__file__).resolve().parents[1]
        / "sigma-rules"
        / "endpoint"
        / "endpoint_dns_query_win_ufile_io_query.yml"
    )
    status, query_path, error_message, query_text = conversion.convert_sigma_rule(
        rule_path=rule,
        backend="elasticsearch",
        output_base=tmp_path,
        emit_sidecars=False,
    )

    assert status == "success"
    assert error_message == ""
    assert query_text == "QueryName:*ufile.io*\n"
    assert query_path.exists()
    assert not query_path.with_suffix(".elasticsearch.meta").exists()
    assert not query_path.with_suffix(".elasticsearch.error").exists()

    assert commands
    assert "--target" in commands[0]
    assert "lucene" in commands[0]
    assert "--without-pipeline" in commands[0]


def test_validate_queries_supports_elasticsearch_query_type(tmp_path) -> None:
    query_dir = tmp_path / "queries"
    query_dir.mkdir(parents=True)
    (query_dir / "sample.elasticsearch").write_text("host.name:WORKSTATION01\n", encoding="utf-8")

    result = validate_queries(
        query_type="elasticsearch",
        directory=str(query_dir),
        artifact_output=str(tmp_path / "validation-elasticsearch.json"),
    )

    assert result["status"] == "success"
    assert result["metrics"]["files_checked"] == 1
    assert result["metrics"]["failed_files"] == 0
