import unittest
import sys
import os
from unittest.mock import MagicMock

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.elimination import Elimination

# --- Mock-Klassen zur Simulation von Abhängigkeiten ---

class MockPlayer:
    """Eine Mock-Klasse für Player, die für Elimination-Tests benötigt wird."""
    def __init__(self, name):
        self.name = name
        self.score = 0
        self.throws = []
        self.sb = MagicMock() # Mock für das Scoreboard

    def update_score_value(self, value, subtract=True):
        # Elimination addiert nur Punkte
        if not subtract:
            self.score += value

    def reset_score(self):
        self.score = 0

class MockGame:
    """Eine Mock-Klasse für Game, um Spieloptionen zu definieren."""
    def __init__(self, count_to=301):
        self.count_to = count_to
        self.end = False

    def get_score(self, ring, segment):
        # Diese Methode ist entscheidend und wird direkt aus der echten Game-Klasse kopiert
        if ring == "Bullseye": return 50
        if ring == "Bull": return 25
        if ring == "Double": return segment * 2
        if ring == "Triple": return segment * 3
        if ring == "Single": return segment
        return 0

# --- Die eigentliche Test-Klasse ---

class TestEliminationLogic(unittest.TestCase):

    def setUp(self):
        """Wird vor jedem einzelnen Test ausgeführt."""
        self.mock_game = MockGame(count_to=301)
        self.elimination_logic = Elimination(self.mock_game)
        self.player1 = MockPlayer("Alice")
        self.player2 = MockPlayer("Bob")
        self.players = [self.player1, self.player2]

    def test_simple_scoring(self):
        """Testet die einfache Punkte-Akkumulation."""
        self.elimination_logic._handle_throw(self.player1, "Triple", 20, self.players)
        self.assertEqual(self.player1.score, 60)
        self.elimination_logic._handle_throw(self.player1, "Single", 19, self.players)
        self.assertEqual(self.player1.score, 79)

    def test_eliminate_opponent(self):
        """Testet das Eliminieren eines Gegners durch Erreichen seines genauen Punktestands."""
        self.player2.score = 120 # Bob hat 120 Punkte
        self.player1.score = 60  # Alice hat 60 Punkte

        # Alice wirft eine Triple 20 (60 Punkte), um Bobs Punktestand zu erreichen
        self.elimination_logic._handle_throw(self.player1, "Triple", 20, self.players)

        # Alices Punktestand sollte jetzt 120 sein
        self.assertEqual(self.player1.score, 120)
        # Bobs Punktestand sollte auf 0 zurückgesetzt werden
        self.assertEqual(self.player2.score, 0)

    def test_bust_by_exceeding_target_score(self):
        """Testet, dass der Punktestand eines Spielers zurückgesetzt wird, wenn er den Zielwert überschreitet."""
        self.player1.score = 300
        # Alice wirft eine Single 5, was sie auf 305 bringen würde (Bust)
        self.elimination_logic._handle_throw(self.player1, "Single", 5, self.players)
        # Ihr Punktestand sollte auf den Wert vor dem Wurf zurückgesetzt werden
        self.assertEqual(self.player1.score, 300)

    def test_win_condition(self):
        """Testet die Gewinnbedingung durch genaues Erreichen des Zielwerts."""
        self.player1.score = 241
        # Alice wirft eine Triple 20 (60), um 301 zu erreichen
        result = self.elimination_logic._handle_throw(self.player1, "Triple", 20, self.players)

        self.assertEqual(self.player1.score, 301)
        self.assertTrue(self.mock_game.end)
        self.assertIn("gewinnt", result)

if __name__ == '__main__':
    unittest.main()