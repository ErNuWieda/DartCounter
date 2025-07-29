import unittest
import sys
import os
from unittest.mock import MagicMock

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.atc import AtC

# --- Mock-Klassen zur Simulation von Abhängigkeiten ---

class MockPlayer:
    """Eine Mock-Klasse für Player, die für AtC-Tests benötigt wird."""
    def __init__(self, name):
        self.name = name
        self.state = {}  # Wird von der AtC-Logik initialisiert
        self.throws = []
        self.sb = MagicMock() # Mock für das Scoreboard

class MockGame:
    """Eine Mock-Klasse für Game, um Spieloptionen für AtC zu definieren."""
    def __init__(self, opt_atc="Single"):
        self.opt_atc = opt_atc
        self.end = False
        # Die Standard-Zielsequenz für Around the Clock
        self.targets = [i for i in range(1, 21)] + ["Bull"]

# --- Die eigentliche Test-Klasse ---

class TestAtcLogic(unittest.TestCase):

    def setUp(self):
        """Wird vor jedem einzelnen Test ausgeführt."""
        # Setup für "Single" Modus
        self.mock_game_single = MockGame(opt_atc="Single")
        self.atc_logic_single = AtC(self.mock_game_single)
        self.player_single = MockPlayer("Alice")
        self.atc_logic_single.initialize_player_state(self.player_single)

        # Setup für "Double" Modus
        self.mock_game_double = MockGame(opt_atc="Double")
        self.atc_logic_double = AtC(self.mock_game_double)
        self.player_double = MockPlayer("Bob")
        self.atc_logic_double.initialize_player_state(self.player_double)

    def test_initial_target(self):
        """Testet, ob das Startziel für einen Spieler korrekt auf 1 gesetzt wird."""
        self.assertEqual(self.player_single.state['target'], 1)
        self.assertEqual(self.player_double.state['target'], 1)

    def test_hit_correct_target_single_mode(self):
        """Testet das Treffen des korrekten Ziels im Single-Modus."""
        # Spieler muss die 1 treffen
        self.atc_logic_single._handle_throw(self.player_single, "Single", 1, [])
        # Das nächste Ziel sollte 2 sein
        self.assertEqual(self.player_single.state['target'], 2)

    def test_hit_wrong_target(self):
        """Testet, dass das Ziel sich nicht ändert, wenn ein falsches Segment getroffen wird."""
        # Spieler muss die 1 treffen, trifft aber die 5
        self.atc_logic_single._handle_throw(self.player_single, "Single", 5, [])
        # Das Ziel sollte bei 1 bleiben
        self.assertEqual(self.player_single.state['target'], 1)

    def test_hit_correct_target_double_mode(self):
        """Testet das Treffen des korrekten Ziels im Double-Modus."""
        # Spieler muss Double 1 treffen
        self.atc_logic_double._handle_throw(self.player_double, "Double", 1, [])
        # Das nächste Ziel sollte 2 sein
        self.assertEqual(self.player_double.state['target'], 2)

    def test_fail_correct_target_double_mode(self):
        """Testet einen Fehlschlag im Double-Modus (richtiges Segment, falscher Ring)."""
        # Spieler muss Double 1 treffen, trifft aber Single 1
        self.atc_logic_double._handle_throw(self.player_double, "Single", 1, [])
        # Das Ziel sollte bei 1 bleiben
        self.assertEqual(self.player_double.state['target'], 1)

    def test_win_condition_with_bullseye(self):
        """Testet die Gewinnbedingung durch Treffen des Bullseye als letztes Ziel."""
        # Setze das Ziel des Spielers manuell auf "Bull"
        self.player_single.state['target'] = "Bull"
        # Spieler trifft Bullseye
        result = self.atc_logic_single._handle_throw(self.player_single, "Bullseye", 50, [])
        
        self.assertTrue(self.mock_game_single.end)
        self.assertIn("gewinnt", result)

    def test_win_condition_with_bull(self):
        """Testet die Gewinnbedingung durch Treffen des Bull als letztes Ziel."""
        self.player_single.state['target'] = "Bull"
        # Spieler trifft Bull
        result = self.atc_logic_single._handle_throw(self.player_single, "Bull", 25, [])
        
        self.assertTrue(self.mock_game_single.end)
        self.assertIn("gewinnt", result)

    def test_undo_throw(self):
        """Testet, ob die Undo-Funktion das Ziel des Spielers korrekt zurücksetzt."""
        # Spieler trifft Ziel 1 und rückt zu Ziel 2 vor
        self.atc_logic_single._handle_throw(self.player_single, "Single", 1, [])
        self.assertEqual(self.player_single.state['target'], 2)
        
        # Mache den Wurf rückgängig
        # Annahme: Der letzte Wurf wird aus player.throws entfernt, bevor _handle_throw_undo aufgerufen wird
        self.player_single.throws.pop()
        self.atc_logic_single._handle_throw_undo(self.player_single, "Single", 1, [])
        
        # Das Ziel sollte wieder 1 sein
        self.assertEqual(self.player_single.state['target'], 1)

if __name__ == '__main__':
    unittest.main()