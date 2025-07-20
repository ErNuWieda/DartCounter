import unittest
import sys
import os

# Füge das Hauptverzeichnis zum Python-Pfad hinzu, damit wir die core-Module importieren können
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.x01 import X01

# --- Mock-Klassen zur Simulation von Abhängigkeiten ---

class MockScoreboard:
    """Ein Mock für das Scoreboard, um UI-Aufrufe zu vermeiden."""
    def update_score(self, score):
        pass # Tut nichts

class MockPlayer:
    """Ein Mock für die Player-Klasse mit den für X01-Tests benötigten Attributen."""
    def __init__(self, name, start_score):
        self.name = name
        self.score = start_score
        self.has_opened = True # Wir nehmen für die meisten Tests an, der Spieler hat bereits eröffnet
        self.throws = []
        self.sb = MockScoreboard() # Jeder Spieler braucht ein Mock-Scoreboard

    def update_score_value(self, value, subtract=True):
        if subtract:
            self.score -= value
        else:
            self.score += value

class MockGame:
    """Ein Mock für die Game-Klasse."""
    def __init__(self, opt_in="Single", opt_out="Single"):
        self.opt_in = opt_in
        self.opt_out = opt_out
        self.shanghai_finish = False
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

class TestX01Logic(unittest.TestCase):

    def setUp(self):
        """Wird vor jedem einzelnen Test ausgeführt."""
        self.mock_game = MockGame(opt_out="Double")
        self.x01_logic = X01(self.mock_game)
        self.player = MockPlayer("Test Player", 100)

    def test_simple_scoring(self):
        """Testet eine einfache Punktlandung."""
        self.x01_logic._handle_throw(self.player, "Triple", 20, [])
        self.assertEqual(self.player.score, 40)
        self.assertEqual(len(self.player.throws), 1)

    def test_bust_by_going_below_zero(self):
        """Testet einen Bust durch Überwerfen."""
        self.player.score = 50
        self.x01_logic._handle_throw(self.player, "Triple", 20, []) # Wirft 60
        self.assertEqual(self.player.score, 50) # Score darf sich nicht ändern

    def test_bust_on_score_one_with_double_out(self):
        """Testet einen Bust bei Rest 1 im Double-Out-Modus."""
        self.player.score = 41
        self.x01_logic._handle_throw(self.player, "Single", 20, []) # Wirft 20 -> Rest 21
        self.x01_logic._handle_throw(self.player, "Single", 20, []) # Wirft 20 -> Rest 1 -> Bust!
        self.assertEqual(self.player.score, 21) # Score wird auf den Stand vor dem Bust-Wurf zurückgesetzt

    def test_win_with_double_out(self):
        """Testet einen gültigen Gewinn mit Double-Out."""
        self.player.score = 40
        result = self.x01_logic._handle_throw(self.player, "Double", 20, [])
        self.assertEqual(self.player.score, 0)
        self.assertTrue(self.mock_game.end)
        self.assertIn("gewinnt", result)

    def test_failed_win_with_double_out(self):
        """Testet einen ungültigen Checkout (Single statt Double)."""
        self.player.score = 20
        self.x01_logic._handle_throw(self.player, "Single", 20, [])
        self.assertEqual(self.player.score, 20) # Score darf sich nicht ändern, da es ein Bust war
        self.assertFalse(self.mock_game.end)

    def test_undo_throw(self):
        """Testet die Undo-Funktion."""
        self.player.score = 100
        self.x01_logic._handle_throw(self.player, "Single", 20, [])
        self.assertEqual(self.player.score, 80)

        # Jetzt machen wir den Wurf rückgängig
        self.x01_logic._handle_throw_undo(self.player, "Single", 20, [])
        self.assertEqual(self.player.score, 100)

if __name__ == '__main__':
    unittest.main()