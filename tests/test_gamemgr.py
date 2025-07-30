import unittest
from unittest.mock import patch, MagicMock, ANY

from core.gamemgr import GameManager, GameSettingsDialog

# Mock tkinter to prevent system hangs
mock_tk = MagicMock()

@patch.dict('sys.modules', {
    'tkinter': mock_tk,
    'tkinter.ttk': mock_tk.ttk,
    'tkinter.messagebox': mock_tk.messagebox,
    'tkinter.filedialog': mock_tk.filedialog
})
class TestGameManager(unittest.TestCase):
    """
    Testet die entkoppelte GameManager-Klasse.
    Die UI-Komponente (GameSettingsDialog) wird gemockt, um den GameManager
    isoliert von der GUI zu testen.
    """

    def setUp(self):
        """Setzt eine saubere Testumgebung für jeden Test auf."""
        self.mock_settings_manager = MagicMock()
        self.mock_sound_manager = MagicMock()
        self.mock_profile_manager = MagicMock()
        self.gm = GameManager(self.mock_sound_manager, self.mock_settings_manager, self.mock_profile_manager)

    @patch('core.gamemgr.GameSettingsDialog', spec=GameSettingsDialog)
    def test_configure_game_when_started(self, mock_dialog_class):
        """
        Testet, ob configure_game die Einstellungen vom Dialog übernimmt,
        wenn der Benutzer das Spiel startet.
        """
        mock_root = MagicMock()
        # 1. Konfiguriere den Mock für die Dialog-Instanz, die erstellt wird
        mock_dialog_instance = mock_dialog_class.return_value
        mock_dialog_instance.was_started = True 
        # Der Dialog gibt jetzt ein Dictionary zurück
        mock_dialog_instance.result = {
            "game": "501",
            "players": ["Alice", "Bob"],
            "opt_out": "Double",
            "count_to": "501",
            "opt_in": "Single",
            "opt_atc": "Single",
            "lifes": "5",
            "rounds": "10",
        }

        # 2. Rufe die zu testende Methode auf
        result = self.gm.configure_game(mock_root)

        # 3. Überprüfe die Ergebnisse
        self.assertTrue(result)
        # Überprüfe, ob der Dialog korrekt instanziiert wurde
        mock_dialog_class.assert_called_once_with(mock_root, self.mock_settings_manager, self.mock_profile_manager)
        # Überprüfe, ob die Einstellungen vom Dialog auf den GameManager übertragen wurden
        self.assertEqual(self.gm.game, "501")
        self.assertEqual(self.gm.players, ["Alice", "Bob"])
        self.assertEqual(self.gm.opt_out, "Double")
        self.assertEqual(self.gm.count_to, "501")
        self.assertEqual(self.gm.opt_in, "Single")
        self.assertEqual(self.gm.lifes, "5")
        self.assertEqual(self.gm.rounds, "10")
        # Überprüfe, ob auf den Dialog gewartet wurde
        mock_root.wait_window.assert_called_once_with(mock_dialog_class.return_value)

    @patch('core.gamemgr.GameSettingsDialog', spec=GameSettingsDialog)
    def test_configure_game_when_cancelled(self, mock_dialog_class):
        """
        Testet, ob configure_game die Standardeinstellungen beibehält,
        wenn der Benutzer den Dialog abbricht.
        """
        mock_root = MagicMock()
        # 1. Konfiguriere den Mock für die Dialog-Instanz
        mock_dialog_instance = mock_dialog_class.return_value
        mock_dialog_instance.was_started = False
        mock_dialog_instance.result = None

        # 2. Rufe die zu testende Methode auf
        result = self.gm.configure_game(mock_root)

        # 3. Überprüfe die Ergebnisse
        self.assertFalse(result)
        # Überprüfe, ob die Standardwerte des GameManagers unverändert sind
        self.assertEqual(self.gm.game, "301")
        self.assertEqual(self.gm.players, [])
        # Überprüfe, ob auf den Dialog gewartet wurde
        mock_root.wait_window.assert_called_once_with(mock_dialog_class.return_value)

if __name__ == '__main__':
    unittest.main()