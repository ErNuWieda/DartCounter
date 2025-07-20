import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.game import Game

# Da die Player-Klasse ein tk.root-Objekt erwartet, müssen wir es mocken,
# bevor wir die Game-Klasse importieren.

class MockTk:
    def deiconify(self): pass

class TestGameWithX01(unittest.TestCase):

    def setUp(self):
        """Wird vor jedem Test ausgeführt."""
        # Wir "patchen" messagebox, damit keine echten Fenster aufpoppen
        self.patcher = patch('core.game.messagebox')
        self.mock_messagebox = self.patcher.start()

        # Erstelle eine Instanz des Spiels
        mock_root = MockTk()
        player_names = ["Alice", "Bob"]
        # (Spielname, Opt-In, Opt-Out, Opt-Atc, Count-To, Lifes, Rounds)
        game_options = ("301", "Single", "Double", "Single", "301", "3", "7")
        
        # Wir müssen die Scoreboard-Erstellung in der Game-Klasse mocken, da sie UI erzeugt.
        with patch('core.game.ScoreBoard') as MockScoreBoard:
            self.game = Game(mock_root, game_options, player_names)

    def tearDown(self):
        """Wird nach jedem Test ausgeführt, um den Patcher zu stoppen."""
        self.patcher.stop()

    def test_initial_state(self):
        """Testet den Anfangszustand des Spiels."""
        self.assertEqual(self.game.name, "301")
        self.assertEqual(len(self.game.players), 2)
        self.assertEqual(self.game.current_player().name, "Alice")
        self.assertEqual(self.game.round, 1)
        for player in self.game.players:
            self.assertEqual(player.score, 301)

    def test_full_turn_and_next_player(self):
        """Simuliert einen vollen Zug und den Wechsel zum nächsten Spieler."""
        alice = self.game.current_player()
        self.assertEqual(alice.name, "Alice")

        # Alice wirft 3 Darts
        self.game.throw("Triple", 20) # 60
        self.game.throw("Single", 20) # 20
        self.game.throw("Single", 5)  # 5
        
        self.assertEqual(alice.score, 301 - 60 - 20 - 5)
        self.assertEqual(len(alice.throws), 3)

        # Wechsel zum nächsten Spieler
        self.game.next_player()
        bob = self.game.current_player()
        self.assertEqual(bob.name, "Bob")
        self.assertEqual(self.game.round, 1) # Immer noch Runde 1

if __name__ == '__main__':
    unittest.main()