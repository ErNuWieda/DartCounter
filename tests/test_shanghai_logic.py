import unittest
import sys
import os
from unittest.mock import MagicMock

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.shanghai import Shanghai

# --- Mock-Klassen zur Simulation von Abhängigkeiten ---

class MockPlayer:
    """Eine Mock-Klasse für Player, die für Shanghai-Tests benötigt wird."""
    def __init__(self, name):
        self.name = name
        self.state = {}  # Wird von der Shanghai-Logik initialisiert
        self.throws = []
        self.sb = MagicMock() # Mock für das Scoreboard

    def update_score_value(self, value, subtract=False):
        # Shanghai addiert nur Punkte
        if not subtract:
            self.state['score'] += value

class MockGame:
    """Eine Mock-Klasse für Game, um Spieloptionen für Shanghai zu definieren."""
    def __init__(self, rounds=7):
        self.rounds = rounds
        self.end = False
        # Die Zielsequenz für Shanghai hängt von der Anzahl der Runden ab
        self.targets = list(range(1, rounds + 1))
        self.round = 1

    def get_score(self, ring, segment):
        # Diese Methode ist entscheidend und wird direkt aus der echten Game-Klasse kopiert
        if ring == "Bullseye": return 50
        if ring == "Bull": return 25
        if ring == "Double": return segment * 2
        if ring == "Triple": return segment * 3
        if ring == "Single": return segment
        return 0

# --- Die eigentliche Test-Klasse ---

class TestShanghaiLogic(unittest.TestCase):

    def setUp(self):
        """Wird vor jedem einzelnen Test ausgeführt."""
        self.mock_game = MockGame(rounds=7)
        self.shanghai_logic = Shanghai(self.mock_game)
        self.player1 = MockPlayer("Alice")
        self.player2 = MockPlayer("Bob")
        self.players = [self.player1, self.player2]
        self.shanghai_logic.initialize_player_state(self.player1)
        self.shanghai_logic.initialize_player_state(self.player2)

    def test_initial_state(self):
        """Testet, ob der Anfangszustand (Ziel und Punktestand) korrekt gesetzt wird."""
        self.assertEqual(self.player1.state['target'], 1)
        self.assertEqual(self.player1.state['score'], 0)

    def test_hit_correct_target_and_score(self):
        """Testet das Treffen des korrekten Ziels und das Sammeln von Punkten."""
        # Das Ziel von Spieler 1 ist 1. Er trifft eine Triple 1.
        self.shanghai_logic._handle_throw(self.player1, "Triple", 1, self.players)
        self.assertEqual(self.player1.state['score'], 3)

    def test_hit_wrong_target(self):
        """Testet, dass das Treffen des falschen Ziels keine Punkte bringt."""
        # Das Ziel von Spieler 1 ist 1. Er trifft eine Single 5.
        self.shanghai_logic._handle_throw(self.player1, "Single", 5, self.players)
        self.assertEqual(self.player1.state['score'], 0)

    def test_shanghai_win_condition(self):
        """Testet den sofortigen Sieg durch ein Shanghai."""
        self.shanghai_logic.update_target_for_round(self.player1, 3) # Ziel ist jetzt 3
        
        # Spieler 1 wirft ein Single 3, Double 3 und Triple 3 in einer Runde
        self.player1.throws = [] # Würfe für den Test zurücksetzen
        self.shanghai_logic._handle_throw(self.player1, "Single", 3, self.players)
        self.shanghai_logic._handle_throw(self.player1, "Double", 3, self.players)
        result = self.shanghai_logic._handle_throw(self.player1, "Triple", 3, self.players)

        self.assertTrue(self.mock_game.end)
        self.assertIn("SHANGHAI", result)

    def test_win_by_points_at_end_of_game(self):
        """Testet den Sieg durch den höchsten Punktestand nach Abschluss aller Runden."""
        self.player1.state['score'] = 150
        self.player2.state['score'] = 100
        self.mock_game.round = 8 # Das Spiel hat 7 Runden, Runde 8 bedeutet, das Spiel ist vorbei
        
        # Ein letzter Wurf des letzten Spielers löst die Gewinnprüfung aus
        result = self.shanghai_logic._handle_throw(self.player2, "Miss", 0, self.players)
        
        self.assertTrue(self.mock_game.end)
        self.assertIn("Alice gewinnt mit dem höchsten Punktestand", result)

if __name__ == '__main__':
    unittest.main()