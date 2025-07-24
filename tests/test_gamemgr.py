import unittest
import tkinter as tk
from unittest.mock import patch, MagicMock, Mock, ANY
import sys
import os

# Fügt das Projektverzeichnis zum Python-Pfad hinzu, damit 'core' importiert werden kann
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.gamemgr import GameManager, GameSettingsDialog

class TestGameManager(unittest.TestCase):
    """
    Testet die entkoppelte GameManager-Klasse.
    Die UI-Komponente (GameSettingsDialog) wird gemockt, um den GameManager
    isoliert von der GUI zu testen.
    """
    def setUp(self):
        """Setzt eine saubere Testumgebung für jeden Test auf."""
        self.root = tk.Tk()
        self.root.withdraw()

        self.mock_settings_manager = MagicMock()
        self.mock_sound_manager = Mock()
        self.gm = GameManager(self.mock_sound_manager, self.mock_settings_manager)

    def tearDown(self):
        """Räumt nach jedem Test auf."""
        if self.root:
            self.root.destroy()

    @patch.object(tk.Tk, 'wait_window')
    @patch('core.gamemgr.GameSettingsDialog', spec=GameSettingsDialog)
    def test_configure_game_when_started(self, mock_dialog_class, mock_wait_window):
        """
        Testet, ob configure_game die Einstellungen vom Dialog übernimmt,
        wenn der Benutzer das Spiel startet.
        """
        # 1. Konfiguriere den Mock für die Dialog-Instanz, die erstellt wird
        mock_dialog_instance = mock_dialog_class.return_value
        mock_dialog_instance.was_started = True
        mock_dialog_instance.game = "501"
        mock_dialog_instance.players = ["Alice", "Bob"]
        mock_dialog_instance.opt_out = "Double"
        # Vervollständige den Mock mit allen Attributen, die GameManager erwartet
        mock_dialog_instance.count_to = "501"
        mock_dialog_instance.opt_in = "Single"
        mock_dialog_instance.opt_atc = "Single"
        mock_dialog_instance.lifes = "5"
        mock_dialog_instance.shanghai_rounds = "10"

        # 2. Rufe die zu testende Methode auf
        result = self.gm.configure_game(self.root)

        # 3. Überprüfe die Ergebnisse
        self.assertTrue(result)
        # Überprüfe, ob der Dialog korrekt instanziiert wurde
        mock_dialog_class.assert_called_once_with(self.root, self.mock_settings_manager)
        # Überprüfe, ob die Einstellungen vom Dialog auf den GameManager übertragen wurden
        self.assertEqual(self.gm.game, "501")
        self.assertEqual(self.gm.players, ["Alice", "Bob"])
        self.assertEqual(self.gm.opt_out, "Double")
        self.assertEqual(self.gm.count_to, "501")
        self.assertEqual(self.gm.opt_in, "Single")
        self.assertEqual(self.gm.lifes, "5")
        self.assertEqual(self.gm.shanghai_rounds, "10")
        # Überprüfe, ob auf den Dialog gewartet wurde
        mock_wait_window.assert_called_once_with(mock_dialog_class.return_value)

    @patch.object(tk.Tk, 'wait_window')
    @patch('core.gamemgr.GameSettingsDialog', spec=GameSettingsDialog)
    def test_configure_game_when_cancelled(self, mock_dialog_class, mock_wait_window):
        """
        Testet, ob configure_game die Standardeinstellungen beibehält,
        wenn der Benutzer den Dialog abbricht.
        """
        # 1. Konfiguriere den Mock für die Dialog-Instanz
        mock_dialog_instance = mock_dialog_class.return_value
        mock_dialog_instance.was_started = False

        # 2. Rufe die zu testende Methode auf
        result = self.gm.configure_game(self.root)

        # 3. Überprüfe die Ergebnisse
        self.assertFalse(result)
        # Überprüfe, ob die Standardwerte des GameManagers unverändert sind
        self.assertEqual(self.gm.game, "301")
        self.assertEqual(self.gm.players, [])
        # Überprüfe, ob auf den Dialog gewartet wurde
        mock_wait_window.assert_called_once_with(mock_dialog_class.return_value)

if __name__ == '__main__':
    unittest.main()