import unittest
from unittest.mock import patch, MagicMock, ANY

from .test_base import GameLogicTestBase
# Klasse, die getestet wird
from core.killer import Killer
# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player
from core.scoreboard import ScoreBoard

class TestKiller(GameLogicTestBase):
    """Testet die Spiellogik der Killer-Klasse."""

    def setUp(self):
        """Setzt eine kontrollierte Testumgebung für jeden Test auf."""
        self.logic_class_module = 'killer'
        super().setUp()
        self.mock_game.name = "Killer"
        self.mock_game.lifes = 3
        self.mock_game.next_player = MagicMock() # Wichtig, da es direkt aufgerufen wird

        self.killer_logic = Killer(self.mock_game)

    def _create_players(self, num_players=2):
        """Hilfsfunktion, um eine Liste von Spielern für Tests zu erstellen."""
        players = []
        for i in range(num_players):
            # Player benötigt game.targets, auch wenn es für Killer leer ist
            self.mock_game.targets = []
            player = Player(name=f"Player {i+1}", game=self.mock_game)
            self.killer_logic.initialize_player_state(player)
            player.sb = MagicMock(spec=ScoreBoard)
            players.append(player)
        # Wichtig: Die Killer-Logik muss die Spielerliste kennen
        self.killer_logic.set_players(players)
        return players

    def test_initialization(self):
        """Testet, ob ein Spieler korrekt für Killer initialisiert wird."""
        player = self._create_players(1)[0]
        self.assertEqual(player.score, self.mock_game.lifes)
        self.assertIsNone(player.state['life_segment'])
        self.assertFalse(player.state['can_kill'])

    def test_set_life_segment_success(self):
        """Testet das erfolgreiche Festlegen eines Lebensfeldes."""
        players = self._create_players(2)
        player1 = players[0]

        self.killer_logic._handle_throw(player1, "Single", 15, players)

        self.assertEqual(player1.state['life_segment'], "15")
        self.mock_game.next_player.assert_called_once() # Spiel sollte sofort zum nächsten Spieler wechseln

    def test_set_life_segment_fails_on_taken_segment(self):
        """Testet, dass das Festlegen eines bereits vergebenen Feldes fehlschlägt."""
        players = self._create_players(2)
        player1, player2 = players
        player2.state['life_segment'] = "15" # Segment 15 ist bereits vergeben

        self.killer_logic._handle_throw(player1, "Single", 15, players)

        self.assertIsNone(player1.state['life_segment'])
        self.mock_messagebox.showwarning.assert_called_once()
        self.mock_game.next_player.assert_not_called()

    def test_become_killer_success(self):
        """Testet, ob ein Spieler durch Treffen seines Doubles zum Killer wird."""
        player = self._create_players(1)[0]
        player.state['life_segment'] = "20"

        self.killer_logic._handle_throw(player, "Double", 20, [])

        self.assertTrue(player.state['can_kill'])
        self.mock_messagebox.showinfo.assert_called_with("Killer Status!", f"{player.name} ist jetzt ein KILLER!", parent=ANY)

    def test_killer_takes_opponent_life(self):
        """Testet, ob ein Killer einem Gegner ein Leben nehmen kann."""
        players = self._create_players(2)
        killer, victim = players
        killer.state['life_segment'] = "20"
        killer.state['can_kill'] = True
        victim.state['life_segment'] = "19"
        victim_initial_lives = victim.score

        self.killer_logic._handle_throw(killer, "Double", 19, players)

        self.assertEqual(victim.score, victim_initial_lives - 1)
        victim.sb.set_score_value.assert_called_with(victim_initial_lives - 1)

    def test_killer_takes_own_life(self):
        """Testet, ob ein Killer sich selbst ein Leben nimmt, wenn er sein eigenes Feld trifft."""
        player = self._create_players(1)[0]
        player.state['life_segment'] = "20"
        player.state['can_kill'] = True
        initial_lives = player.score

        self.killer_logic._handle_throw(player, "Double", 20, [])

        self.assertEqual(player.score, initial_lives - 1)
        player.sb.set_score_value.assert_called_with(initial_lives - 1)

    def test_win_condition_last_player_standing(self):
        """Testet die Gewinnbedingung, wenn nur noch ein Spieler übrig ist."""
        players = self._create_players(2)
        killer, victim = players
        killer.state['life_segment'] = "20" # Ein Killer muss ein Lebensfeld haben
        killer.state['can_kill'] = True
        victim.state['life_segment'] = "19"
        victim.score = 1 # Opfer hat nur noch ein Leben

        result = self.killer_logic._handle_throw(killer, "Double", 19, players)

        self.assertEqual(victim.score, 0)
        self.assertTrue(self.mock_game.end)
        self.assertIn("gewinnt Killer", result)

    def test_undo_take_life_restores_victim_life(self):
        """Testet, ob das Rückgängigmachen einer 'take_life'-Aktion das Leben wiederherstellt."""
        players = self._create_players(2)
        killer, victim = players
        killer.state['life_segment'] = "20" # Ein Killer muss ein Lebensfeld haben
        killer.state['can_kill'] = True
        victim.state['life_segment'] = "19"

        # Aktion: Leben nehmen
        self.killer_logic._handle_throw(killer, "Double", 19, players)
        self.assertEqual(victim.score, self.mock_game.lifes - 1, "Das Leben des Opfers sollte reduziert sein.")

        # Aktion: Rückgängig machen
        self.killer_logic._handle_throw_undo(killer, "Double", 19, players)

        self.assertEqual(victim.score, self.mock_game.lifes, "Das Leben des Opfers sollte wiederhergestellt sein.")