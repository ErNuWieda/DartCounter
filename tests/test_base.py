import unittest
from unittest.mock import patch, MagicMock

from core.game import Game
from core.player import Player
from core.scoreboard import ScoreBoard

class GameLogicTestBase(unittest.TestCase):
    """
    Eine gemeinsame Basisklasse für alle Tests von Spiellogik-Klassen.
    Sie enthält wiederverwendbare setUp-Logik und Hilfsmethoden.
    """
    logic_class = None
    logic_class_module = ""

    def setUp(self):
        """Setzt eine kontrollierte, gemeinsame Testumgebung auf."""
        self.mock_game = MagicMock(spec=Game)
        self.mock_game.round = 1
        self.mock_game.end = False
        self.mock_game.db = MagicMock()
        self.mock_game.db.root = MagicMock()
        self.mock_game.highscore_manager = MagicMock()
        self.mock_game.sound_manager = MagicMock()
        self.mock_game.get_score.side_effect = self._get_score_side_effect
        self.mock_game.targets = [] # Standard-Fallback

        # Patch für messagebox, wird von allen Logik-Tests benötigt
        # Die Unterklasse muss 'self.logic_class_module' definieren.
        patcher = patch(f'core.{self.logic_class_module}.messagebox')
        self.mock_messagebox = patcher.start()
        self.addCleanup(patcher.stop)

    def _get_score_side_effect(self, ring, segment):
        """Simuliert die get_score Methode der Game-Klasse für die Tests."""
        segment = int(segment)
        if ring == "Triple": return segment * 3
        if ring == "Double": return segment * 2
        if ring == "Single": return segment
        if ring == "Bullseye": return 50
        if ring == "Bull": return 25
        return 0