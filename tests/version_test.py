from typing import Tuple

import pytest

from pyzabbix._version import Version


@pytest.mark.parametrize(
    "version,expected",
    [
        # fmt: off
        ("2.5.2",       (2, 5, 2)),
        ("3.0.0rc1",    (3, 0, 0)),
        ("3.0.0",       (3, 0, 0)),
        ("3.0",         (3, 0, 0)),
        ("3",           (3, 0, 0)),
        # fmt: on
    ],
)
def test_parse_version(
    version: str,
    expected: Tuple[int, int, int],
) -> None:
    assert Version.parse(version) == expected
