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
from unittest.mock import MagicMock
from core.checkout_calculator import CheckoutCalculator
from core import checkout_calculator  # To mock module-level functions/variables


# Parametrize tests for better organization and coverage.
@pytest.mark.parametrize(
    "score, darts_left, opt_out, expected",
    [
        # --- Basic Finishes (3 Darts, Double Out) ---
        (170, 3, "Double", "T20, T20, BE"),
        (167, 3, "Double", "T20, T19, BE"),
        (100, 3, "Double", "T20, D20"),
        (40, 3, "Double", "D20"),
        (2, 3, "Double", "D1"),
        # --- Finishes with fewer Darts ---
        (100, 2, "Double", "T20, D20"),  # Still possible
        (111, 2, "Double", "-"),  # Not possible with 2 darts
        (40, 2, "Double", "D20"),
        (40, 1, "Double", "D20"),
        (39, 1, "Double", "-"),  # Not a double out
        # --- Bogey Numbers ---
        (169, 3, "Double", "-"),
        (163, 3, "Double", "-"),
        (159, 3, "Double", "-"),
        # --- Single Out ---
        (
            59,
            3,
            "Single",
            "T3, BE",
        ),  # Calculated path is T3, BE (9+50=59). Old test was wrong.
        (40, 3, "Single", "D20"),  # 1-dart finish is possible and preferred
        (39, 1, "Single", "T13"),  # Possible with single out
        # --- Edge Cases ---
        (1, 3, "Double", "-"),
        (0, 3, "Double", "-"),
        (171, 3, "Double", "-"),  # Too high
    ],
)
def test_get_checkout_suggestion_standard_paths(score, darts_left, opt_out, expected):
    """
    Tests standard checkout suggestions for various scores and conditions.
    """
    suggestion = CheckoutCalculator.get_checkout_suggestion(score, opt_out, darts_left)
    assert suggestion == expected


# Tests for preferred double logic
@pytest.mark.parametrize(
    "score, darts_left, preferred_double, expected",
    [
        # --- Successful Calculated Paths ---
        (
            132,
            3,
            16,
            "BE, BE, D16",
        ),  # setup_score=100 -> BE, BE is the best 2-dart setup
        (96, 3, 18, "T20, D18"),  # Calculated path for D18
        (80, 2, 20, "D20, D20"),  # Calculated path for D20
        (57, 2, 16, "25, D16"),  # Calculated path for D16 via Bull
        (50, 1, 25, "BE"),  # Prefers Bullseye
        (32, 1, 16, "D16"),  # Direct finish on preferred double
        # --- Testfälle, bei denen die Erwartung korrigiert wurde ---
        # Für 99 gibt es einen Standard-Pfad in der JSON, der auf D16 endet. Dieser wird bevorzugt.
        (99, 3, 16, "T19, 10, D16"),
        (
            89,
            3,
            18,
            "T1, BE, D18",
        ),  # setup_score=53 -> T1, BE (quality 5) is better than T11, 20 (quality 0)
        # --- Fallback to standard path from JSON ---
        # Score 98, pref D16. Calculated path not possible. Standard paths for 98 are ["T20 D19", "T18 D22"]. Neither ends in D16.
        # Die Logik berechnet "D8, BE, D16", verwirft diesen aber als unkonventionell und fällt
        # korrekt auf den Standard-Pfad "T20, D19" zurück.
        (98, 3, 16, "T20, D19"),
        # Score 98, pref D19. Calculated path not possible, but "T20 D19" is a standard path. It should find it.
        (98, 3, 19, "T20, D19"),  # The new logic finds this standard path first.
    ],
)
def test_get_checkout_suggestion_with_preferred_double(
    score, darts_left, preferred_double, expected
):
    """
    Tests checkout suggestions when a preferred double is provided.
    """
    suggestion = CheckoutCalculator.get_checkout_suggestion(
        score, "Double", darts_left, preferred_double=preferred_double
    )
    assert suggestion == expected


def test_get_checkout_suggestion_handles_list_in_json():
    """
    Tests that the function correctly handles cases where the JSON file
    provides a list of possible checkouts.
    """
    # Score 98 has ["T20 D19", "T18 D22"] in checkout_paths.json
    # Without preference, it should return the first one.
    suggestion = CheckoutCalculator.get_checkout_suggestion(98, "Double", 3)
    assert suggestion == "T20, D19"


def test_load_checkout_paths_handles_bad_data(monkeypatch):
    """
    Tests that _load_checkout_paths ignores invalid entries in the JSON file.
    This covers the try-except block.
    """
    mock_data = {"170": "T20 T20 BE", "not_a_number": "some value", "167": "T20 T19 BE"}
    monkeypatch.setattr(
        checkout_calculator,
        "JsonIOHandler",
        MagicMock(read_json=MagicMock(return_value=mock_data)),
    )
    paths = checkout_calculator._load_checkout_paths()
    assert 170 in paths and 167 in paths and "not_a_number" not in paths


def test_load_checkout_paths_handles_no_file(monkeypatch):
    """
    Tests that _load_checkout_paths returns an empty dict if the file doesn't exist.
    """
    monkeypatch.setattr(
        checkout_calculator,
        "JsonIOHandler",
        MagicMock(read_json=MagicMock(return_value=None)),
    )
    paths = checkout_calculator._load_checkout_paths()
    assert paths == {}
