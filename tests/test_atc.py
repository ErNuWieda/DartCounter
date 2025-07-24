import unittest
from unittest.mock import patch, MagicMock

from .test_base import GameLogicTestBase
# Klasse, die getestet wird
from core.atc import AtC
# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player
from core.scoreboard import ScoreBoard

class TestAtC(GameLogicTestBase):
    """Testet die Spiellogik der AtC (Around the Clock) Klasse."""

    def setUp(self):
        """Setzt eine kontrollierte Testumgebung für jeden Test auf."""
        self.logic_class_module = 'atc'
        super().setUp()
        self.mock_game.name = "Around the Clock"
        self.mock_game.opt_atc = "Single"  # Standardwert

        # Instanz der zu testenden Klasse
        self.atc_logic = AtC(self.mock_game)
        self.mock_game.targets = self.atc_logic.get_targets()

    def _create_player(self):
        """
        Hilfsfunktion, um eine echte Player-Instanz für ATC-Tests zu erstellen.
        """
        # Erstelle eine echte Player-Instanz mit dem gemockten Spiel
        player = Player(name="Tester", game=self.mock_game)
        # Initialisiere den Spieler-Zustand für ATC
        self.atc_logic.initialize_player_state(player)
        # Mock für das ScoreBoard
        player.sb = MagicMock(spec=ScoreBoard)
        return player

    def test_initialization(self):
        """Testet, ob ein Spieler korrekt für ATC initialisiert wird."""
        player = self._create_player()
        self.assertEqual(player.score, 0)
        self.assertEqual(player.state['next_target'], "1")
        self.assertEqual(player.state['hits'].get("1"), 0)
        self.assertIn("20", player.state['hits']) # Prüfen, ob alle Ziele initialisiert sind

    def test_valid_hit_advances_target(self):
        """Testet, ob ein gültiger Treffer das nächste Ziel korrekt setzt."""
        player = self._create_player()
        self.atc_logic._handle_throw(player, "Single", 1, [])
        self.assertEqual(player.state['hits']["1"], 1, "Ziel 1 sollte als getroffen markiert sein.")
        self.assertEqual(player.state['next_target'], "2", "Das nächste Ziel sollte 2 sein.")
        self.mock_messagebox.showerror.assert_not_called()

    def test_invalid_hit_shows_error(self):
        """Testet, ob ein Wurf auf das falsche Ziel eine Fehlermeldung auslöst."""
        player = self._create_player()
        self.atc_logic._handle_throw(player, "Single", 5, []) # Falsches Ziel
        self.assertEqual(player.state['hits']["1"], 0, "Ziel 1 sollte unberührt bleiben.")
        self.assertEqual(player.state['next_target'], "1", "Das Ziel sollte 1 bleiben.")
        self.mock_messagebox.showerror.assert_called_once()

    def test_valid_hit_with_double_option(self):
        """Testet einen gültigen Treffer, wenn die Option 'Double' aktiv ist."""
        self.mock_game.opt_atc = "Double"
        self.atc_logic = AtC(self.mock_game) # Logik mit neuer Option neu initialisieren
        player = self._create_player()

        self.atc_logic._handle_throw(player, "Double", 1, [])
        self.assertEqual(player.state['hits']["1"], 1)
        self.assertEqual(player.state['next_target'], "2")
        self.mock_messagebox.showerror.assert_not_called()

    def test_win_condition(self):
        """Testet, ob das Spiel endet, wenn alle Ziele getroffen wurden."""
        player = self._create_player()
        
        # Alle Ziele von 1 bis 20 treffen
        for i in range(1, 21):
            self.atc_logic._handle_throw(player, "Single", i, [])
        
        # Den letzten Wurf auf Bull machen
        result = self.atc_logic._handle_throw(player, "Bull", 25, [])

        self.assertTrue(self.mock_game.end, "Das Spiel sollte als beendet markiert sein.")
        self.assertIn("gewinnt", result, "Eine Gewinnnachricht sollte zurückgegeben werden.")

    def test_undo_restores_target(self):
        """Testet, ob die Undo-Funktion den Zustand korrekt wiederherstellt."""
        player = self._create_player()
        self.atc_logic._handle_throw(player, "Single", 1, [])
        self.assertEqual(player.state['next_target'], "2")

        self.atc_logic._handle_throw_undo(player, "Single", 1, [])
        
        self.assertEqual(player.state['next_target'], "1", "Das Ziel sollte auf 1 zurückgesetzt werden.")
        self.assertEqual(player.state['hits']["1"], 0, "Die Treffer auf Ziel 1 sollten zurückgesetzt werden.")