# Copyright (C) 2025 fozga
#
# This file is part of Prokudin.
#
# Prokudin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prokudin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Prokudin.  If not, see <https://www.gnu.org/licenses/>.

"""Pytest configuration for integration tests."""

from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication, None, None]:
    """Session-scoped QApplication shared by integration tests."""
    app = QApplication.instance() or QApplication([])
    yield app  # type: ignore[misc]


@pytest.fixture(scope="module")
def real_window(
    qapp: QApplication,
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator["MainWindow", None, None]:  # type: ignore[name-defined]  # noqa: F821
    """Fully real MainWindow for integration tests (no handler mocks).

    Patches:
        - ``restore_autosave``: suppressed so the window opens with a clean
          state instead of replaying the developer's last session.
        - ``get_presets_dir`` and ``get_config_dir``: redirected to tmp_path
          to avoid slow filesystem operations during initialization (creating
          real directories under ~/.config, /app, etc.).

    All other collaborators (ImageProcessorService, handlers, widgets) are real.
    """
    from src.ui.main_window import MainWindow

    tmp = tmp_path_factory.mktemp("prokudin-main-window")
    presets_dir = tmp / "presets"
    presets_dir.mkdir(exist_ok=True)
    config_dir = tmp / "config"
    config_dir.mkdir(exist_ok=True)

    with patch("src.ui.main_window.restore_autosave"), patch(
        "src.ui.main_window.get_presets_dir", return_value=str(presets_dir)
    ), patch("src.ui.main_window.get_config_dir", return_value=str(config_dir)):
        w = MainWindow()
    w.show()
    yield w
    w.close()

