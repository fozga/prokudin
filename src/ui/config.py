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
Configuration and preset directory resolution for the Prokudin UI.

Provides pure filesystem utilities to locate and create configuration and preset
directories, supporting both containerized and local filesystem layouts.
"""

import os


def find_project_root() -> str:
    """
    Walk up the filesystem from the current module to find the project root.

    The project root is identified by the presence of `requirements.txt`.

    Returns:
        str: Absolute path to the project root directory.

    Raises:
        RuntimeError: If the project root cannot be found within 5 levels of the
                      current module.
    """
    current = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = current
    for _ in range(5):
        if os.path.exists(os.path.join(current, "requirements.txt")):
            project_root = current
            break
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return project_root


def first_writable(candidates: list[str], label: str) -> str:
    """
    Find the first candidate path that can be created with write permissions.

    Attempts to create each candidate directory in order (with `exist_ok=True`).
    Returns the first path that succeeds. Skips paths that fail with OSError
    or PermissionError.

    Args:
        candidates: List of absolute directory paths to try, in order.
        label: A descriptive label for the directory type (e.g., "presets",
               "config"), used in error messages.

    Returns:
        str: The first candidate path that was successfully created or already
             existed with write permissions.

    Raises:
        RuntimeError: If all candidates fail to be created or are not writable.
    """
    for path in candidates:
        try:
            os.makedirs(path, exist_ok=True)
            return path
        except (OSError, PermissionError):
            continue
    raise RuntimeError(f"Failed to create {label} directory in any location")


def get_presets_dir() -> str:
    """
    Resolve the presets directory, trying container and local fallback paths.

    Tries the following paths in order:
    1. `/app/presets` (container path)
    2. `<project_root>/presets` (local development path)
    3. `~/.config/prokudin/presets` (user home fallback)

    Returns:
        str: Absolute path to the presets directory.

    Raises:
        RuntimeError: If none of the candidate paths can be created or made writable.
    """
    project_root = find_project_root()
    return first_writable(
        [
            "/app/presets",
            os.path.join(project_root, "presets"),
            os.path.expanduser("~/.config/prokudin/presets"),
        ],
        "presets",
    )


def get_config_dir() -> str:
    """
    Resolve the config directory, trying container and local fallback paths.

    Tries the following paths in order:
    1. `/app/config` (container path)
    2. `<project_root>/config` (local development path)
    3. `~/.config/prokudin` (user home fallback)

    Returns:
        str: Absolute path to the config directory.

    Raises:
        RuntimeError: If none of the candidate paths can be created or made writable.
    """
    project_root = find_project_root()
    return first_writable(
        [
            "/app/config",
            os.path.join(project_root, "config"),
            os.path.expanduser("~/.config/prokudin"),
        ],
        "config",
    )
