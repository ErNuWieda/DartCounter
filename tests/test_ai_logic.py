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

import unittest
from unittest.mock import MagicMock

from core.ai_logic import AILogic
from core.player import Player

class TestAILogic(unittest.TestCase):
    """Testet die strategische Logik der KI."""

    def setUp(self):
        """Erstellt eine Mock-Instanz für game_logic und die AILogic."""
        # Mock für die game_logic, die AILogic benötigt
        self.mock_game_logic = MagicMock()
        self.mock_game_logic.game.name = "501"
        self.mock_game_logic.opt_out = "Double"
        
        # Die zu testende Instanz
        self.ai_logic = AILogic(self.mock_game_logic)

        # Mock für einen Spieler
        self.mock_player = MagicMock(spec=Player)
        self.mock_player.throws = [] # Start eines neuen Zugs

    def test_determine_target_for_x01_direct_checkout(self):
        """Testet, dass die KI auf ein bekanntes Checkout-Ziel zielt."""
        self.mock_player.score = 170 # Bekannter 3-Dart-Checkout: T20 T20 BE
        expected_coords = self.ai_logic.geometry.get_target_coords("T20")
        target_coords = self.ai_logic._determine_target_for_x01(self.mock_player)
        self.assertEqual(target_coords, expected_coords, "Bei 170 Rest sollte das Ziel T20 sein.")

    def test_determine_target_for_x01_setup_shot_to_good_leave(self):
        """Testet, dass die KI einen Setup-Wurf macht, um einen guten Rest zu hinterlassen."""
        self.mock_player.score = 180 # Kein Checkout, aber T20 hinterlässt 120 (guter Rest)
        expected_coords = self.ai_logic.geometry.get_target_coords("T20")
        target_coords = self.ai_logic._determine_target_for_x01(self.mock_player)
        self.assertEqual(target_coords, expected_coords, "Bei 180 Rest sollte das Ziel T20 sein, um 120 zu hinterlassen.")

    def test_determine_target_for_x01_setup_shot_avoids_bad_leave(self):
        """Testet, dass die KI ein niedrigeres Ziel wählt, um einen besseren Rest zu erzielen."""
        # Bei 99 Rest: Wurf auf T20 -> 39 (schlecht). Wurf auf T19 -> 42 (schlecht).
        # Wurf auf T16 -> 51 (gut!). Die KI sollte T16 als Ziel wählen.
        self.mock_player.score = 99
        expected_coords = self.ai_logic.geometry.get_target_coords("T16")
        target_coords = self.ai_logic._determine_target_for_x01(self.mock_player)
        self.assertEqual(target_coords, expected_coords, "Bei 99 Rest sollte das Ziel T16 sein, um 51 zu hinterlassen.")

    def test_determine_target_for_x01_low_score_fallback(self):
        """Testet, dass die KI bei niedrigem Score auf ein Single-Feld zielt, um Bust zu vermeiden."""
        self.mock_player.score = 61 # T20 würde busten, S20 ist sicher.
        expected_coords = self.ai_logic.geometry.get_target_coords("S20")
        target_coords = self.ai_logic._determine_target_for_x01(self.mock_player)
        self.assertEqual(target_coords, expected_coords, "Bei 61 Rest sollte das Ziel S20 sein, um einen Bust zu vermeiden.")

    def test_determine_target_for_non_x01_game(self):
        """Testet, dass die KI für andere Spiele auf ein Standardziel (T20) zurückfällt."""
        self.mock_game_logic.game.name = "Cricket"
        expected_coords = self.ai_logic.geometry.get_target_coords("T20")
        target_coords = self.ai_logic.determine_target(self.mock_player)
        self.assertEqual(target_coords, expected_coords, "Für Cricket sollte das Standardziel T20 sein.")

if __name__ == '__main__':
    unittest.main(verbosity=2)
