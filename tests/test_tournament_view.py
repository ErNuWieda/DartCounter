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
from unittest.mock import MagicMock, patch
from core.tournament_view import TournamentView


@pytest.fixture
def mock_manager():
    """Creates a MagicMock for the TournamentManager."""
    manager = MagicMock()
    manager.system = "Doppel-K.o."
    manager.winner = None
    manager.bracket = {
        "winners": [[{"player1": "A", "player2": "B"}]],
        "losers": [[{"player1": "C", "player2": "D"}]],
    }
    manager.get_next_match.return_value = {"player1": "A", "player2": "B"}
    manager.get_podium.return_value = {
        "first": "Alice",
        "second": "Bob",
        "third": "Charlie",
    }
    return manager


@pytest.fixture
def view(tk_root_session, mock_manager):
    """
    Fixture to create a TournamentView instance with a mocked manager.
    The view is destroyed after the test.
    """
    # The callback can be a simple MagicMock for testing
    callback = MagicMock()
    # Patch BracketCanvas before TournamentView is created. This ensures that
    # view.winners_canvas and view.losers_canvas are MagicMock instances,
    # allowing us to assert that their methods (like draw_bracket) are called.
    with patch("core.tournament_view.BracketCanvas", new_callable=MagicMock):
        # The view is created as a child of the session-scoped root window
        test_view = TournamentView(tk_root_session, mock_manager, callback)
        # update() is needed to process geometry and initial setup
        test_view.update()
        yield test_view
        # Clean up the view window after each test
        if test_view and test_view.winfo_exists():
            test_view.destroy()


def test_initial_layout_for_double_elim(view, mock_manager):
    """Tests if both winner and loser bracket frames are visible for Double Elimination."""
    mock_manager.system = "Doppel-K.o."

    # The view is already created by the fixture, we just need to check its state
    assert view.wb_frame.winfo_ismapped(), "Winners Bracket frame should be visible."
    assert view.lb_frame.winfo_ismapped(), "Losers Bracket frame should be visible."
    assert (
        not view.podium_frame.winfo_ismapped()
    ), "Podium frame should be hidden initially."


def test_initial_layout_for_single_elim(tk_root_session, mock_manager):
    """Tests if only the winner bracket frame is visible for Single Elimination."""
    mock_manager.system = "K.o.-System"
    # Create a new view specifically for this test case
    view_single = TournamentView(tk_root_session, mock_manager, MagicMock())
    view_single.update()

    assert (
        view_single.wb_frame.winfo_ismapped()
    ), "Winners Bracket frame should be visible."
    assert (
        not view_single.lb_frame.winfo_ismapped()
    ), "Losers Bracket frame should be hidden."

    view_single.destroy()


def test_update_bracket_tree_running_tournament(view, mock_manager):
    """Tests the view state when a tournament is running."""
    mock_manager.winner = None
    mock_manager.get_next_match.return_value = {"player1": "A", "player2": "B"}

    view.update_bracket_tree()

    # Check visibility of frames
    assert view.wb_frame.winfo_ismapped()
    assert not view.podium_frame.winfo_ismapped()

    # Check button state
    assert str(view.next_match_button.cget("state")) == "normal"

    # Check if the draw methods of the canvases were called
    view.winners_canvas.draw_bracket.assert_called()
    view.losers_canvas.draw_bracket.assert_called()


def test_update_bracket_tree_finished_tournament(view, mock_manager):
    """Tests the view state when a tournament is finished, showing the podium."""
    mock_manager.winner = "Alice"
    mock_manager.get_next_match.return_value = None

    view.update_bracket_tree()
    # Force tkinter to process all pending UI updates before we assert visibility.
    view.update_idletasks()

    # Check visibility of frames
    assert (
        not view.wb_frame.winfo_ismapped()
    ), "Winners bracket should be hidden when podium is shown."
    assert (
        not view.lb_frame.winfo_ismapped()
    ), "Losers bracket should be hidden when podium is shown."
    assert (
        view.podium_frame.winfo_ismapped()
    ), "Podium should be visible when tournament is finished."

    # Check button state
    # Cast the Tcl object to a string for a reliable comparison
    assert str(view.next_match_button.cget("state")) == "disabled"

    # Check if podium labels are updated
    assert view.podium_labels["first_name"].cget("text") == "Alice"
    assert view.podium_labels["second_name"].cget("text") == "Bob"
    assert view.podium_labels["third_name"].cget("text") == "Charlie"
