"""Pytest configuration for tests/unit/: mocks unavailable dependencies before test collection."""

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


def pytest_configure(config: Any) -> None:
    """Start PyQt5 sys.modules mock before test collection imports Qt-dependent modules."""
    mock_qtcore = MagicMock()
    mock_qtcore.Qt = _MockQt()
    config._pyqt5_patcher = patch.dict(
        "sys.modules",
        {
            "PyQt5": MagicMock(),
            "PyQt5.QtCore": mock_qtcore,
            "PyQt5.QtGui": MagicMock(),
            "PyQt5.QtWidgets": MagicMock(),
        },
    )
    config._pyqt5_patcher.start()


def pytest_unconfigure(config: Any) -> None:
    """Stop PyQt5 sys.modules mock after the test session ends."""
    if hasattr(config, "_pyqt5_patcher"):
        config._pyqt5_patcher.stop()
