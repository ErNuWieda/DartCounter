# Dartcounter Deluxe
# Copyright (C) 2025 Martin Hehl (airnooweeda)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch, ANY

from core import ui_utils


@pytest.mark.ui
class TestShowMessage:
    """Tests the ui_utils.show_message function."""

    @pytest.mark.parametrize(
        "msg_type, expected_func_name",
        [
            ("info", "showinfo"),
            ("warning", "showwarning"),
            ("error", "showerror"),
        ],
    )
    @patch("core.ui_utils.messagebox")
    def test_show_message_native_dialogs(
        self, mock_messagebox, msg_type, expected_func_name, tk_root_session
    ):
        """
        Tests that the correct native messagebox function is called when
        auto_close_for_ai_after_ms is 0.
        """
        title = "Test Title"
        message = "Test Message"

        ui_utils.show_message(msg_type, title, message, parent=tk_root_session)

        expected_func = getattr(mock_messagebox, expected_func_name)
        expected_func.assert_called_once_with(title, message, parent=tk_root_session)

    @patch("core.ui_utils.tk.Toplevel")
    def test_show_message_custom_dialog_creation(self, mock_toplevel, tk_root_session):
        """
        Tests the creation and content of the custom auto-closing dialog.
        """
        mock_dialog_instance = MagicMock()
        # Mock the after method to prevent it from actually running
        mock_dialog_instance.after = MagicMock()
        mock_toplevel.return_value = mock_dialog_instance

        title = "AI Turn"
        message = "AI is thinking..."
        timeout = 500

        ui_utils.show_message(
            "info",
            title,
            message,
            parent=tk_root_session,
            auto_close_for_ai_after_ms=timeout,
        )

        # Assert that a Toplevel window was created
        mock_toplevel.assert_called_once_with(tk_root_session)
        mock_dialog_instance.title.assert_called_once_with(title)

        # Assert that the auto-close timer was set
        mock_dialog_instance.after.assert_called_once_with(timeout, ANY)

        # Assert that the dialog was made modal
        mock_dialog_instance.grab_set.assert_called_once()
        mock_dialog_instance.wait_window.assert_called_once()

    @patch("core.ui_utils.tk.Toplevel")
    def test_custom_dialog_ok_button_closes_dialog(self, mock_toplevel, tk_root_session):
        """
        Tests that clicking the OK button in the custom dialog destroys it
        and cancels the timer.
        """
        mock_dialog_instance = MagicMock()
        # Simulate the return value of after() to be a valid ID
        mock_dialog_instance.after.return_value = "after#123"
        mock_toplevel.return_value = mock_dialog_instance

        # We need to find the 'on_ok' function that is created inside show_message
        # We can patch the Button to capture its command
        with patch("core.ui_utils.ttk.Button") as mock_button:
            ui_utils.show_message(
                "info", "t", "m", parent=tk_root_session, auto_close_for_ai_after_ms=500
            )

            # Get the command that was passed to the OK button
            ok_command = mock_button.call_args.kwargs.get("command")
            assert ok_command is not None

            # Execute the command
            ok_command()

        # Check that the timer was cancelled and the dialog was destroyed
        mock_dialog_instance.after_cancel.assert_called_once_with("after#123")
        mock_dialog_instance.destroy.assert_called_once()


@pytest.mark.ui
class TestAskQuestion:
    """Tests the ui_utils.ask_question function."""

    @pytest.mark.parametrize(
        "buttons, expected_func_name",
        [
            ("yesno", "askyesno"),
            ("yesnocancel", "askyesnocancel"),
            ("retrycancel", "askretrycancel"),
            ("okcancel", "askokcancel"),
        ],
    )
    @patch("core.ui_utils.messagebox")
    def test_ask_question_calls_correct_function(
        self, mock_messagebox, buttons, expected_func_name, tk_root_session
    ):
        """Tests that the correct messagebox function is called for each button type."""
        title = "Confirm?"
        message = "Are you sure?"

        ui_utils.ask_question(buttons, title, message, parent=tk_root_session, default="no")

        expected_func = getattr(mock_messagebox, expected_func_name)
        expected_func.assert_called_once_with(
            title, message, parent=tk_root_session, default="no"
        )

