# Dartcounter Deluxe
# Copyright (C) 2025 Martin Hehl (airnooweeda)
# Copyright (C) 2025 I Deny Code Assist
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
from core.dartboard_geometry import DartboardGeometry
from core.dartboard import DartBoard


class TestDartboardGeometry:

    # Test get_segment_from_coords
    def test_get_segment_from_coords_center(self):
        # Testet mit der korrekten Referenzgröße der Klasse
        size = DartboardGeometry.ORIGINAL_SIZE
        center = DartboardGeometry.CENTER
        assert (
            DartboardGeometry.get_segment_from_coords(center, center, size=size)
            == "Bullseye"
        )

    def test_get_segment_from_coords_specific_segments(self):
        # Testet mit der korrekten Referenzgröße der Klasse
        size = DartboardGeometry.ORIGINAL_SIZE
        center = DartboardGeometry.CENTER
        # Oben im Board, im Triple-20-Segment
        # Radius für T20 ist zwischen 470 und 520. Winkel ist -90 Grad.
        y_pos_t20 = center - (DartboardGeometry.RADIEN["triple_inner"] + 10)
        assert (
            DartboardGeometry.get_segment_from_coords(center, y_pos_t20, size=size)
            == "20"
        )
        # Rechts im Board, im Single-6-Segment
        # Radius für S6 ist zwischen 80 und 470. Winkel ist 0 Grad.
        x_pos_s6 = center + (DartboardGeometry.RADIEN["bull"] + 10)
        assert (
            DartboardGeometry.get_segment_from_coords(x_pos_s6, center, size=size)
            == "6"
        )

    def test_get_segment_from_coords_miss(self):
        # Außerhalb des Boards
        size = DartboardGeometry.ORIGINAL_SIZE
        assert DartboardGeometry.get_segment_from_coords(0, 0, size=size) == "Miss"
        assert (
            DartboardGeometry.get_segment_from_coords(size - 1, size - 1, size=size)
            == "Miss"
        )

    # Test get_target_coords
    def test_get_target_coords(self):
        # Teste einige bekannte Ziel-Koordinaten
        assert DartboardGeometry.get_target_coords("T20") is not None
        assert DartboardGeometry.get_target_coords("BE") == (
            DartboardGeometry.CENTER,
            DartboardGeometry.CENTER,
        )
        assert DartboardGeometry.get_target_coords("INVALID") is None


@pytest.fixture
def mock_dartboard():
    """Fixture to create a mocked DartBoard instance for testing UI-independent logic."""
    # Mock the parent 'spiel' object
    mock_spiel = MagicMock()

    # We can't instantiate DartBoard directly because it creates a Toplevel window.
    # So we patch the __init__ method to prevent UI creation.
    with patch.object(DartBoard, "__init__", lambda s, spiel: None):
        board = DartBoard(mock_spiel)
        board.spiel = mock_spiel

        # Manually set the attributes that would be created in __init__
        board.center_x = 500
        board.center_y = 500
        # Simulate a board scaled to 1000x1000 for easy calculations
        scale = 1000 / DartboardGeometry.ORIGINAL_SIZE
        board.skaliert = {
            k: int(v * scale) for k, v in DartboardGeometry.RADIEN.items()
        }

        yield board


class TestDartBoard:
    """Tests for the DartBoard class, which handles user interaction and click logic."""

    def test_get_ring_segment_logic(self, mock_dartboard):
        """Tests the core logic of identifying the ring and segment from coordinates."""
        board = mock_dartboard

        # Test Bullseye (scaled radius: 13)
        assert board.get_ring_segment(500, 500) == (
            "Bullseye",
            50,
        ), "Ein Wurf genau in die Mitte sollte ein Bullseye sein."
        # Test Bull (25) (scaled radii: bullseye=13, bull=36)
        assert board.get_ring_segment(500, 520) == ("Bull", 25)
        # Test Triple 20 (at the top) (scaled radii: triple_inner=213, triple_outer=236)
        assert board.get_ring_segment(500, 500 - 220) == ("Triple", 20)
        # Test Double 3 (unten) (scaled radii: double_inner=356, double_outer=379)
        # Angle for 3 is 270 degrees (straight down).
        assert board.get_ring_segment(500, 500 + 360) == ("Double", 3)
        # Test Single 1 (top right, angle ~72 deg) (scaled radii: bull=36, triple_inner=213)
        # Die alten Koordinaten (600, 400) ergaben einen Winkel von 45°, was im 18er-Segment liegt.
        assert board.get_ring_segment(531, 405) == ("Single", 1)
        # Test Miss
        assert board.get_ring_segment(0, 0) == ("Miss", 0)
