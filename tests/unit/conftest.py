"""Pytest configuration for tests/unit/: mocks unavailable dependencies before test collection.

The PyQt5 mock is applied at conftest import time (not in pytest_configure) to ensure
it's active before pytest-cov's coverage tracer instruments Qt-dependent modules.
"""

from typing import Any
from unittest.mock import MagicMock, patch


class _MockQt:
    """Minimal stand-in for PyQt5.QtCore.Qt with integer key-code constants."""

    class Key:
        """Integer constants for Qt key codes used in keyboard handler tests."""

        Key_1 = 49
        Key_2 = 50
        Key_3 = 51
        Key_A = 65
        Key_B = 66
        Key_Escape = 16777216


# Apply mock immediately at conftest import time, before pytest-cov traces imports
_mock_qtcore = MagicMock()
_mock_qtcore.Qt = _MockQt()
_pyqt5_patcher = patch.dict(
    "sys.modules",
    {
        "PyQt5": MagicMock(),
        "PyQt5.QtCore": _mock_qtcore,
        "PyQt5.QtGui": MagicMock(),
        "PyQt5.QtWidgets": MagicMock(),
    },
)
_pyqt5_patcher.start()


def pytest_unconfigure(config: Any) -> None:
    """Stop PyQt5 sys.modules mock after the test session ends."""
    _pyqt5_patcher.stop()
