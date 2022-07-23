import re
from typing import NamedTuple

VERSION_RE = re.compile(
    r"""
    (?P<major>[0-9]+)
    (?:\.(?P<minor>[0-9]+))?
    (?:\.(?P<patch>[0-9]+))?
    """,
    re.VERBOSE | re.IGNORECASE,
)


class Version(NamedTuple):
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, version: str) -> "Version":
        match = VERSION_RE.search(version)
        if not match:
            raise Exception(f"invalid version {version}")

        major = int(match.group("major"))
        minor = int(match.group("minor") or 0)
        patch = int(match.group("patch") or 0)

        return Version(major, minor, patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
