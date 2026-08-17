"""Pytest configuration for tests/unit/: mocks unavailable dependencies before test collection.

The PyQt5 mock is applied at conftest import time (not in pytest_configure) to ensure
it's active before pytest-cov's coverage tracer instruments Qt-dependent modules.
"""

from typing import Any
from unittest.mock import MagicMock, patch


class _MockQt:
    """Minimal stand-in for PyQt5.QtCore.Qt constants used by unit tests."""

    KeepAspectRatio = 1
    SmoothTransformation = 2

    class Key:
        """Integer constants for Qt key codes used in keyboard handler tests."""

        Key_1 = 49
        Key_2 = 50
        Key_3 = 51
        Key_A = 65
        Key_B = 66
        Key_Escape = 16777216

    class GlobalColor:
        """Integer constants for Qt global colors used in UI tests."""

        red = 1
        green = 2
        blue = 4


# Stub base classes for Qt widgets.  When src.ui.* modules execute
# ``class Foo(QMainWindow):`` or ``class Bar(QWidget):``, the base class must
# be a real ``type`` (not a MagicMock instance) so that Python's metaclass
# machinery creates a proper class object whose methods are accessible via
# ``getattr``.  Using a plain MagicMock as the base causes the class statement
# to invoke MagicMock as a metaclass, which returns another MagicMock and
# discards all method definitions.
class _StubQObject:
    """Minimal real-type stub for Qt widget base classes (QMainWindow, QWidget, …)."""


# Apply mock immediately at conftest import time, before pytest-cov traces imports
_mock_qtcore = MagicMock()
_mock_qtcore.Qt = _MockQt()
_mock_qtwidgets = MagicMock()
_mock_qtwidgets.QMainWindow = _StubQObject
_mock_qtwidgets.QWidget = _StubQObject
_mock_qtwidgets.QDialog = _StubQObject
_pyqt5_patcher = patch.dict(
    "sys.modules",
    {
        "PyQt5": MagicMock(),
        "PyQt5.QtCore": _mock_qtcore,
        "PyQt5.QtGui": MagicMock(),
        "PyQt5.QtWidgets": _mock_qtwidgets,
    },
)
_pyqt5_patcher.start()


def pytest_unconfigure(config: Any) -> None:
    """Stop PyQt5 sys.modules mock after the test session ends."""
    _pyqt5_patcher.stop()
