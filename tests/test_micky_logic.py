import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.micky import Micky, MICKY_TARGETS

# --- Mock-Klassen zur Simulation von Abhängigkeiten ---

class MockPlayer:
    """Eine Mock-Klasse für Player, die für Micky-Maus-Tests benötigt wird."""
    def __init__(self, name):
        self.name = name
        # Jeder Spieler startet mit 0 Treffern auf jedes Ziel
        self.hits = {target: 0 for target in MICKY_TARGETS}
        self.next_target = MICKY_TARGETS[0] # Startziel
        self.score = 0
        self.sb = MagicMock() # Mock für das Scoreboard

class MockGame:
    """Eine Mock-Klasse für Game, um den Spielzustand zu verwalten."""
    def __init__(self):
        self.name = "Micky Maus"
        self.end = False
        self.round = 1
        self.db = MagicMock() # Für messagebox parent

# --- Die eigentliche Test-Klasse ---

class TestMickyLogic(unittest.TestCase):

    def setUp(self):
        """Wird vor jedem einzelnen Test ausgeführt."""
        # Wir patchen messagebox, damit keine echten Fenster aufpoppen
        self.patcher = patch('core.micky.messagebox')
        self.mock_messagebox = self.patcher.start()

        self.mock_game = MockGame()
        self.micky_logic = Micky(self.mock_game)
        self.player1 = MockPlayer("Alice")
        self.player2 = MockPlayer("Bob")
        self.players = [self.player1, self.player2]

    def tearDown(self):
        """Wird nach jedem Test ausgeführt, um den Patcher zu stoppen."""
        self.patcher.stop()

    def test_hit_correct_target(self):
        """Testet, dass das Treffen eines gültigen Ziels die Trefferanzahl erhöht."""
        self.player1.next_target = "20"
        player = self.player1
        self.assertEqual(player.hits["20"], 0)
        
        # Ein Wurf auf Triple 20 sollte das Ziel sofort schließen
        self.micky_logic._handle_throw(player, "Triple", 20, self.players)
        self.assertEqual(player.hits["20"], 3)

    def test_hit_wrong_target(self):
        """Testet, dass das Treffen eines ungültigen Ziels ignoriert wird."""
        self.player1.next_target = "20"
        player = self.player1
        # Die 11 ist kein Ziel bei Micky Maus
        self.micky_logic._handle_throw(player, "Single", 11, self.players)
        # Die Trefferliste sollte unverändert sein
        self.assertTrue(all(hit_count == 0 for hit_count in player.hits.values()))

    def test_hit_already_closed_target(self):
        """Testet, dass weitere Treffer auf ein geschlossenes Ziel keine Auswirkung haben."""
        self.player1.next_target = "18"
        player = self.player1
        player.hits["18"] = 3 # Die 18 ist bereits geschlossen
        
        # Ein weiterer Wurf auf die 18
        self.micky_logic._handle_throw(player, "Single", 18, self.players)
        # Die Anzahl der Treffer sollte bei 3 bleiben
        self.assertEqual(player.hits["18"], 3)

    def test_win_condition(self):
        """Testet die Gewinnbedingung, wenn ein Spieler alle Ziele geschlossen hat."""
        player = self.player1
        
        # Schließe alle Ziele für Alice, bis auf das letzte (Bull)
        # und setze das nächste Ziel entsprechend
        for target in self.micky_logic.targets[:-1]:
            player.hits[target] = 3
        player.next_target = "Bull"
        
        self.assertFalse(self.mock_game.end)
        
        # Alice trifft das letzte Ziel (Bull) dreimal
        self.micky_logic._handle_throw(player, "Bullseye", 50, self.players) # Zählt als 2 Treffer
        result = self.micky_logic._handle_throw(player, "Bull", 25, self.players) # Der dritte Treffer
        
        self.assertTrue(self.mock_game.end)
        self.assertIn("gewinnt", result)


if __name__ == '__main__':
    unittest.main()