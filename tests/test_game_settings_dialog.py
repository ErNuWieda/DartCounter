import unittest
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock, ANY

from core.gamemgr import GameSettingsDialog

class TestGameSettingsDialog(unittest.TestCase):
    """
    Testet die UI-Logik der GameSettingsDialog-Klasse isoliert.
    """
    @classmethod
    def setUpClass(cls):
        """Erstellt eine einzige Tk-Wurzel für alle Tests in dieser Klasse, um Tcl-Fehler zu vermeiden."""
        cls.root = tk.Tk()
        # Verhindert, dass Fenster tatsächlich erscheinen, indem wir sie außerhalb des sichtbaren Bereichs verschieben.
        cls.root.geometry("+5000+5000")

    @classmethod
    def tearDownClass(cls):
        """Zerstört die Tk-Wurzel, nachdem alle Tests in dieser Klasse ausgeführt wurden."""
        if cls.root:
            cls.root.destroy()

    def setUp(self):
        """Setzt für jeden Test einen neuen Dialog in einer Test-Umgebung auf."""
        self.mock_settings_manager = MagicMock()
        self.mock_settings_manager.get.return_value = ["P1", "P2", "P3", "P4"] # for last_player_names
        
        self.mock_profile_manager = MagicMock()
        mock_profile1 = MagicMock()
        mock_profile1.name = "ProfA"
        mock_profile2 = MagicMock()
        mock_profile2.name = "ProfB"
        self.mock_profile_manager.get_profiles.return_value = [mock_profile1, mock_profile2]
        self.dialog = GameSettingsDialog(self.root, self.mock_settings_manager, self.mock_profile_manager) # self.root ist jetzt aus setUpClass
        # Wichtig, damit UI-Updates im Test verarbeitet werden.
        # update() ist unter Windows zuverlässiger als update_idletasks().
        self.dialog.update()

    def tearDown(self):
        """Räumt nach jedem Test auf."""
        self.dialog.destroy() # Zerstört nur den Dialog, nicht die Wurzel

    def test_initial_state_shows_x01_options(self):
        """Testet, ob der Dialog standardmäßig die Optionen für '301' anzeigt."""
        self.assertEqual(self.dialog.game, "301")
        
        x01_frame = self.dialog.game_option_frames["x01_options"]
        killer_frame = self.dialog.game_option_frames["killer_options"]

        self.assertTrue(x01_frame.winfo_ismapped(), "x01-Frame sollte standardmäßig sichtbar sein.")
        self.assertFalse(killer_frame.winfo_ismapped(), "Killer-Frame sollte standardmäßig unsichtbar sein.")

    def test_change_game_shows_correct_options_frame(self):
        """Testet, ob bei einer Spielauswahl der korrekte Options-Frame angezeigt wird."""
        game_select_combo = self.dialog.game_select
        x01_frame = self.dialog.game_option_frames["x01_options"]
        killer_frame = self.dialog.game_option_frames["killer_options"]

        # Simuliere die Auswahl von "Killer" durch den Benutzer
        game_select_combo.set("Killer")
        game_select_combo.event_generate("<<ComboboxSelected>>")
        self.dialog.update_idletasks()

        # Überprüfe den neuen Zustand
        self.assertEqual(self.dialog.game, "Killer")
        self.assertFalse(x01_frame.winfo_ismapped(), "x01-Frame sollte nach Wechsel zu Killer unsichtbar sein.")
        self.assertTrue(killer_frame.winfo_ismapped(), "Killer-Frame sollte nach Wechsel sichtbar sein.")
        
        # Check if comboboxes for players have the profile names
        player_combo = self.dialog.player_name_entries[0]
        self.assertIsInstance(player_combo, ttk.Combobox)
        self.assertEqual(tuple(player_combo['values']), ('ProfA', 'ProfB'))

    def test_start_button_collects_data_and_sets_flag(self):
        """Testet, ob der Start-Button die Daten korrekt sammelt und den Dialog schließt."""
        # Benutzereingaben simulieren
        self.dialog.player_select.set("2")
        self.dialog.set_anzahl_spieler() # Callback manuell aufrufen
        self.dialog.player_name_entries[0].delete(0, tk.END)
        self.dialog.player_name_entries[0].insert(0, "Martin")
        self.dialog.player_name_entries[1].delete(0, tk.END)
        self.dialog.player_name_entries[1].insert(0, "Gemini")

        # Simuliere den Klick auf den Start-Button
        self.dialog._on_start()

        # Überprüfe das Ergebnis
        self.assertTrue(self.dialog.was_started)
        self.assertIsNotNone(self.dialog.result, "Das Ergebnis-Dictionary sollte nicht None sein.")
        self.assertEqual(self.dialog.result['players'], ["Martin", "Gemini"])
        self.mock_settings_manager.set.assert_called_with('last_player_names', ANY)

if __name__ == '__main__':
    unittest.main()