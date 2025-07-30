import unittest
import tkinter as tk # Import real tkinter
from unittest.mock import MagicMock, ANY, patch

# Die zu testende Klasse
from core.gamemgr import GameSettingsDialog

class TestGameSettingsDialog(unittest.TestCase):
    """
    Testet die UI-Logik der GameSettingsDialog-Klasse isoliert.
    Verwendet eine echte, aber versteckte Tk-Instanz, um UI-Interaktionen
    zuverlässig zu testen, ohne Fenster anzuzeigen.
    """
    @classmethod
    def setUpClass(cls):
        """Erstellt eine einzige Tk-Wurzel für alle Tests in dieser Klasse."""
        cls.root = tk.Tk()
        # Verhindert, dass das Hauptfenster angezeigt wird
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        """Zerstört die Tk-Wurzel, nachdem alle Tests beendet sind."""
        if cls.root:
            cls.root.destroy()
            cls.root = None # Wichtig für saubere Testläufe

    def setUp(self):
        """Setzt für jeden Test einen neuen Dialog in einer Test-Umgebung auf."""
        # Patch wait_window, um zu verhindern, dass der modale Dialog den Test blockiert.
        # Dies ist notwendig, da der GameManager `parent.wait_window(dialog)` aufruft.
        # In unseren Tests ist `parent` die versteckte `tk.Tk`-Wurzel.
        patcher_wait = patch('tkinter.Toplevel.wait_window')
        patcher_wait.start()
        self.addCleanup(patcher_wait.stop)

        self.mock_settings_manager = MagicMock()
        self.mock_settings_manager.get.return_value = ["P1", "P2", "", ""] # für last_player_names

        self.mock_profile_manager = MagicMock()
        mock_profile1 = MagicMock()
        mock_profile1.name = "ProfA"
        mock_profile2 = MagicMock()
        mock_profile2.name = "ProfB"
        self.mock_profile_manager.get_profiles.return_value = [mock_profile1, mock_profile2]

        # Instanziiere den Dialog mit Mocks
        # Instanziiere den Dialog mit der echten, aber versteckten Wurzel
        self.dialog = GameSettingsDialog(self.root, self.mock_settings_manager, self.mock_profile_manager)
        # update() ist notwendig, damit die Widgets gezeichnet und ihre Werte gesetzt werden
        self.dialog.update()

    def tearDown(self):
        """Räumt nach jedem Test auf."""
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.destroy()

    def test_initialization_and_default_state(self):
        """Testet, ob der Dialog korrekt initialisiert wird und die Standardoptionen (X01) anzeigt."""
        self.mock_settings_manager.get.assert_called_with('last_player_names', ANY)

        # Prüfen, ob die Comboboxen die korrekten Werte haben
        self.assertEqual(self.dialog.player_name_entries[0].get(), "P1")
        self.assertEqual(self.dialog.player_name_entries[1].get(), "P2")

        # Prüfen, ob der korrekte Options-Frame sichtbar ist
        self.assertTrue(self.dialog.game_option_frames['x01_options'].winfo_ismapped())
        self.assertFalse(self.dialog.game_option_frames['killer_options'].winfo_ismapped())
        self.assertFalse(self.dialog.game_option_frames['shanghai_options'].winfo_ismapped())

    def test_set_game_changes_visible_options(self):
        """Testet, ob bei einer Spielauswahl der korrekte Options-Frame angezeigt wird."""
        # Simuliere die Auswahl von "Killer" durch den Benutzer
        self.dialog.game_select.set("Killer")
        # Löst den Callback aus, der die Frames umschaltet
        self.dialog.game_select.event_generate("<<ComboboxSelected>>")
        self.dialog.update() # Verarbeite das Event

        # Überprüfe die Sichtbarkeit der Frames
        self.assertFalse(self.dialog.game_option_frames['x01_options'].winfo_ismapped())
        self.assertTrue(self.dialog.game_option_frames['killer_options'].winfo_ismapped())

    def test_start_button_collects_data_and_sets_flag(self):
        """Testet, ob der Start-Button die Daten korrekt sammelt und den Dialog schließt."""
        # Benutzereingaben simulieren
        self.dialog.player_select.set("2")
        self.dialog.set_anzahl_spieler() # Löst den Callback aus, um Entries zu aktivieren/deaktivieren
        self.dialog.player_name_entries[0].set("Martin")
        self.dialog.player_name_entries[1].set("Gemini")

        # Spieloptionen simulieren
        self.dialog.game_select.set("501")
        self.dialog.game_select.event_generate("<<ComboboxSelected>>")
        self.dialog.opt_out_select.set("Double")
        self.dialog.opt_out_select.event_generate("<<ComboboxSelected>>")

        # Klick auf den Start-Button simulieren
        self.dialog._on_start()

        # Überprüfe das Ergebnis
        self.assertTrue(self.dialog.was_started)
        self.assertIsNotNone(self.dialog.result)
        self.assertEqual(self.dialog.result['players'], ["Martin", "Gemini"])
        self.assertEqual(self.dialog.result['game'], "501")
        self.assertEqual(self.dialog.result['opt_out'], "Double")

        expected_saved_names = ["Martin", "Gemini", "", ""]
        self.mock_settings_manager.set.assert_called_once_with('last_player_names', expected_saved_names)
        self.assertFalse(self.dialog.winfo_exists(), "Der Dialog sollte nach dem Start geschlossen sein.")

    def test_start_button_shows_error_on_duplicate_names(self):
        """Testet, ob ein Fehler angezeigt wird, wenn Spielernamen doppelt sind."""
        with patch('core.gamemgr.messagebox') as mock_messagebox:
            self.dialog.player_select.set("2")
            self.dialog.set_anzahl_spieler()
            self.dialog.player_name_entries[0].set("Martin")
            self.dialog.player_name_entries[1].set("Martin") # Duplikat

            self.dialog._on_start()

            self.assertFalse(self.dialog.was_started)
            mock_messagebox.showerror.assert_called_once_with("Fehler", "Spielernamen müssen eindeutig sein.", parent=self.dialog)
            self.assertTrue(self.dialog.winfo_exists(), "Der Dialog sollte nach einem Fehler offen bleiben.")

    def test_cancel_button_sets_flag_and_destroys(self):
        """Testet, ob der Abbrechen-Button den Dialog korrekt beendet."""
        self.dialog._on_cancel()
        self.assertFalse(self.dialog.was_started)
        self.assertIsNone(self.dialog.result)
        self.assertFalse(self.dialog.winfo_exists(), "Der Dialog sollte nach dem Abbrechen geschlossen sein.")

if __name__ == '__main__':
    unittest.main()
