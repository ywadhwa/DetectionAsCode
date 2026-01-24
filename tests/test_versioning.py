from scripts.lib.versioning import is_version_bumped


def test_version_bump_true():
    assert is_version_bumped("1.0.0", "1.0.1")


def test_version_bump_false():
    assert not is_version_bumped("1.2.0", "1.2.0")
