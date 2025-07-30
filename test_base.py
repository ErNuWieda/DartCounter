import unittest
from unittest.mock import MagicMock
import tkinter as tk

class GameLogicTestBase(unittest.TestCase):
    """
    Basisklasse für alle Spiellogik-Tests.

    Diese Klasse stellt gemeinsame Funktionalitäten und Mocks bereit,
    die von allen Spiellogik-Testklassen verwendet werden können.
    """

    def setUp(self):
        """
        Setzt eine kontrollierte Testumgebung für jeden Test auf.
        """
        # Mock für die Haupt-Spielinstanz
        self.mock_game = MagicMock()
        self.mock_game.end = False
        self.mock_game.round = 1
        self.mock_game.db.root = tk.Tk() # Benötigt für Dialoge
        self.mock_game.db.root.withdraw() # Verhindert, dass ein leeres Fenster angezeigt wird

        # Mock für die messagebox
        self.mock_messagebox = MagicMock()

        # Patche tkinter.messagebox, sodass wir es mocken können
        self.messagebox_patcher = unittest.mock.patch(f'core.{self.logic_class_module}.messagebox', new=self.mock_messagebox)
        self.messagebox_patcher.start()

    def tearDown(self):
        """
        Räumt nach jedem Test auf.
        """
        # Stoppe den Patcher
        self.messagebox_patcher.stop()

        if self.mock_game.db.root:
            try:
                self.mock_game.db.root.destroy()
            except tk.TclError:
                # Kann passieren, wenn die Root bereits zerstört wurde.
                pass

    def assertPlayersAreEqual(self, player1, player2):
        """Hilfsmethode zum Vergleichen von zwei Spielerobjekten."""
        self.assertEqual(player1.name, player2.name)
        self.assertEqual(player1.score, player2.score)