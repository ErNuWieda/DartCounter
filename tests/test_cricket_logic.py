import unittest
import sys
import os
from unittest.mock import MagicMock

# Füge das Hauptverzeichnis zum Python-Pfad hinzu, damit wir die core-Module importieren können
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.cricket import Cricket, CRICKET_TARGET_VALUES

# --- Mock-Klassen zur Simulation von Abhängigkeiten ---

class MockPlayer:
    """Eine Mock-Klasse für Player, die für Cricket-Tests benötigt wird."""
    def __init__(self, name):
        self.name = name
        self.score = 0
        # Jeder Spieler startet mit 0 Treffern auf jedes Ziel
        self.hits = {target: 0 for target in CRICKET_TARGET_VALUES.keys()}
        self.targets = list(CRICKET_TARGET_VALUES.keys())
        self.sb = MagicMock() # Verwenden von MagicMock für das Scoreboard

    def update_score_value(self, value, subtract=True):
        if subtract:
            self.score -= value
        else:
            self.score += value

class MockGame:
    """Eine Mock-Klasse für Game, um den Spielmodus (Cricket/Cut Throat) zu definieren."""
    def __init__(self, name="Cricket"):
        self.name = name
        self.end = False
        self.round = 1

# --- Die eigentliche Test-Klasse ---

class TestCricketLogic(unittest.TestCase):

    def setUp(self):
        """Wird vor jedem einzelnen Test ausgeführt."""
        # Setup für Standard-Cricket
        self.mock_game_cricket = MockGame(name="Cricket")
        self.cricket_logic = Cricket(self.mock_game_cricket)
        self.player1_cricket = MockPlayer("Alice")
        self.player2_cricket = MockPlayer("Bob")
        self.players_cricket = [self.player1_cricket, self.player2_cricket]

        # Setup für Cut-Throat-Cricket
        self.mock_game_cut_throat = MockGame(name="Cut Throat")
        self.cut_throat_logic = Cricket(self.mock_game_cut_throat)
        self.player1_ct = MockPlayer("Charlie")
        self.player2_ct = MockPlayer("David")
        self.players_ct = [self.player1_ct, self.player2_ct]

    def test_closing_target(self):
        """Testet, dass das dreimalige Treffen eines Ziels dieses schließt."""
        player = self.player1_cricket
        self.assertEqual(player.hits["20"], 0)
        # Ein Wurf auf Triple 20 sollte das Ziel sofort schließen
        self.cricket_logic._handle_throw(player, "Triple", 20, self.players_cricket)
        self.assertEqual(player.hits["20"], 3)

    def test_cricket_scoring(self):
        """Testet das Standard-Cricket-Scoring, nachdem ein Ziel geschlossen wurde."""
        player = self.player1_cricket
        # Schließe die 20 für Alice
        player.hits["20"] = 3
        
        # Alice trifft eine weitere 20, Bob hat sie noch nicht geschlossen
        self.cricket_logic._handle_throw(player, "Single", 20, self.players_cricket)
        
        self.assertEqual(player.score, 20)
        self.assertEqual(self.player2_cricket.score, 0)

    def test_cricket_no_scoring_when_opponent_closed(self):
        """Testet, dass keine Punkte erzielt werden, wenn der Gegner das Ziel ebenfalls geschlossen hat."""
        # Alice schließt die 20
        self.player1_cricket.hits["20"] = 3
        # Bob schließt die 20 ebenfalls
        self.player2_cricket.hits["20"] = 3
        
        # Alice trifft eine weitere 20
        self.cricket_logic._handle_throw(self.player1_cricket, "Single", 20, self.players_cricket)
        
        # Es sollten keine Punkte hinzugefügt werden
        self.assertEqual(self.player1_cricket.score, 0)

    def test_cut_throat_scoring(self):
        """Testet das Cut-Throat-Scoring (Punkte werden den Gegnern hinzugefügt)."""
        player = self.player1_ct
        # Charlie schließt die 19
        player.hits["19"] = 3
        
        # Charlie trifft eine weitere Double 19, David hat sie noch nicht geschlossen
        self.cut_throat_logic._handle_throw(player, "Double", 19, self.players_ct)
        
        # Charlies Punktestand sollte 0 bleiben
        self.assertEqual(player.score, 0)
        # Davids Punktestand sollte um 38 (2 * 19) steigen
        self.assertEqual(self.player2_ct.score, 38)

    def test_bullseye_counts_as_two_marks(self):
        """Testet, dass ein Bullseye als zwei Treffer auf 'Bull' zählt."""
        player = self.player1_cricket
        self.assertEqual(player.hits["Bull"], 0)
        self.cricket_logic._handle_throw(player, "Bullseye", 50, self.players_cricket)
        self.assertEqual(player.hits["Bull"], 2)

    def test_win_condition_cricket(self):
        """Testet die Gewinnbedingung für Standard-Cricket."""
        player = self.player1_cricket
        # Schließe alle Ziele für Alice
        for target in player.targets:
            player.hits[target] = 3
        
        # Alice hat einen höheren Punktestand als Bob
        player.score = 100
        self.player2_cricket.score = 50
        
        # Ein letzter (nicht wertender) Wurf, um die Gewinnprüfung auszulösen
        result = self.cricket_logic._handle_throw(player, "Single", 1, self.players_cricket)
        
        self.assertTrue(self.mock_game_cricket.end)
        self.assertIn("gewinnt", result)

    def test_no_win_if_score_is_lower_cricket(self):
        """Testet, dass das Spiel nicht endet, wenn ein Spieler alle Ziele schließt, aber einen niedrigeren Punktestand hat."""
        player = self.player1_cricket
        # Schließe alle Ziele für Alice
        for target in player.targets:
            player.hits[target] = 3
            
        # Alice hat einen niedrigeren Punktestand als Bob
        player.score = 50
        self.player2_cricket.score = 100
        
        # Ein letzter Wurf
        result = self.cricket_logic._handle_throw(player, "Single", 1, self.players_cricket)
        
        self.assertFalse(self.mock_game_cricket.end)
        self.assertIsNone(result)

    def test_win_condition_cut_throat(self):
        """Testet die Gewinnbedingung für Cut-Throat-Cricket (niedrigster Punktestand gewinnt)."""
        player = self.player1_ct
        # Schließe alle Ziele für Charlie
        for target in player.targets:
            player.hits[target] = 3
            
        # Charlie hat einen niedrigeren Punktestand als David
        player.score = 50
        self.player2_ct.score = 100
        
        # Ein letzter Wurf, um die Gewinnprüfung auszulösen
        result = self.cut_throat_logic._handle_throw(player, "Single", 1, self.players_ct)
        
        self.assertTrue(self.mock_game_cut_throat.end)
        self.assertIn("gewinnt", result)

if __name__ == '__main__':
    unittest.main()