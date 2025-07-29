import unittest
from unittest.mock import patch, MagicMock

from .test_base import GameLogicTestBase
# Klasse, die getestet wird
from core.shanghai import Shanghai
# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player
from core.scoreboard import ScoreBoard

class TestShanghai(GameLogicTestBase):
    """Testet die Spiellogik der Shanghai-Klasse."""

    def setUp(self):
        """Setzt eine kontrollierte Testumgebung für jeden Test auf."""
        self.logic_class_module = 'shanghai'
        super().setUp()

        self.mock_game.name = "Shanghai"
        self.mock_game.rounds = 7

        self.shanghai_logic = Shanghai(self.mock_game)
        # Wichtig: get_targets() muss aufgerufen werden, damit self.targets in der Logik gesetzt wird
        self.mock_game.targets = self.shanghai_logic.get_targets()

    def _create_players(self, num_players=2):
        """Hilfsfunktion, um eine Liste von Spielern für Tests zu erstellen."""
        players = []
        for i in range(num_players):
            player = Player(name=f"Player {i+1}", game=self.mock_game)
            self.shanghai_logic.initialize_player_state(player)
            player.sb = MagicMock(spec=ScoreBoard)
            players.append(player)
        return players

    def test_initialization(self):
        """Testet, ob ein Spieler korrekt für Shanghai initialisiert wird."""
        player = self._create_players(1)[0]
        self.assertEqual(player.score, 0)
        self.assertEqual(player.next_target, "1")
        self.assertEqual(player.hits.get("1"), 0)
        self.assertIn("7", self.shanghai_logic.get_targets())
        self.assertNotIn("8", self.shanghai_logic.get_targets())

    def test_correct_hit_scores_points(self):
        """Testet, ob ein Treffer auf das korrekte Ziel (der Runde) Punkte gibt."""
        self.mock_game.round = 2 # Wir sind in Runde 2, Ziel ist "2"
        player = self._create_players(1)[0]
        
        self.shanghai_logic._handle_throw(player, "Triple", 2, [])
        
        self.assertEqual(player.score, 6)
        self.assertEqual(player.hits["2"], 1)

    def test_incorrect_hit_scores_no_points(self):
        """Testet, ob ein Treffer auf ein falsches Ziel keine Punkte gibt."""
        self.mock_game.round = 3 # Ziel ist "3"
        player = self._create_players(1)[0]

        self.shanghai_logic._handle_throw(player, "Single", 4, []) # Wurf auf die 4
        
        self.assertEqual(player.score, 0)
        self.assertEqual(player.hits.get("3"), 0)

    def test_shanghai_win_condition(self):
        """Testet, ob ein Shanghai (S, D, T) zum sofortigen Sieg führt."""
        self.mock_game.round = 5 # Ziel ist "5"
        player = self._create_players(1)[0]
        
        # Simuliere die drei Würfe für ein Shanghai
        player.throws = [("Single", 5, None), ("Double", 5, None), ("Triple", 5, None)]
        
        result = self.shanghai_logic._handle_throw(player, "Triple", 5, []) # Der letzte Wurf löst die Prüfung aus
        
        self.assertTrue(self.mock_game.end)
        self.assertIn("Shanghai auf die 5", result)

    def test_end_of_rounds_win_condition(self):
        """Testet, ob nach der letzten Runde der Spieler mit den meisten Punkten gewinnt."""
        self.mock_game.rounds = 2 # Kurzes Spiel mit 2 Runden
        self.mock_game.round = 3 # Simuliert, dass das Spiel in die "Prüfungsphase" nach der letzten Runde geht
        players = self._create_players(2)
        player1, player2 = players
        player1.score = 100
        player2.score = 50
        
        # Der Wurf selbst ist irrelevant, er löst nur die Gewinnprüfung aus
        result = self.shanghai_logic._handle_throw(player2, "Miss", 0, players)
        
        self.assertTrue(self.mock_game.end)
        self.assertIn(f"{player1.name} gewinnt mit 100 Punkten", result)

    def test_undo_restores_state(self):
        """Testet, ob das Rückgängigmachen eines Wurfs Score und Treffer korrekt wiederherstellt."""
        self.mock_game.round = 4 # Ziel ist "4"
        player = self._create_players(1)[0]

        # Aktion: Ein gültiger Wurf
        self.shanghai_logic._handle_throw(player, "Double", 4, [])

        # Überprüfung des Zustands nach dem Wurf
        self.assertEqual(player.score, 8)
        self.assertEqual(player.hits.get("4"), 1)

        # Aktion: Rückgängig machen
        self.shanghai_logic._handle_throw_undo(player, "Double", 4, [])

        # Überprüfung des wiederhergestellten Zustands
        self.assertEqual(player.score, 0, "Der Punktestand sollte zurückgesetzt sein.")
        self.assertEqual(player.hits.get("4"), 0, "Die Treffer sollten ebenfalls zurückgesetzt sein.")