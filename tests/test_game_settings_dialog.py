import unittest
import tkinter as tk
from unittest.mock import MagicMock, ANY
import sys
import os

# Fügt das Projektverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.gamemgr import GameSettingsDialog

class TestGameSettingsDialog(unittest.TestCase):
    """
    Testet die UI-Logik der GameSettingsDialog-Klasse isoliert.
    """
    def setUp(self):
        """Setzt für jeden Test einen neuen Dialog in einer Test-Umgebung auf."""
        self.root = tk.Tk()
        self.root.withdraw() # Verhindert, dass Fenster tatsächlich erscheinen
        self.mock_settings_manager = MagicMock()
        self.mock_settings_manager.get.return_value = ["P1", "P2", "P3", "P4"]
        self.dialog = GameSettingsDialog(self.root, self.mock_settings_manager)
        # Wichtig, damit UI-Updates im Test verarbeitet werden
        self.dialog.update_idletasks()

    def tearDown(self):
        """Räumt nach jedem Test auf."""
        if self.dialog:
            self.dialog.destroy()
        if self.root:
            self.root.destroy()

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
        self.assertEqual(self.dialog.players, ["Martin", "Gemini"])
        self.mock_settings_manager.set.assert_called_with('last_player_names', ANY)

if __name__ == '__main__':
    unittest.main()