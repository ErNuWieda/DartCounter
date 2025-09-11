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
from core.bracket_canvas import BracketCanvas


@pytest.fixture
def bracket_canvas(tk_root_session):
    """
    Fixture to create a BracketCanvas instance within a Toplevel window.
    This ensures the canvas has a valid parent and geometry for testing.
    """
    # A Toplevel window is used as a container for the canvas
    test_window = tk.Toplevel(tk_root_session)
    # Give the canvas a fixed size so that position calculations are predictable
    canvas = BracketCanvas(test_window, width=800, height=600)
    canvas.pack()
    # update_idletasks() is crucial to force tkinter to calculate the canvas geometry
    canvas.update_idletasks()
    yield canvas
    # Clean up the window after the test
    test_window.destroy()


@pytest.fixture
def simple_bracket_data():
    """Provides simple tournament data for a 4-player bracket."""
    return [
        [  # Round 1
            {"player1": "Alice", "player2": "Bob", "winner": "Alice"},
            {"player1": "Charlie", "player2": "David", "winner": "Charlie"},
        ],
        [{"player1": "Alice", "player2": "Charlie", "winner": None}],  # Round 2 (Final)
    ]


def find_text_item(canvas, text_to_find):
    """Helper function to find a text item on the canvas by its content."""
    for item_id in canvas.find_all():
        if canvas.type(item_id) == "text":
            if text_to_find in canvas.itemcget(item_id, "text"):
                return item_id
    return None


def test_draw_simple_bracket(bracket_canvas, simple_bracket_data):
    """Tests if a simple bracket is drawn with the correct player names."""
    bracket_canvas.draw_bracket(
        simple_bracket_data, next_match=None, bracket_winner=None
    )

    # Assert that player names are present on the canvas
    assert find_text_item(bracket_canvas, "Alice") is not None
    assert find_text_item(bracket_canvas, "Bob") is not None
    assert find_text_item(bracket_canvas, "Charlie") is not None
    assert find_text_item(bracket_canvas, "David") is not None

    # Check if the round titles are drawn
    assert find_text_item(bracket_canvas, "Runde 1") is not None
    assert find_text_item(bracket_canvas, "Runde 2") is not None


def test_draw_bracket_with_winner(bracket_canvas, simple_bracket_data):
    """Tests if the bracket winner is drawn correctly with a trophy icon."""
    final_winner = "Charlie"
    simple_bracket_data[1][0]["winner"] = final_winner  # Set winner for the final match

    bracket_canvas.draw_bracket(
        simple_bracket_data, next_match=None, bracket_winner=final_winner
    )

    winner_item_id = find_text_item(bracket_canvas, f"🏆 {final_winner}")
    assert winner_item_id is not None, "Winner text with trophy should be drawn."


def test_draw_bracket_with_next_match_highlight(bracket_canvas, simple_bracket_data):
    """Tests if the next match to be played is highlighted with a colored rectangle."""
    next_match_to_play = simple_bracket_data[1][0]  # The final match

    bracket_canvas.draw_bracket(
        simple_bracket_data, next_match=next_match_to_play, bracket_winner=None
    )

    # Find the highlight rectangle by checking the color of all rectangles on the canvas.
    # This is more robust than assuming the drawing order.
    highlight_rects_found = []
    for item_id in bracket_canvas.find_all():
        if bracket_canvas.type(item_id) == "rectangle":
            if (
                bracket_canvas.itemcget(item_id, "fill")
                == bracket_canvas.NEXT_MATCH_COLOR
            ):
                highlight_rects_found.append(item_id)

    assert (
        len(highlight_rects_found) == 1
    ), "Exactly one highlight rectangle should be drawn for the next match."


def test_draw_bracket_with_bye(bracket_canvas):
    """Tests if a BYE is drawn with the correct styling."""
    bracket_data = [[{"player1": "Alice", "player2": "BYE", "winner": "Alice"}]]
    bracket_canvas.draw_bracket(bracket_data, next_match=None, bracket_winner=None)

    bye_item_id = find_text_item(bracket_canvas, "BYE")
    assert bye_item_id is not None, "BYE text should be drawn."

    # Check if the BYE text has the specific loser styling
    bye_color = bracket_canvas.itemcget(bye_item_id, "fill")
    assert bye_color == bracket_canvas.LOSER_COLOR
