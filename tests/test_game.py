import unittest
from unittest.mock import patch, MagicMock

# Import the class to be tested
from core.game import Game
# Import classes that are dependencies and will be mocked
from core.player import Player
from core.x01 import X01


class TestGame(unittest.TestCase):
    """Testet die Kernlogik der Game-Klasse, insbesondere Spieler- und Rundenwechsel."""

    def setUp(self):
        """
        Setzt eine kontrollierte Testumgebung für jeden Test auf.
        - Mockt UI-Komponenten (messagebox, ScoreBoard, DartBoard).
        - Mockt die spezifische Spiellogik (z.B. X01).
        - Erstellt eine Game-Instanz mit gemockten Spielern.
        """
        # Patch, um UI-Elemente und externe Abhängigkeiten zu neutralisieren
        patcher_messagebox = patch('core.game.messagebox')
        patcher_scoreboard = patch('core.game.ScoreBoard') # Wird in Game.setup_scoreboards verwendet
        patcher_dartboard = patch('core.game.DartBoard') # Wird jetzt in Game.__init__ verwendet

        # Erstelle einen Mock für die X01-Klasse. Dieser wird in die Map injiziert.
        self.mock_x01_class = MagicMock()

        # Patche das Dictionary, das von der Factory-Methode verwendet wird, nicht die Klasse selbst.
        # Dies stellt sicher, dass get_game_logic bei der Suche nach "301" unseren Mock erhält.
        patcher_logic_map = patch.dict('core.game.GAME_LOGIC_MAP', {'301': self.mock_x01_class})

        self.mock_messagebox = patcher_messagebox.start()
        self.mock_scoreboard_class = patcher_scoreboard.start()
        self.mock_dartboard = patcher_dartboard.start()
        patcher_logic_map.start()

        # Sicherstellen, dass die Mocks nach jedem Test gestoppt werden
        self.addCleanup(patcher_messagebox.stop)
        self.addCleanup(patcher_scoreboard.stop)
        self.addCleanup(patcher_dartboard.stop)
        self.addCleanup(patcher_logic_map.stop)

        # Konfiguration für das Spiel
        self.game_options = {
            'name': '301', 'opt_in': 'Single', 'opt_out': 'Single',
            'opt_atc': 'Single', 'count_to': 301, 'lifes': 3, 'rounds': 7
        }
        self.player_names = ["Alice", "Bob"]

        # Erstelle Mock-Spieler-Instanzen manuell, um ihr Verhalten zu kontrollieren
        self.mock_players = []
        for i, name in enumerate(self.player_names):
            player = MagicMock(spec=Player)
            player.name = name
            player.id = i + 1
            player.throws = []
            player.reset_turn = MagicMock()
            self.mock_players.append(player)

        # Patch die Player-Klasse, damit sie unsere Mock-Spieler zurückgibt
        self.patcher_player = patch('core.game.Player', side_effect=self.mock_players)
        self.mock_player_class = self.patcher_player.start()
        self.addCleanup(self.patcher_player.stop)

        # Initialisiere die Game-Klasse
        self.game = Game(
            root=MagicMock(),
            game_options=self.game_options,
            player_names=self.player_names,
            sound_manager=MagicMock(),
            highscore_manager=MagicMock(),
            player_stats_manager=MagicMock()
        )
        # Weisen die erstellten Mock-Spieler der Instanz zu (da der Patcher sie erstellt hat)
        self.game.players = self.mock_players
        # Mock die Methode, die UI-Interaktionen auslöst
        self.game.announce_current_player_turn = MagicMock()


    def test_initialization(self):
        """Testet, ob das Spiel korrekt initialisiert wird."""
        self.assertEqual(len(self.game.players), 2)
        self.assertEqual(self.game.players[0].name, "Alice")
        self.assertEqual(self.game.current, 0, "Das Spiel sollte mit dem ersten Spieler (Index 0) beginnen.")
        self.assertEqual(self.game.round, 1, "Das Spiel sollte in Runde 1 beginnen.")
        self.assertFalse(self.game.end)
        # Prüfen, ob die Spiellogik-Klasse (X01) instanziiert wurde
        self.mock_x01_class.assert_called_once_with(self.game)
        # Prüfen, ob die UI-Komponenten (Dartboard, Scoreboards) im Konstruktor erstellt wurden
        self.mock_dartboard.assert_called_once_with(self.game)
        self.mock_scoreboard_class.assert_called()


    def test_current_player_returns_correct_player(self):
        """Testet, ob current_player() den richtigen Spieler zurückgibt."""
        self.game.current = 0
        self.assertEqual(self.game.current_player(), self.mock_players[0])

        self.game.current = 1
        self.assertEqual(self.game.current_player(), self.mock_players[1])


    def test_next_player_advances_turn(self):
        """Testet den einfachen Wechsel zum nächsten Spieler innerhalb einer Runde."""
        player1 = self.game.current_player()
        
        self.game.next_player()

        self.assertEqual(self.game.current, 1, "Der Index des aktuellen Spielers sollte auf 1 erhöht werden.")
        self.assertEqual(self.game.round, 1, "Die Runde sollte gleich bleiben.")
        player1.reset_turn.assert_called_once()
        self.game.announce_current_player_turn.assert_called_once()


    def test_next_player_increments_round(self):
        """Testet, ob die Runde erhöht wird, wenn der letzte Spieler seinen Zug beendet."""
        self.game.current = len(self.game.players) - 1 # Setze auf den letzten Spieler (Bob)
        last_player = self.game.current_player()

        self.game.next_player()

        self.assertEqual(self.game.current, 0, "Der Index sollte nach dem letzten Spieler auf 0 zurückgesetzt werden.")
        self.assertEqual(self.game.round, 2, "Die Runde sollte auf 2 erhöht werden.")
        last_player.reset_turn.assert_called_once()
        self.game.announce_current_player_turn.assert_called_once()


    def test_leave_game_current_player_advances_turn(self):
        """Testet, was passiert, wenn der aktuelle Spieler das Spiel verlässt."""
        player_to_leave = self.game.players[0]
        
        self.game.leave(player_to_leave.id)

        self.assertEqual(len(self.game.players), 1, "Die Spielerliste sollte einen Spieler weniger haben.")
        self.assertNotIn(player_to_leave, self.game.players)
        self.assertEqual(self.game.current, 0, "Der 'current' Zeiger sollte auf den neuen Spieler an Index 0 zeigen.")
        self.assertEqual(self.game.players[0].name, "Bob")
        self.game.announce_current_player_turn.assert_called_once()


    def test_leave_game_non_current_player_adjusts_index(self):
        """Testet das Verlassen eines Spielers, der nicht am Zug ist."""
        self.game.current = 1 # Bob ist am Zug
        player_to_leave = self.game.players[0] # Alice verlässt das Spiel

        self.game.leave(player_to_leave.id)

        self.assertEqual(len(self.game.players), 1)
        self.assertNotIn(player_to_leave, self.game.players)
        self.assertEqual(self.game.current, 0, "Der 'current' Zeiger sollte auf 0 dekrementiert werden, da ein Spieler davor entfernt wurde.")
        self.game.announce_current_player_turn.assert_not_called()


    def test_leave_game_last_player_ends_game(self):
        """Testet, ob das Spiel endet, wenn der letzte Spieler geht."""
        # Reduziere die Spielerliste auf einen
        self.game.players = [self.mock_players[0]]
        self.game.current = 0
        player_to_leave = self.game.players[0]
        # Mock die destroy-Methode, um ihren Aufruf zu prüfen
        self.game.destroy = MagicMock()

        self.game.leave(player_to_leave.id)

        self.assertEqual(len(self.game.players), 0)
        self.assertTrue(self.game.end, "Die 'end'-Flagge sollte auf True gesetzt werden.")
        self.mock_messagebox.showinfo.assert_called_once()
        self.game.destroy.assert_called_once()