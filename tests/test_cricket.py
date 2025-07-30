import unittest
from unittest.mock import patch, MagicMock

from .test_base import GameLogicTestBase
# Klasse, die getestet wird
from core.cricket import Cricket
# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player
from core.scoreboard import ScoreBoard

class TestCricket(GameLogicTestBase):
    """Testet die Spiellogik der Cricket-Klasse."""

    def setUp(self):
        """Setzt eine kontrollierte Testumgebung für jeden Test auf."""
        self.logic_class_module = 'cricket'
        super().setUp()

        self.mock_game.name = "Cricket"

        # Instanz der zu testenden Klasse
        self.cricket_logic = Cricket(self.mock_game)
        
        # Player.__init__ greift auf game.targets zu, also muss es im Mock existieren.
        self.mock_game.targets = self.cricket_logic.get_targets()

    def _create_players(self, num_players=2):
        """Hilfsfunktion, um eine Liste von Spielern für Tests zu erstellen."""
        players = []
        for i in range(num_players):
            player = Player(name=f"Player {i+1}", game=self.mock_game)
            self.cricket_logic.initialize_player_state(player)
            player.sb = MagicMock(spec=ScoreBoard)
            players.append(player)
        return players

    def test_initialization(self):
        """Testet, ob ein Spieler korrekt für Cricket initialisiert wird."""
        player = self._create_players(1)[0]
        self.assertEqual(player.score, 0)
        self.assertEqual(player.state['hits'].get("20"), 0)
        self.assertIn("15", player.state['hits'])
        self.assertNotIn("14", player.state['hits'], "14 sollte kein Ziel im Standard-Cricket sein.")

    def test_valid_hit_adds_marks(self):
        """Testet, ob ein gültiger Treffer die Trefferzahl korrekt erhöht."""
        player = self._create_players(1)[0]
        
        # Ein Single-Treffer
        self.cricket_logic._handle_throw(player, "Single", 20, [])
        self.assertEqual(player.state['hits']["20"], 1)

        # Ein Double-Treffer auf dasselbe Ziel
        self.cricket_logic._handle_throw(player, "Double", 20, [])
        self.assertEqual(player.state['hits']["20"], 3, "Ein Single und ein Double sollten das Ziel schließen.")

    def test_hit_on_closed_target_scores_points(self):
        """Testet, ob ein Treffer auf ein geschlossenes Ziel Punkte gibt."""
        players = self._create_players(2)
        player1, player2 = players

        # Spieler 1 schließt die 20
        player1.state['hits']["20"] = 3
        
        # Spieler 1 wirft erneut auf die 20
        self.cricket_logic._handle_throw(player1, "Single", 20, players)

        self.assertEqual(player1.score, 20, "Spieler 1 sollte 20 Punkte erhalten haben.")
        self.assertEqual(player2.score, 0)

    def test_no_points_if_all_opponents_closed_target(self):
        """Testet, dass keine Punkte vergeben werden, wenn alle Gegner das Ziel ebenfalls geschlossen haben."""
        players = self._create_players(2)
        player1, player2 = players

        # Beide Spieler schließen die 20
        player1.state['hits']["20"] = 3
        player2.state['hits']["20"] = 3

        # Spieler 1 wirft erneut auf die 20
        self.cricket_logic._handle_throw(player1, "Single", 20, players)

        self.assertEqual(player1.score, 0, "Es sollten keine Punkte vergeben werden, da das Ziel 'tot' ist.")

    def test_bullseye_counts_as_two_marks(self):
        """Testet, dass ein Bullseye als zwei Treffer auf 'Bull' zählt."""
        player = self._create_players(1)[0]
        self.assertEqual(player.state['hits']["Bull"], 0)
        self.cricket_logic._handle_throw(player, "Bullseye", 50, [])
        self.assertEqual(player.state['hits']["Bull"], 2)

    def test_win_condition_all_targets_closed_and_highest_score(self):
        """Testet die Gewinnbedingung: Alle Ziele geschlossen und höchste Punktzahl."""
        players = self._create_players(2)
        player1, player2 = players

        # Simuliere, dass Spieler 1 alle Ziele geschlossen hat und mehr Punkte hat
        for target in self.cricket_logic.get_targets():
            player1.state['hits'][target] = 3
        player1.score = 100
        player2.score = 50

        # Ein Wurf auf ein gültiges, bereits geschlossenes Ziel, um die Gewinnprüfung auszulösen.
        # Der vorherige Fehler war ein Wurf auf ein ungültiges Ziel (z.B. "1").
        result = self.cricket_logic._handle_throw(player1, "Single", 20, players)

        self.assertTrue(self.mock_game.end, "Das Spiel sollte als beendet markiert sein.")
        self.assertIn("gewinnt", result, "Eine Gewinnnachricht sollte zurückgegeben werden.")

    def test_no_win_if_score_is_lower(self):
        """Testet, dass das Spiel nicht endet, wenn alle Ziele geschlossen sind, aber der Score niedriger ist."""
        players = self._create_players(2)
        player1, player2 = players

        # Spieler 1 schließt alle Ziele, hat aber weniger Punkte
        for target in self.cricket_logic.get_targets():
            player1.state['hits'][target] = 3
        player1.score = 50
        player2.score = 100

        result = self.cricket_logic._handle_throw(player1, "Single", 20, players)

        self.assertFalse(self.mock_game.end, "Das Spiel sollte nicht beendet sein, da der Score niedriger ist.")
        self.assertIsNone(result)

    def test_win_on_equal_score(self):
        """
        Testet, dass ein Spieler gewinnt, wenn er alle Ziele schließt und
        den Punktestand eines Gegners egalisiert (und niemand mehr Punkte hat).
        """
        players = self._create_players(2)
        player1, player2 = players

        # Setup: Spieler 1 hat 100 Punkte, aber nicht alle Ziele geschlossen.
        player1.score = 100
        
        # Spieler 2 schließt alle Ziele und erreicht damit 100 Punkte.
        for target in self.cricket_logic.get_targets():
            player2.state['hits'][target] = 3
        player2.score = 80

        # Aktion: Spieler 2 wirft eine S20, um den Score auf 100 zu erhöhen.
        result = self.cricket_logic._handle_throw(player2, "Single", 20, players)

        # Überprüfung:
        self.assertTrue(self.mock_game.end, "Das Spiel sollte beendet sein, da Spieler 2 gewonnen hat.")
        self.assertIn("gewinnt", result, "Eine Gewinnnachricht sollte zurückgegeben werden.")

    # --- Cut Throat Specific Tests ---

    def test_cut_throat_scoring_adds_points_to_opponents(self):
        """Testet, ob bei 'Cut Throat' Punkte den Gegnern hinzugefügt werden."""
        self.mock_game.name = "Cut Throat"
        self.cricket_logic = Cricket(self.mock_game) # Re-initialize with new game name
        players = self._create_players(3)
        player1, player2, player3 = players

        # Setup:
        # Player 1 hat die 20 geschlossen.
        player1.state['hits']["20"] = 3
        # Player 2 hat die 20 offen.
        player2.state['hits']["20"] = 1
        # Player 3 hat die 20 ebenfalls geschlossen.
        player3.state['hits']["20"] = 3

        # Aktion: Spieler 1 trifft die 20 erneut.
        self.cricket_logic._handle_throw(player1, "Single", 20, players)

        # Überprüfung:
        self.assertEqual(player1.score, 0, "Der werfende Spieler sollte keine Punkte erhalten.")
        self.assertEqual(player2.score, 20, "Der Gegner mit offenem Ziel sollte Strafpunkte erhalten.")
        self.assertEqual(player3.score, 0, "Der Gegner mit geschlossenem Ziel sollte keine Punkte erhalten.")

    def test_cut_throat_win_condition_lowest_score(self):
        """Testet die Gewinnbedingung für Cut Throat (alle Ziele zu, niedrigster Score)."""
        self.mock_game.name = "Cut Throat"
        self.cricket_logic = Cricket(self.mock_game)
        players = self._create_players(2)
        player1, player2 = players

        # Setup: Spieler 1 schließt alle Ziele und hat den niedrigeren Score.
        for target in self.cricket_logic.get_targets():
            player1.state['hits'][target] = 3
        player1.score = 50
        player2.score = 100

        # Aktion: Ein Wurf auf ein gültiges Ziel, um die Gewinnprüfung auszulösen.
        result = self.cricket_logic._handle_throw(player1, "Single", 20, players)

        # Überprüfung:
        self.assertTrue(self.mock_game.end, "Das Spiel sollte als beendet markiert sein.")
        self.assertIn("gewinnt", result, "Eine Gewinnnachricht sollte zurückgegeben werden.")

    def test_cut_throat_win_on_equal_score(self):
        """Testet, dass bei Cut Throat ein Sieg erfolgt, wenn der Score gleich dem des Gegners ist."""
        self.mock_game.name = "Cut Throat"
        self.cricket_logic = Cricket(self.mock_game)
        players = self._create_players(2)
        player1, player2 = players

        # Setup: Spieler 1 schließt alle Ziele und hat den gleichen (niedrigen) Score wie Spieler 2.
        for target in self.cricket_logic.get_targets():
            player1.state['hits'][target] = 3
        player1.score = 50
        player2.score = 50

        # Aktion: Der letzte Wurf, der das Spiel beendet.
        result = self.cricket_logic._handle_throw(player1, "Single", 20, players)

        # Überprüfung:
        self.assertTrue(self.mock_game.end, "Das Spiel sollte bei Punktegleichstand als gewonnen gelten.")
        self.assertIn("gewinnt", result, "Eine Gewinnnachricht sollte zurückgegeben werden.")

    def test_cut_throat_no_win_if_score_is_higher(self):
        """Testet, dass bei Cut Throat kein Sieg erfolgt, wenn der Score höher ist."""
        self.mock_game.name = "Cut Throat"
        self.cricket_logic = Cricket(self.mock_game)
        players = self._create_players(2)
        player1, player2 = players

        # Setup: Spieler 1 schließt alle Ziele, hat aber den höheren Score.
        for target in self.cricket_logic.get_targets():
            player1.state['hits'][target] = 3
        player1.score = 100
        player2.score = 50

        # Aktion: Der Wurf, der die Ziele schließt, aber nicht das Spiel beendet.
        result = self.cricket_logic._handle_throw(player1, "Single", 20, players)

        # Überprüfung:
        self.assertFalse(self.mock_game.end, "Das Spiel sollte nicht beendet sein, da der Score höher ist.")
        self.assertIsNone(result)

    # --- Undo Tests ---

    def test_undo_simple_hit_restores_marks(self):
        """Testet, ob das Rückgängigmachen eines einfachen Treffers die Marks korrekt wiederherstellt."""
        player = self._create_players(1)[0]

        # Aktion: Ein Treffer
        self.cricket_logic._handle_throw(player, "Double", 20, [])
        self.assertEqual(player.state['hits']["20"], 2)

        # Aktion: Rückgängig machen
        self.cricket_logic._handle_throw_undo(player, "Double", 20, [])

        # Überprüfung:
        self.assertEqual(player.state['hits']["20"], 0, "Die Treffer auf Ziel 20 sollten zurückgesetzt sein.")

    def test_undo_scoring_hit_restores_score_and_marks(self):
        """Testet, ob das Rückgängigmachen eines punktenden Wurfs Score und Marks wiederherstellt."""
        players = self._create_players(2)
        player1, player2 = players

        # Setup: Spieler 1 schließt die 20 und wirft dann einen punktenden Dart.
        player1.state['hits']["20"] = 3
        self.cricket_logic._handle_throw(player1, "Single", 20, players)
        self.assertEqual(player1.score, 20)
        self.assertEqual(player1.state['hits']["20"], 4)

        # Aktion: Rückgängig machen
        self.cricket_logic._handle_throw_undo(player1, "Single", 20, players)

        # Überprüfung:
        self.assertEqual(player1.score, 0, "Der Punktestand sollte auf 0 zurückgesetzt sein.")
        self.assertEqual(player1.state['hits']["20"], 3, "Die Treffer sollten auf 3 zurückgesetzt sein.")

    def test_undo_cut_throat_scoring_hit_restores_opponent_score(self):
        """Testet, ob Undo bei Cut Throat die Strafpunkte des Gegners korrekt entfernt."""
        self.mock_game.name = "Cut Throat"
        self.cricket_logic = Cricket(self.mock_game)
        players = self._create_players(2)
        player1, player2 = players

        # Setup: Spieler 1 schließt die 19 und gibt Spieler 2 Strafpunkte.
        player1.state['hits']["19"] = 3
        self.cricket_logic._handle_throw(player1, "Double", 19, players)
        self.assertEqual(player2.score, 38)

        # Aktion: Rückgängig machen
        self.cricket_logic._handle_throw_undo(player1, "Double", 19, players)

        # Überprüfung:
        self.assertEqual(player2.score, 0, "Die Strafpunkte von Spieler 2 sollten entfernt worden sein.")
        self.assertEqual(player1.state['hits']["19"], 3, "Die Treffer von Spieler 1 sollten auf 3 zurückgesetzt sein.")