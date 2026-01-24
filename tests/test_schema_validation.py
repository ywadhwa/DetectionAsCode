import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def load_schema(name: str):
    schema_path = Path("schemas") / name
    return Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))


def test_sigma_rule_schema():
    data = yaml.safe_load(Path("tests/fixtures/sample_rule.yml").read_text(encoding="utf-8"))
    validator = load_schema("sigma_rule.schema.json")
    errors = list(validator.iter_errors(data))
    assert not errors


def test_meta_schema():
    data = yaml.safe_load(Path("tests/fixtures/sample_meta.yml").read_text(encoding="utf-8"))
    validator = load_schema("detection_meta.schema.json")
    errors = list(validator.iter_errors(data))
    assert not errors


def test_pack_schema():
    data = yaml.safe_load(Path("tests/fixtures/sample_pack.yml").read_text(encoding="utf-8"))
    validator = load_schema("content_pack.schema.json")
    errors = list(validator.iter_errors(data))
    assert not errors
