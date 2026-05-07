"""
Status bar component for the Prokudin application.

Handles displaying application mode and status messages to the user.
"""

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QLabel, QStatusBar


class StatusBarHandler(QObject):
    """
    Manages the status bar functionality in the application.

    This class handles updating the status message and the mode indicator
    in the application's status bar, providing a clean interface for other
    parts of the application to communicate status to the user.
    """

    # Standard timeout values (milliseconds)
    SHORT_TIMEOUT = 2000  # 2 seconds - for brief notifications
    MEDIUM_TIMEOUT = 3000  # 3 seconds - for standard messages
    LONG_TIMEOUT = 5000  # 5 seconds - for important messages
    NO_TIMEOUT = 0  # 0 - messages remain until replaced

    def __init__(self, status_bar: QStatusBar) -> None:
        """
        Initialize the status bar handler.

        Args:
            status_bar (QStatusBar): The Qt status bar widget to manage.
        """
        super().__init__()
        self.status_bar = status_bar
        self.status_bar.setSizeGripEnabled(False)

        # Create and configure the mode indicator label
        self.mode_label = QLabel("Load images")
        self.mode_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-right: 100px;")
        self.status_bar.addPermanentWidget(self.mode_label)

        # Set initial message
        self.set_message("Ready - Load channel images to begin processing")

    def set_message(self, message: str, timeout: int = NO_TIMEOUT) -> None:
        """
        Update the status bar with a new message.

        Args:
            message (str): The message to display in the status bar.
            timeout (int): Duration in milliseconds to display the message.
                           Default is NO_TIMEOUT, which means the message remains
                           until replaced.
        """
        self.status_bar.showMessage(message, timeout)

    def set_mode(self, mode: str) -> None:
        """
        Update the mode indicator in the status bar.

        Args:
            mode (str): The mode to display ("Load images", "Editing",
                       "Cropping", "Saving", etc.)
        """
        self.mode_label.setText(mode)

    def update_mode_from_state(self, loaded_channels: int, crop_mode: bool = False, saving: bool = False) -> None:
        """
        Update the mode indicator based on the current application state.

        Args:
            loaded_channels (int): Number of channels that are currently loaded.
            crop_mode (bool): Whether crop mode is currently active.
            saving (bool): Whether the application is currently saving.
        """
        if saving:
            self.set_mode("Saving")
        elif crop_mode:
            self.set_mode("Cropping")
        elif loaded_channels < 3:
            self.set_mode("Load images")
        else:
            self.set_mode("Editing")
