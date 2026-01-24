from packaging.version import Version

def parse_version(value: str) -> Version:
    return Version(str(value))

def is_version_bumped(old: str, new: str) -> bool:
    return parse_version(new) > parse_version(old)
