import unittest
from unittest.mock import patch, MagicMock

from .test_base import GameLogicTestBase
# Klasse, die getestet wird
from core.x01 import X01
# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player
from core.scoreboard import ScoreBoard

class TestX01(GameLogicTestBase):
    """Testet die Spiellogik der X01-Klasse, insbesondere Opt-In/Out und Bust-Regeln."""

    def setUp(self):
        """Setzt eine kontrollierte Testumgebung für jeden Test auf."""
        self.logic_class_module = 'x01'
        super().setUp()

        self.mock_game.name = "501"
        self.mock_game.opt_in = "Double"  # Standardwert
        self.mock_game.opt_out = "Double" # Wichtig: Muss VOR der X01-Instanziierung gesetzt werden.

        # Instanz der zu testenden Klasse
        self.x01_logic = X01(self.mock_game)

    def _create_player(self, score, has_opened=True):
        """
        Hilfsfunktion, um eine echte Player-Instanz für Tests zu erstellen.
        Dies ist robuster als ein Mock, da es die interne Logik des Spielers
        (z.B. Properties) korrekt verwendet.
        """
        # Erstelle eine echte Player-Instanz mit dem gemockten Spiel
        player = Player(name="Tester", game=self.mock_game)
        player.score = score
        player.state['has_opened'] = has_opened
        # Mock für das ScoreBoard, das vom Spieler referenziert wird.
        # spec=ScoreBoard stellt sicher, dass der Mock die __del__-Methode hat.
        player.sb = MagicMock(spec=ScoreBoard)
        return player

    # --- Opt-In Tests ---
    def test_opt_in_double_fails_on_single_throw(self):
        """Testet, ob bei 'Double In' ein Single-Wurf ungültig ist."""
        self.mock_game.opt_in = "Double"
        player = self._create_player(score=501, has_opened=False)

        self.x01_logic._handle_throw(player, "Single", 20, [])

        # Der Punktestand wird nicht reduziert, da der Wurf ungültig ist.
        self.assertEqual(player.score, 501, "Der Punktestand darf sich bei einem ungültigen 'In'-Wurf nicht ändern.")
        self.assertFalse(player.state['has_opened'], "Der Spieler darf nach einem ungültigen 'In'-Wurf nicht als 'geöffnet' markiert sein.")
        self.mock_messagebox.showerror.assert_called_once()

    def test_opt_in_double_succeeds_on_double_throw(self):
        """Testet, ob bei 'Double In' ein Double-Wurf gültig ist und das Spiel eröffnet."""
        self.mock_game.opt_in = "Double"
        player = self._create_player(score=501, has_opened=False)

        self.x01_logic._handle_throw(player, "Double", 20, [])

        self.assertEqual(player.score, 461, "Der Punktestand sollte korrekt reduziert werden.")
        self.assertTrue(player.state['has_opened'], "Der Spieler sollte nun als 'geöffnet' markiert sein.")
        self.mock_messagebox.showerror.assert_not_called()

    # --- Bust Tests ---
    def test_bust_if_score_goes_below_zero(self):
        """Testet, ob ein Wurf, der den Score unter 0 bringen würde, ein 'Bust' ist."""
        player = self._create_player(score=20)

        self.x01_logic._handle_throw(player, "Triple", 20, []) # Wurf von 60

        self.assertEqual(player.score, 20, "Der Punktestand sollte nach einem Bust unverändert sein.")
        self.mock_messagebox.showerror.assert_called_once()

    def test_opt_out_double_busts_if_score_is_one(self):
        """Testet, ob bei 'Double Out' ein Rest von 1 ein 'Bust' ist."""
        player = self._create_player(score=21)

        self.x01_logic._handle_throw(player, "Single", 20, []) # Bringt Score auf 1

        self.assertEqual(player.score, 21, "Der Punktestand sollte nach einem Bust unverändert sein.")
        self.mock_messagebox.showerror.assert_called_once()

    def test_opt_out_double_busts_on_single_finish(self):
        """Testet, ob bei 'Double Out' ein Finish mit einem Single-Wurf ein 'Bust' ist."""
        player = self._create_player(score=20)

        self.x01_logic._handle_throw(player, "Single", 20, [])

        self.assertEqual(player.score, 20, "Der Punktestand sollte nach einem Bust unverändert sein.")
        self.mock_messagebox.showerror.assert_called_once()

    # --- Gültiger Wurf & Gewinn Tests ---
    def test_valid_throw_updates_score_and_stats(self):
        """Testet, ob ein gültiger Wurf den Score und die Statistiken korrekt aktualisiert."""
        player = self._create_player(score=100)

        self.x01_logic._handle_throw(player, "Triple", 20, []) # Wurf von 60

        self.assertEqual(player.score, 40)
        self.assertEqual(player.stats['total_darts_thrown'], 1)
        self.assertEqual(player.stats['total_score_thrown'], 60)
        self.mock_messagebox.showerror.assert_not_called()

    def test_win_on_double_out_updates_all_stats(self):
        """Testet, ob ein Gewinnwurf bei 'Double Out' alle relevanten Daten korrekt aktualisiert."""
        player = self._create_player(score=40)

        # Initialzustand der Statistiken
        self.assertEqual(player.stats['checkout_opportunities'], 0)
        self.assertEqual(player.stats['checkouts_successful'], 0)
        self.assertEqual(player.stats['highest_finish'], 0)

        result = self.x01_logic._handle_throw(player, "Double", 20, [])

        # Überprüfen des Endzustands
        self.assertEqual(player.score, 0)
        self.assertTrue(self.mock_game.end)
        # Ein robuster Test prüft auf das korrekte Verhalten, nicht auf ein fehlendes Feature.
        self.assertEqual(player.stats['checkout_opportunities'], 1, "Es gab eine Checkout-Möglichkeit, die gezählt werden sollte.")
        self.assertEqual(player.stats['checkouts_successful'], 1, "Der Checkout war erfolgreich.")
        self.assertEqual(player.stats['highest_finish'], 40, "Das höchste Finish sollte der Anfangsscore sein.")
        self.assertIn("gewinnt", result, "Eine Gewinnnachricht sollte zurückgegeben werden.")

    # --- Undo Tests ---
    def test_undo_simple_throw_restores_state(self):
        """Testet, ob das Rückgängigmachen eines Wurfs Score und Stats korrekt wiederherstellt."""
        player = self._create_player(score=100)
        # Simuliere einen Wurf
        self.x01_logic._handle_throw(player, "Triple", 20, [])
        self.assertEqual(player.score, 40)
        self.assertEqual(player.stats['total_darts_thrown'], 1)
        self.assertEqual(player.stats['total_score_thrown'], 60)

        # Mache den Wurf rückgängig
        self.x01_logic._handle_throw_undo(player, "Triple", 20, [])

        # Prüfe den wiederhergestellten Zustand
        self.assertEqual(player.score, 100, "Der Score sollte wiederhergestellt sein.")
        self.assertEqual(player.stats['total_darts_thrown'], 0, "Die Anzahl der Würfe sollte zurückgesetzt sein.")
        self.assertEqual(player.stats['total_score_thrown'], 0, "Der Gesamtscore sollte zurückgesetzt sein.")

    def test_undo_winning_throw_restores_player_state(self):
        """Testet, ob das Rückgängigmachen eines Gewinnwurfs den Spieler-Zustand wiederherstellt."""
        player = self._create_player(score=40)
        # Simuliere einen Gewinnwurf
        self.x01_logic._handle_throw(player, "Double", 20, [])
        self.assertEqual(player.stats['checkouts_successful'], 1)

        # Mache den Gewinnwurf rückgängig
        self.x01_logic._handle_throw_undo(player, "Double", 20, [])

        self.assertEqual(player.score, 40, "Der Score sollte wiederhergestellt sein.")
        self.assertEqual(player.stats['checkouts_successful'], 0, "Erfolgreiche Checkouts sollten zurückgesetzt sein.")

if __name__ == '__main__':
    unittest.main(verbosity=2)