import unittest
import sys
import os
from unittest.mock import MagicMock

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Tactics verwendet die Cricket-Logik, aber mit einem anderen Zielsatz.
# Wir importieren die Logik-Klasse und den spezifischen Zielsatz.
from core.cricket import Cricket, TACTICS_TARGETS

# --- Mock-Klassen zur Simulation von Abhängigkeiten ---

class MockPlayer:
    """Eine Mock-Klasse für Player, die für Tactics-Tests benötigt wird."""
    def __init__(self, name):
        self.name = name
        self.score = 0
        # Jeder Spieler startet mit 0 Treffern auf jedes Tactics-Ziel
        self.hits = {target: 0 for target in TACTICS_TARGETS}
        self.targets = TACTICS_TARGETS
        self.sb = MagicMock()

    def update_score_value(self, value, subtract=False):
        # Tactics addiert Punkte, genau wie Standard-Cricket
        if not subtract:
            self.score += value

class MockGame:
    """Eine Mock-Klasse für Game, die den Spielmodus 'Tactics' simuliert."""
    def __init__(self):
        self.name = "Tactics" # Dies ist entscheidend, damit die Logik die richtigen Ziele wählt
        self.end = False
        self.round = 1

# --- Die eigentliche Test-Klasse ---

class TestTacticsLogic(unittest.TestCase):

    def setUp(self):
        """Wird vor jedem einzelnen Test ausgeführt."""
        self.mock_game = MockGame()
        # Die Logik-Klasse ist Cricket, aber sie wird mit einem Tactics-Spiel konfiguriert
        self.tactics_logic = Cricket(self.mock_game)
        self.player1 = MockPlayer("Alice")
        self.player2 = MockPlayer("Bob")
        self.players = [self.player1, self.player2]

    def test_hit_correct_target(self):
        """Testet, dass das Treffen eines gültigen Tactics-Ziels (z.B. 12) die Treffer erhöht."""
        player = self.player1
        self.assertEqual(player.hits["12"], 0)
        
        # Ein Wurf auf Triple 12 sollte das Ziel sofort schließen
        self.tactics_logic._handle_throw(player, "Triple", 12, self.players)
        self.assertEqual(player.hits["12"], 3)

    def test_hit_wrong_target(self):
        """Testet, dass das Treffen eines ungültigen Ziels (z.B. 9) ignoriert wird."""
        player = self.player1
        # Die 9 ist kein Ziel bei Tactics
        self.tactics_logic._handle_throw(player, "Single", 9, self.players)
        # Die Trefferliste sollte unverändert sein
        self.assertTrue(all(hit_count == 0 for hit_count in player.hits.values()))

    def test_scoring_after_closing_target(self):
        """Testet die Punktvergabe, nachdem ein Ziel geschlossen wurde."""
        player = self.player1
        # Schließe die 15 für Alice
        player.hits["15"] = 3
        
        # Alice trifft eine weitere 15, Bob hat sie noch nicht geschlossen
        self.tactics_logic._handle_throw(player, "Single", 15, self.players)
        
        self.assertEqual(player.score, 15)
        self.assertEqual(self.player2.score, 0)

    def test_win_condition(self):
        """Testet die Gewinnbedingung (alle Ziele geschlossen, höchste Punktzahl)."""
        player = self.player1
        # Schließe alle Ziele für Alice
        for target in TACTICS_TARGETS:
            player.hits[target] = 3
        
        # Alice hat einen höheren Punktestand als Bob
        player.score = 150
        self.player2.score = 100
        
        # Ein letzter (nicht wertender) Wurf, um die Gewinnprüfung auszulösen
        result = self.tactics_logic._handle_throw(player, "Single", 1, self.players)
        
        self.assertTrue(self.mock_game.end)
        self.assertIn("gewinnt", result)

if __name__ == '__main__':
    unittest.main()