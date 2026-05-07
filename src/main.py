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

"""
Main entry point for the Prokudin application.

This script initializes the Qt application, creates the main window,
and starts the event loop for the GUI.

Usage:
    python main.py

Modules:
    sys: Provides access to command-line arguments and system exit.
    PyQt5.QtWidgets.QApplication: Manages the Qt application event loop.
    main_window.MainWindow: Main window class for the application.
"""

import sys

from PyQt5.QtWidgets import QApplication

from .ui.main_window import MainWindow


def main() -> None:
    """
    Initialize and run the Prokudin application.

    This function creates a QApplication instance, instantiates and displays the main window,
    and starts the Qt event loop. The application will exit when the main window is closed.

    Args:
        None

    Returns:
        None
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
