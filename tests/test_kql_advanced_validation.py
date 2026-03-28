from __future__ import annotations

from pathlib import Path

from scripts.validate_kql_advanced import CaseInsensitiveDict, collect_query_files, normalize_type


def test_normalize_type_maps_known_aliases() -> None:
    assert normalize_type("BigInt") == "long"
    assert normalize_type("URI") == "string"
    assert normalize_type(" Date Time ") == "datetime"


def test_case_insensitive_dict_normalizes_nested_keys() -> None:
    payload = CaseInsensitiveDict({"Name": "TableA", "Properties": [{"Type": "String"}]})
    assert payload["name"] == "TableA"
    assert payload["properties"][0]["type"] == "String"


def test_collect_query_files_from_directory(tmp_path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    query_dir = repo / "output" / "kql"
    query_dir.mkdir(parents=True)
    (query_dir / "one.kql").write_text("SecurityEvent | take 1\n", encoding="utf-8")
    (query_dir / "two.txt").write_text("ignore\n", encoding="utf-8")

    monkeypatch.setattr("scripts.validate_kql_advanced.repo_root", lambda: repo)

    files = collect_query_files(directory="output/kql")
    assert files == [query_dir / "one.kql"]


def test_collect_query_files_with_explicit_query(tmp_path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    query_file = repo / "saved_query.kql"
    query_file.write_text("SigninLogs | take 1\n", encoding="utf-8")

    monkeypatch.setattr("scripts.validate_kql_advanced.repo_root", lambda: repo)

    files = collect_query_files(directory="output/kql", query="saved_query.kql")
    assert files == [query_file]
