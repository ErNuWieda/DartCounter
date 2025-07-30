import unittest
from unittest.mock import patch, MagicMock

from tests.test_base import GameLogicTestBase
# Klasse, die getestet wird
from core.micky import Micky
# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player
from core.scoreboard import ScoreBoard

class TestMicky(GameLogicTestBase):
    """Testet die Spiellogik der Micky-Klasse."""

    def setUp(self):
        """Setzt eine kontrollierte Testumgebung für jeden Test auf."""
        self.logic_class_module = 'micky'
        super().setUp()
        self.mock_game.name = "Micky Maus"

        self.micky_logic = Micky(self.mock_game)
        self.mock_game.targets = self.micky_logic.get_targets()

    def _create_player(self):
        """Hilfsfunktion, um eine Player-Instanz für Tests zu erstellen."""
        player = Player(name="Tester", game=self.mock_game)
        self.micky_logic.initialize_player_state(player)
        player.sb = MagicMock(spec=ScoreBoard)
        return player

    def test_initialization(self):
        """Testet, ob ein Spieler korrekt für Micky Maus initialisiert wird."""
        player = self._create_player()
        self.assertEqual(player.score, 0)
        self.assertEqual(player.next_target, "20")
        self.assertEqual(player.hits.get("20"), 0)

    def test_correct_hit_increases_marks(self):
        """Testet, ob ein Treffer auf das korrekte Ziel die Treffer erhöht."""
        player = self._create_player()
        player.next_target = "20"
        
        self.micky_logic._handle_throw(player, "Single", 20, [])
        self.assertEqual(player.hits["20"], 1)
        self.mock_messagebox.showerror.assert_not_called()

    def test_incorrect_hit_shows_error(self):
        """Testet, ob ein Treffer auf ein falsches Ziel einen Fehler anzeigt."""
        player = self._create_player()
        player.next_target = "20"

        self.micky_logic._handle_throw(player, "Single", 19, [])
        self.assertEqual(player.hits["20"], 0)
        self.assertEqual(player.next_target, "20")
        self.mock_messagebox.showerror.assert_called_once()

    def test_closing_target_advances_to_next(self):
        """Testet, ob das Schließen eines Ziels zum nächsten Ziel fortschreitet."""
        player = self._create_player()
        player.next_target = "20"
        player.hits["20"] = 2 # Already 2 hits

        self.micky_logic._handle_throw(player, "Single", 20, [])
        self.assertEqual(player.hits["20"], 3)
        self.assertEqual(player.next_target, "19")

    def test_win_condition(self):
        """Testet die Gewinnbedingung, wenn das letzte Ziel (Bull) geschlossen wird."""
        player = self._create_player()
        
        # Alle Ziele außer Bull schließen
        for target in self.micky_logic.get_targets():
            if target != "Bull":
                player.hits[target] = 3
        
        # Das nächste Ziel sollte Bull sein
        player.next_target = "Bull"
        player.hits["Bull"] = 2 # Zwei Treffer auf Bull

        # Der letzte Wurf, der das Spiel gewinnt
        result = self.micky_logic._handle_throw(player, "Bull", 25, [])

        self.assertTrue(self.mock_game.end)
        self.assertIn("gewinnt", result)

    def test_undo_restores_marks_and_target(self):
        """Testet, ob Undo die Treffer und das nächste Ziel korrekt wiederherstellt."""
        player = self._create_player()
        
        # Treffer auf 20, nächstes Ziel ist 19
        self.micky_logic._handle_throw(player, "Triple", 20, [])
        self.assertEqual(player.hits["20"], 3)
        self.assertEqual(player.next_target, "19")

        # Aktion: Rückgängig machen
        self.micky_logic._handle_throw_undo(player, "Triple", 20, [])

        # Überprüfung
        self.assertEqual(player.hits["20"], 0)
        self.assertEqual(player.next_target, "20")