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
from unittest.mock import Mock, patch

# Fügt das Hauptverzeichnis zum Python-Pfad hinzu, damit die core-Module gefunden werden.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.ai_player import AIPlayer
from core.player_profile import PlayerProfile
from core.player import Player
from core.checkout_calculator import CheckoutCalculator

class TestAIPlayer(unittest.TestCase):
    """Testet die Funktionalität der AIPlayer-Klasse."""

    def setUp(self):
        """Setzt eine Testumgebung mit einem Mock-Spiel und einem KI-Spieler auf."""
        # Mock für das Game-Objekt und seine Abhängigkeiten
        self.mock_game = Mock()
        self.mock_game.db = Mock()
        self.mock_game.db.root = Mock()
        self.mock_game.game = Mock()  # Für spielspezifische Logik (z.B. Cricket-Ziele)
        self.mock_game.end = False

        # Mock für das Spielerprofil
        self.ai_profile = PlayerProfile(
            name="RoboCop",
            is_ai=True,
            difficulty='Fortgeschritten'
        )

        # Erstellt die AIPlayer-Instanz für die Tests
        self.ai_player = AIPlayer(name="RoboCop", game=self.mock_game, profile=self.ai_profile)
        self.ai_player.score = 501 # Standard-Score für X01
        self.ai_player.turn_is_over = False

        # Fügt den KI-Spieler zur Spielerliste des Mock-Spiels hinzu
        self.mock_game.players = [self.ai_player]

    def test_initialization(self):
        """Testet, ob der AIPlayer korrekt initialisiert wird."""
        self.assertIsInstance(self.ai_player, AIPlayer)
        self.assertTrue(self.ai_player.is_ai())
        self.assertEqual(self.ai_player.name, "RoboCop")
        self.assertEqual(self.ai_player.difficulty, 'Fortgeschritten')
        self.assertIn('radius', self.ai_player.settings)
        self.assertEqual(self.ai_player.settings['radius'], 60)
        self.assertEqual(self.ai_player.settings['delay'], 600)

    def test_get_strategic_target_for_x01_high_score(self):
        """Testet die Zielauswahl für X01 bei hohem Punktestand (kein Finish)."""
        self.mock_game.name = "501"
        self.ai_player.score = 171 # Knapp über dem Finish-Bereich
        target = self.ai_player._get_strategic_target(throw_number=1)
        self.assertEqual(target, ("Triple", 20))

    @patch('core.ai_player.CheckoutCalculator.get_checkout_suggestion')
    def test_get_strategic_target_for_x01_checkout_path(self, mock_get_suggestion):
        """Testet die Zielauswahl, wenn ein Checkout-Pfad verfügbar ist."""
        self.mock_game.name = "501"
        self.mock_game.opt_out = "Double"
        
        # Szenario 1: 100 Rest, 3 Darts -> T20, D20
        self.ai_player.score = 100
        mock_get_suggestion.return_value = "T20, D20"
        target = self.ai_player._get_strategic_target(throw_number=1)
        self.assertEqual(target, ("Triple", 20))
        mock_get_suggestion.assert_called_once_with(100, "Double", 3)

        # Szenario 2: 40 Rest, 2 Darts -> D20
        self.ai_player.score = 40
        mock_get_suggestion.reset_mock()
        mock_get_suggestion.return_value = "D20"
        target = self.ai_player._get_strategic_target(throw_number=2)
        self.assertEqual(target, ("Double", 20))
        mock_get_suggestion.assert_called_once_with(40, "Double", 2)

    @patch('core.ai_player.CheckoutCalculator.get_checkout_suggestion')
    def test_get_strategic_target_for_x01_no_checkout_path(self, mock_get_suggestion):
        """Testet die Zielauswahl, wenn kein Checkout-Pfad gefunden wird (Fallback)."""
        self.mock_game.name = "501"
        self.ai_player.score = 169 # Kein 2-Dart-Finish
        self.mock_game.opt_out = "Double"
        mock_get_suggestion.return_value = "Kein Finish möglich"

        target = self.ai_player._get_strategic_target(throw_number=2) # 2 Darts übrig
        self.assertEqual(target, ("Triple", 20)) # Fallback auf Standardstrategie
        mock_get_suggestion.assert_called_once_with(169, "Double", 2)

    def test_get_strategic_target_for_cricket_opening(self):
        """Testet die Zielauswahl für Cricket, wenn noch Ziele offen sind."""
        self.mock_game.name = "Cricket"
        self.mock_game.game.get_targets.return_value = ['20', '19', '18', '17', '16', '15', 'Bull']
        
        # KI hat noch nichts getroffen
        self.ai_player.state['hits'] = {}
        target = self.ai_player._get_strategic_target(throw_number=1)
        self.assertEqual(target, ("Triple", 20))

        # KI hat die 20 geschlossen und sollte nun auf die 19 zielen
        self.ai_player.state['hits'] = {'20': 3}
        target = self.ai_player._get_strategic_target(throw_number=1)
        self.assertEqual(target, ("Triple", 19))

    def test_get_strategic_target_for_cricket_scoring(self):
        """Testet die Zielauswahl für Cricket, wenn die eigenen Ziele geschlossen sind."""
        self.mock_game.name = "Cricket"
        targets = ['20', '19', 'Bull']
        self.mock_game.game.get_targets.return_value = targets

        # Mock für einen Gegner, der die '19' noch nicht geschlossen hat
        mock_opponent = Mock(spec=Player)
        mock_opponent.state = {'hits': {'20': 3, '19': 2, 'Bull': 3}}
        
        # KI hat alle Ziele geschlossen
        self.ai_player.state['hits'] = {'20': 3, '19': 3, 'Bull': 3}
        self.mock_game.players = [self.ai_player, mock_opponent]

        # Die KI sollte nun versuchen, auf dem offenen Ziel '19' des Gegners zu punkten
        target = self.ai_player._get_strategic_target(throw_number=1)
        self.assertEqual(target, ("Triple", 19))

    def test_get_strategic_target_fallback(self):
        """Testet die Fallback-Zielauswahl."""
        # Verwendet einen Spielmodus ohne implementierte Strategie
        self.mock_game.name = "Unknown Game"
        target = self.ai_player._get_strategic_target(throw_number=1)
        self.assertEqual(target, ("Bullseye", 50))

    def test_parse_target_string(self):
        """Testet die Hilfsmethode zum Parsen von Ziel-Strings."""
        self.assertEqual(self.ai_player._parse_target_string("T20"), ("Triple", 20))
        self.assertEqual(self.ai_player._parse_target_string("D18"), ("Double", 18))
        self.assertEqual(self.ai_player._parse_target_string("S1"), ("Single", 1))
        self.assertEqual(self.ai_player._parse_target_string("BULL"), ("Bullseye", 50))
        self.assertEqual(self.ai_player._parse_target_string("Bullseye"), ("Bullseye", 50))
        self.assertEqual(self.ai_player._parse_target_string("17"), ("Single", 17))
        self.assertEqual(self.ai_player._parse_target_string("INVALID"), ("Triple", 20))

    @patch('core.ai_player.random.uniform')
    @patch('core.ai_player.math.cos')
    @patch('core.ai_player.math.sin')
    def test_execute_throw_simulates_click(self, mock_sin, mock_cos, mock_uniform):
        """Testet, ob _execute_throw einen Dartwurf korrekt simuliert."""
        # Konfiguriert die Mocks für vorhersagbare "Zufälligkeit"
        mock_uniform.side_effect = [1.5708, 10]  # Winkel = pi/2, Distanz = 10px
        mock_cos.return_value = 0  # cos(pi/2) ≈ 0
        mock_sin.return_value = 1  # sin(pi/2) = 1

        # Mock für die Dartboard-Interaktion
        self.mock_game.db.get_coords_for_target.return_value = (300, 300)  # Zielmitte
        
        # Erwartete Wurfkoordinaten: x=300, y=310
        expected_x, expected_y = 300, 310

        # Führt den Wurf aus
        self.ai_player._execute_throw(1)

        # Verifiziert, dass die Klick-Simulation des Dartboards mit den korrekten Koordinaten aufgerufen wurde
        self.mock_game.db.on_click_simulated.assert_called_once_with(expected_x, expected_y)

    def test_execute_throw_stops_on_bust(self):
        """Testet, ob die KI aufhört zu werfen, wenn der Zug vorbei ist (z.B. Bust)."""
        self.mock_game.db.get_coords_for_target.return_value = (300, 300)
        self.ai_player.turn_is_over = True  # Simuliert einen Bust

        self.ai_player._execute_throw(1)  # Versucht, den ersten Wurf auszuführen

        # Die KI sollte keinen Klick simulieren
        self.mock_game.db.on_click_simulated.assert_not_called()
        # Die KI sollte sofort den nächsten Spieler aufrufen
        self.mock_game.db.root.after.assert_called_once_with(
            self.ai_player.settings['delay'],
            self.mock_game.next_player
        )

    def test_take_turn_initiates_sequence(self):
        """Testet, ob take_turn die Wurfsequenz startet."""
        self.ai_player.take_turn()
        # Es sollte der erste Wurf geplant werden
        self.mock_game.db.root.after.assert_called_once_with(
            self.ai_player.settings['delay'],
            self.ai_player._execute_throw,
            1
        )