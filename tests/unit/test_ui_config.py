"""Unit tests for src/ui/config.py."""

import os
from unittest.mock import patch

import pytest

from src.ui.config import find_project_root, first_writable, get_config_dir, get_presets_dir


class TestFindProjectRoot:
    """
    Test Design Specification: find_project_root()
    Module under test: src/ui/config.py

    Contract:
        Walks up the filesystem from the current module (src/ui) to find the
        project root, identified by the presence of `requirements.txt`.
        The search is limited to 5 levels.
        Returns the absolute path to the project root.
        Raises RuntimeError if the project root cannot be found.

    Equivalence partitions:
        EP1  requirements.txt exists 1 level up (project root is parent of src)
             → returns the parent directory path
        EP2  requirements.txt is found within 5 levels
             → returns the correct ancestor directory
        EP3  requirements.txt does not exist within 5 levels
             → returns the highest accessible ancestor as fallback

    Boundary values:
        BV1  Search limit at 5 levels (requirements.txt found at limit)
        BV2  Search limit exceeded (requirements.txt beyond 5 levels, returns fallback)

    Exclusions:
        - Does not validate that the returned path is a valid Python project.
        - Does not modify the filesystem.

    Constraints:
        - Uses os.path for filesystem operations.
        - os.path.exists is mocked to control file discovery.
    """

    def test_finds_project_root_one_level_up(self) -> None:
        """
        Given src/ui is the current module location,
        When find_project_root is called,
        Then it returns the parent of src (the project root).
        """
        # Arrange
        with patch("src.ui.config.os.path.abspath") as mock_abspath, patch(
            "src.ui.config.os.path.dirname"
        ) as mock_dirname, patch("src.ui.config.os.path.exists") as mock_exists:

            # Simulate: /project/src/ui/config.py
            mock_abspath.return_value = "/project/src/ui/config.py"
            # dirname calls: 1st dir from abspath, 2nd dir for current, then dirname in loop
            # abspath -> /project/src/ui -> /project/src (current)
            # Loop iter 1: dirname(/project/src) -> /project -> dirname(/project) -> /
            mock_dirname.side_effect = ["/project/src", "/project", "/project", "/"]
            # requirements.txt not found at /project/src, found at /project
            mock_exists.side_effect = [False, True]

            # Act
            result = find_project_root()

            # Assert
            assert result == "/project"

    def test_finds_project_root_within_five_levels(self) -> None:
        """
        Given requirements.txt exists at a parent directory within 5 levels,
        When find_project_root is called,
        Then it returns that parent directory.
        """
        # Arrange
        with patch("src.ui.config.os.path.abspath") as mock_abspath, patch(
            "src.ui.config.os.path.dirname"
        ) as mock_dirname, patch("src.ui.config.os.path.exists") as mock_exists:

            # Starting point: /a/b/c/d/src/ui/config.py
            mock_abspath.return_value = "/a/b/c/d/src/ui/config.py"

            def dirname_impl(path: str) -> str:
                """Simulate dirname by removing the last path component."""
                parts = path.rstrip("/").split("/")
                if len(parts) <= 1:
                    return "/"
                return "/".join(parts[:-1])

            mock_dirname.side_effect = dirname_impl

            def exists_impl(path: str) -> bool:
                """Return True only for /a/requirements.txt."""
                return path == "/a/requirements.txt"

            mock_exists.side_effect = exists_impl

            # Act
            result = find_project_root()

            # Assert
            assert result == "/a"

    def test_returns_highest_ancestor_when_requirements_not_found(self) -> None:
        """
        Given requirements.txt does not exist within 5 levels,
        When find_project_root is called,
        Then it returns the highest directory reached before loop limit.
        """
        # Arrange
        with patch("src.ui.config.os.path.abspath") as mock_abspath, patch(
            "src.ui.config.os.path.dirname"
        ) as mock_dirname, patch("src.ui.config.os.path.exists") as mock_exists:

            # Starting point: /a/b/c/d/e/src/ui/config.py
            mock_abspath.return_value = "/a/b/c/d/e/src/ui/config.py"
            # dirname calls: we walk up 5 times but never find requirements.txt
            # abspath -> /a/b/c/d/e/src/ui -> /a/b/c/d/e/src (current)
            # iter 1: /a/b/c/d/e -> /a/b/c/d
            # iter 2: /a/b/c/d -> /a/b/c
            # iter 3: /a/b/c -> /a/b
            # iter 4: /a/b -> /a
            # iter 5: /a -> / (or root check)
            mock_dirname.side_effect = [
                "/a/b/c/d/e/src",  # 1st from abspath
                "/a/b/c/d/e",      # 2nd from abspath (current)
                "/a/b/c/d/e",      # parent in iter 1
                "/a/b/c/d",        # current in iter 1
                "/a/b/c/d",        # parent in iter 2
                "/a/b/c",          # current in iter 2
                "/a/b/c",          # parent in iter 3
                "/a/b",            # current in iter 3
                "/a/b",            # parent in iter 4
                "/a",              # current in iter 4
                "/a",              # parent in iter 5
                "/",               # current in iter 5
            ]
            # requirements.txt never found
            mock_exists.return_value = False

            # Act
            result = find_project_root()

            # Assert (returns the initial current which was the highest we reached)
            assert result == "/a/b/c/d/e"




class TestFirstWritable:
    """
    Test Design Specification: first_writable()
    Module under test: src/ui/config.py

    Contract:
        Tries to create each candidate directory in order.
        Returns the path of the first candidate that can be created
        (or already exists) with write permissions.
        Uses os.makedirs(..., exist_ok=True) to handle existing dirs.
        Skips candidates that raise OSError or PermissionError.
        Raises RuntimeError with a descriptive message if all candidates fail.

    Equivalence partitions:
        EP1  First candidate succeeds (writable)
             → returns first candidate
        EP2  First fails, second succeeds
             → returns second candidate
        EP3  Multiple fail, third succeeds
             → returns third candidate
        EP4  All candidates fail with OSError or PermissionError
             → raises RuntimeError with label in message

    Boundary values:
        BV1  Single candidate, succeeds → returns that candidate
        BV2  Single candidate, fails → raises RuntimeError

    Exclusions:
        - Does not validate the returned path is a "good" location.
        - Does not check permissions beyond the makedirs attempt.

    Constraints:
        - os.makedirs is mocked to simulate success/failure.
        - Error label is included in the RuntimeError message.
    """

    def test_first_candidate_succeeds(self) -> None:
        """
        Given a list of candidates and the first is writable,
        When first_writable is called,
        Then it returns the first candidate without trying others.
        """
        # Arrange
        candidates = ["/app/presets", "/home/user/.config/presets"]
        label = "presets"

        with patch("src.ui.config.os.makedirs") as mock_makedirs:
            mock_makedirs.return_value = None  # succeeds

            # Act
            result = first_writable(candidates, label)

            # Assert
            assert result == "/app/presets"
            mock_makedirs.assert_called_once_with("/app/presets", exist_ok=True)

    def test_first_fails_second_succeeds(self) -> None:
        """
        Given a list of candidates where the first fails with PermissionError,
        When first_writable is called,
        Then it skips the first and returns the second.
        """
        # Arrange
        candidates = ["/app/presets", "/home/user/.config/presets"]
        label = "presets"

        with patch("src.ui.config.os.makedirs") as mock_makedirs:
            # First call raises PermissionError, second succeeds
            mock_makedirs.side_effect = [PermissionError("no write"), None]

            # Act
            result = first_writable(candidates, label)

            # Assert
            assert result == "/home/user/.config/presets"
            assert mock_makedirs.call_count == 2

    def test_multiple_fail_third_succeeds(self) -> None:
        """
        Given a list of three candidates where first and second fail,
        When first_writable is called,
        Then it skips the first two and returns the third.
        """
        # Arrange
        candidates = ["/app/presets", "/root/presets", "/home/user/.config/presets"]
        label = "presets"

        with patch("src.ui.config.os.makedirs") as mock_makedirs:
            # First two fail, third succeeds
            mock_makedirs.side_effect = [OSError("not found"), PermissionError("denied"), None]

            # Act
            result = first_writable(candidates, label)

            # Assert
            assert result == "/home/user/.config/presets"
            assert mock_makedirs.call_count == 3

    def test_all_candidates_fail_raises_runtime_error(self) -> None:
        """
        Given a list of candidates where all fail,
        When first_writable is called,
        Then it raises RuntimeError with the label in the message.
        """
        # Arrange
        candidates = ["/app/presets", "/root/presets", "/read_only/presets"]
        label = "presets"

        with patch("src.ui.config.os.makedirs") as mock_makedirs:
            # All calls fail
            mock_makedirs.side_effect = PermissionError("denied")

            # Act / Assert
            with pytest.raises(RuntimeError, match="Failed to create presets directory"):
                first_writable(candidates, label)

    def test_single_candidate_succeeds(self) -> None:
        """
        Given a single candidate that is writable,
        When first_writable is called,
        Then it returns that candidate.
        """
        # Arrange
        candidates = ["/app/config"]
        label = "config"

        with patch("src.ui.config.os.makedirs") as mock_makedirs:
            mock_makedirs.return_value = None

            # Act
            result = first_writable(candidates, label)

            # Assert
            assert result == "/app/config"

    def test_single_candidate_fails_raises_error(self) -> None:
        """
        Given a single candidate that fails,
        When first_writable is called,
        Then it raises RuntimeError.
        """
        # Arrange
        candidates = ["/read_only/config"]
        label = "config"

        with patch("src.ui.config.os.makedirs") as mock_makedirs:
            mock_makedirs.side_effect = OSError("read-only filesystem")

            # Act / Assert
            with pytest.raises(RuntimeError, match="Failed to create config directory"):
                first_writable(candidates, label)


class TestGetPresetsDir:
    """
    Test Design Specification: get_presets_dir()
    Module under test: src/ui/config.py

    Contract:
        Locates the presets directory by calling find_project_root and
        first_writable with a specific list of candidates:
        1. /app/presets (container)
        2. <project_root>/presets (local development)
        3. ~/.config/prokudin/presets (user home fallback)

        Returns the absolute path to the first writable presets directory.
        Raises RuntimeError if none of the candidates can be created or made writable.

    Equivalence partitions:
        EP1  /app/presets is writable → returns /app/presets
        EP2  /app/presets fails, project_root/presets succeeds → returns project_root/presets
        EP3  Container and project paths fail, home fallback succeeds → returns ~/.config/prokudin/presets
        EP4  All paths fail → raises RuntimeError with "presets" in message

    Boundary values:
        BV1  Home expansion: ~ is properly expanded to user home directory

    Exclusions:
        - Does not validate the returned directory is readable or contains files.
        - Does not initialize presets if the directory is empty.

    Constraints:
        - os.path.expanduser is used to expand ~.
        - find_project_root and first_writable are mocked to control behavior.
    """

    def test_returns_app_presets_when_available(self) -> None:
        """
        Given /app/presets is writable,
        When get_presets_dir is called,
        Then it returns /app/presets.
        """
        # Arrange
        with patch("src.ui.config.find_project_root") as mock_find_root, patch(
            "src.ui.config.first_writable"
        ) as mock_first_writable, patch("src.ui.config.os.path.expanduser") as mock_expanduser:
            mock_find_root.return_value = "/home/user/project"
            mock_expanduser.return_value = "/home/user/.config/prokudin/presets"
            mock_first_writable.return_value = "/app/presets"

            # Act
            result = get_presets_dir()

            # Assert
            assert result == "/app/presets"
            mock_first_writable.assert_called_once_with(
                ["/app/presets", "/home/user/project/presets", "/home/user/.config/prokudin/presets"],
                "presets",
            )

    def test_returns_project_presets_when_app_unavailable(self) -> None:
        """
        Given /app/presets is unavailable but project_root/presets is writable,
        When get_presets_dir is called,
        Then it returns project_root/presets.
        """
        # Arrange
        with patch("src.ui.config.find_project_root") as mock_find_root, patch(
            "src.ui.config.first_writable"
        ) as mock_first_writable, patch("src.ui.config.os.path.expanduser") as mock_expanduser:
            mock_find_root.return_value = "/home/user/project"
            mock_expanduser.return_value = "/home/user/.config/prokudin/presets"
            mock_first_writable.return_value = "/home/user/project/presets"

            # Act
            result = get_presets_dir()

            # Assert
            assert result == "/home/user/project/presets"

    def test_returns_home_presets_when_others_fail(self) -> None:
        """
        Given container and project paths fail, but home fallback is writable,
        When get_presets_dir is called,
        Then it returns ~/.config/prokudin/presets (expanded).
        """
        # Arrange
        with patch("src.ui.config.find_project_root") as mock_find_root, patch(
            "src.ui.config.first_writable"
        ) as mock_first_writable, patch("src.ui.config.os.path.expanduser") as mock_expanduser:
            mock_find_root.return_value = "/home/user/project"
            mock_expanduser.return_value = "/home/user/.config/prokudin/presets"
            mock_first_writable.return_value = "/home/user/.config/prokudin/presets"

            # Act
            result = get_presets_dir()

            # Assert
            assert result == "/home/user/.config/prokudin/presets"

    def test_raises_when_all_candidates_fail(self) -> None:
        """
        Given all presets directory candidates fail,
        When get_presets_dir is called,
        Then it raises RuntimeError.
        """
        # Arrange
        with patch("src.ui.config.find_project_root") as mock_find_root, patch(
            "src.ui.config.first_writable"
        ) as mock_first_writable:
            mock_find_root.return_value = "/home/user/project"
            mock_first_writable.side_effect = RuntimeError("Failed to create presets directory in any location")

            # Act / Assert
            with pytest.raises(RuntimeError, match="Failed to create presets directory"):
                get_presets_dir()


class TestGetConfigDir:
    """
    Test Design Specification: get_config_dir()
    Module under test: src/ui/config.py

    Contract:
        Locates the config directory by calling find_project_root and
        first_writable with a specific list of candidates:
        1. /app/config (container)
        2. <project_root>/config (local development)
        3. ~/.config/prokudin (user home fallback)

        Returns the absolute path to the first writable config directory.
        Raises RuntimeError if none of the candidates can be created or made writable.

    Equivalence partitions:
        EP1  /app/config is writable → returns /app/config
        EP2  /app/config fails, project_root/config succeeds → returns project_root/config
        EP3  Container and project paths fail, home fallback succeeds → returns ~/.config/prokudin
        EP4  All paths fail → raises RuntimeError with "config" in message

    Boundary values:
        BV1  Home expansion: ~ is properly expanded to user home directory

    Exclusions:
        - Does not validate the returned directory is readable or writable for file operations.
        - Does not initialize config files if the directory is empty.

    Constraints:
        - os.path.expanduser is used to expand ~.
        - find_project_root and first_writable are mocked to control behavior.
    """

    def test_returns_app_config_when_available(self) -> None:
        """
        Given /app/config is writable,
        When get_config_dir is called,
        Then it returns /app/config.
        """
        # Arrange
        with patch("src.ui.config.find_project_root") as mock_find_root, patch(
            "src.ui.config.first_writable"
        ) as mock_first_writable, patch("src.ui.config.os.path.expanduser") as mock_expanduser:
            mock_find_root.return_value = "/home/user/project"
            mock_expanduser.return_value = "/home/user/.config/prokudin"
            mock_first_writable.return_value = "/app/config"

            # Act
            result = get_config_dir()

            # Assert
            assert result == "/app/config"
            mock_first_writable.assert_called_once_with(
                ["/app/config", "/home/user/project/config", "/home/user/.config/prokudin"],
                "config",
            )

    def test_returns_project_config_when_app_unavailable(self) -> None:
        """
        Given /app/config is unavailable but project_root/config is writable,
        When get_config_dir is called,
        Then it returns project_root/config.
        """
        # Arrange
        with patch("src.ui.config.find_project_root") as mock_find_root, patch(
            "src.ui.config.first_writable"
        ) as mock_first_writable, patch("src.ui.config.os.path.expanduser") as mock_expanduser:
            mock_find_root.return_value = "/home/user/project"
            mock_expanduser.return_value = "/home/user/.config/prokudin"
            mock_first_writable.return_value = "/home/user/project/config"

            # Act
            result = get_config_dir()

            # Assert
            assert result == "/home/user/project/config"

    def test_returns_home_config_when_others_fail(self) -> None:
        """
        Given container and project paths fail, but home fallback is writable,
        When get_config_dir is called,
        Then it returns ~/.config/prokudin (expanded).
        """
        # Arrange
        with patch("src.ui.config.find_project_root") as mock_find_root, patch(
            "src.ui.config.first_writable"
        ) as mock_first_writable, patch("src.ui.config.os.path.expanduser") as mock_expanduser:
            mock_find_root.return_value = "/home/user/project"
            mock_expanduser.return_value = "/home/user/.config/prokudin"
            mock_first_writable.return_value = "/home/user/.config/prokudin"

            # Act
            result = get_config_dir()

            # Assert
            assert result == "/home/user/.config/prokudin"

    def test_raises_when_all_candidates_fail(self) -> None:
        """
        Given all config directory candidates fail,
        When get_config_dir is called,
        Then it raises RuntimeError.
        """
        # Arrange
        with patch("src.ui.config.find_project_root") as mock_find_root, patch(
            "src.ui.config.first_writable"
        ) as mock_first_writable:
            mock_find_root.return_value = "/home/user/project"
            mock_first_writable.side_effect = RuntimeError("Failed to create config directory in any location")

            # Act / Assert
            with pytest.raises(RuntimeError, match="Failed to create config directory"):
                get_config_dir()
