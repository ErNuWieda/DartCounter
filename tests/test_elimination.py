import unittest
from unittest.mock import patch, MagicMock

from .test_base import GameLogicTestBase
# Klasse, die getestet wird
from core.elimination import Elimination
# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player
from core.scoreboard import ScoreBoard

class TestElimination(GameLogicTestBase):
    """Testet die Spiellogik der Elimination-Klasse."""

    def setUp(self):
        """Setzt eine kontrollierte Testumgebung für jeden Test auf."""
        self.logic_class_module = 'elimination'
        super().setUp()

        self.mock_game.name = "Elimination"
        self.mock_game.count_to = 301
        self.mock_game.opt_out = "Single" # Standard

        self.elimination_logic = Elimination(self.mock_game)

    def _create_players(self, num_players=2):
        """Hilfsfunktion, um eine Liste von Spielern für Tests zu erstellen."""
        players = []
        for i in range(num_players):
            player = Player(name=f"Player {i+1}", game=self.mock_game)
            self.elimination_logic.initialize_player_state(player)
            player.sb = MagicMock(spec=ScoreBoard)
            players.append(player)
        return players

    def test_initialization(self):
        """Testet, ob ein Spieler korrekt für Elimination initialisiert wird."""
        player = self._create_players(1)[0]
        self.assertEqual(player.score, 0)

    def test_valid_throw_increases_score(self):
        """Testet, ob ein gültiger Wurf den Punktestand korrekt erhöht."""
        player = self._create_players(1)[0]
        self.elimination_logic._handle_throw(player, "Triple", 20, [])
        self.assertEqual(player.score, 60)
        self.mock_messagebox.showerror.assert_not_called()

    def test_bust_if_score_exceeds_target(self):
        """Testet, ob ein Bust auftritt, wenn der Score das Ziel überschreitet."""
        player = self._create_players(1)[0]
        player.score = 300
        self.elimination_logic._handle_throw(player, "Single", 2, [])
        self.assertEqual(player.score, 300, "Der Score sollte nach einem Bust unverändert sein.")
        self.mock_messagebox.showerror.assert_called_once()

    def test_elimination_resets_opponent_score(self):
        """Testet, ob ein Spieler einen Gegner eliminieren kann."""
        players = self._create_players(2)
        player1, player2 = players
        player1.score = 40
        player2.score = 100

        # Spieler 1 wirft eine 60 und erreicht 100, was player2 eliminiert.
        self.elimination_logic._handle_throw(player1, "Triple", 20, players)
        
        self.assertEqual(player1.score, 100)
        self.assertEqual(player2.score, 0, "Der Score von Spieler 2 sollte auf 0 zurückgesetzt werden.")
        self.mock_messagebox.showinfo.assert_called_once()

    def test_win_condition(self):
        """Testet, ob das Spiel endet, wenn der Zielscore exakt erreicht wird."""
        player = self._create_players(1)[0]
        player.score = 241
        
        result = self.elimination_logic._handle_throw(player, "Triple", 20, [])
        
        self.assertEqual(player.score, 301)
        self.assertTrue(self.mock_game.end)
        self.assertIn("gewinnt", result)

    def test_undo_simple_throw_restores_score(self):
        """Testet, ob Undo einen einfachen Wurf korrekt zurücknimmt."""
        player = self._create_players(1)[0]
        self.elimination_logic._handle_throw(player, "Single", 20, [])
        self.assertEqual(player.score, 20)

        self.elimination_logic._handle_throw_undo(player, "Single", 20, [])
        self.assertEqual(player.score, 0)

    def test_undo_elimination_restores_victim_score(self):
        """Testet, ob Undo eine Eliminierung korrekt rückgängig macht."""
        players = self._create_players(2)
        player1, player2 = players
        player1.score = 40
        player2.score = 100

        # Spieler 1 eliminiert Spieler 2
        self.elimination_logic._handle_throw(player1, "Triple", 20, players)
        self.assertEqual(player2.score, 0)

        # Aktion: Rückgängig machen
        self.elimination_logic._handle_throw_undo(player1, "Triple", 20, players)

        # Überprüfung
        self.assertEqual(player1.score, 40, "Der Score des Werfers sollte wiederhergestellt sein.")
        self.assertEqual(player2.score, 100, "Der Score des Opfers sollte wiederhergestellt sein.")