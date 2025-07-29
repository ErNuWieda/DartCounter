import unittest
import tkinter as tk
from unittest.mock import MagicMock, ANY, patch

# Die zu testende Klasse
from core.tournament_dialog import TournamentSettingsDialog

class TestTournamentSettingsDialog(unittest.TestCase):
    """
    Testet die UI-Logik der TournamentSettingsDialog-Klasse isoliert.
    """
    @classmethod
    def setUpClass(cls):
        """Erstellt eine einzige Tk-Wurzel für alle Tests in dieser Klasse."""
        cls.root = tk.Tk()
        cls.root.geometry("+5000+5000")

    @classmethod
    def tearDownClass(cls):
        """Zerstört die Tk-Wurzel, nachdem alle Tests beendet sind."""
        if cls.root:
            cls.root.destroy()

    def setUp(self):
        """Setzt für jeden Test einen neuen Dialog in einer Test-Umgebung auf."""
        # Patch wait_window, um zu verhindern, dass der modale Dialog den Test blockiert.
        patcher_wait = patch('tkinter.Toplevel.wait_window')
        patcher_wait.start()
        self.addCleanup(patcher_wait.stop)

        self.mock_settings_manager = MagicMock()
        self.mock_settings_manager.get.return_value = ["ProfA", "Guest1"] # für last_tournament_players

        self.mock_profile_manager = MagicMock()
        mock_profile_a = MagicMock()
        mock_profile_a.name = "ProfA"
        mock_profile_b = MagicMock()
        mock_profile_b.name = "ProfB"
        self.mock_profile_manager.get_profiles.return_value = [mock_profile_a, mock_profile_b]

        self.dialog = TournamentSettingsDialog(self.root, self.mock_profile_manager, self.mock_settings_manager)
        self.dialog.update()

    def tearDown(self):
        """Räumt nach jedem Test auf."""
        # Stelle sicher, dass der Dialog nur zerstört wird, wenn er noch existiert.
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.destroy()

    def test_initialization_loads_last_players(self):
        """Testet, ob der Dialog initialisiert und die zuletzt verwendeten Spieler korrekt lädt."""
        self.mock_settings_manager.get.assert_called_once_with('last_tournament_players', [])
        
        # Prüfen, ob die ersten beiden Spielereinträge auf die geladenen Namen gesetzt sind
        self.assertEqual(self.dialog.player_name_entries[0].get(), "ProfA")
        self.assertEqual(self.dialog.player_name_entries[1].get(), "Guest1")
        self.assertEqual(self.dialog.player_name_entries[2].get(), "") # Sollte leer sein
        self.assertEqual(self.dialog.player_name_entries[3].get(), "") # Sollte leer sein

    def test_start_button_collects_data_and_saves_settings(self):
        """Testet, ob der Start-Button die Daten korrekt sammelt und die Einstellungen speichert."""
        # Benutzereingaben simulieren
        self.dialog.player_count_var.set("2")
        self.dialog._update_player_entries() # Manuelles Auslösen des Updates
        self.dialog.player_name_entries[0].set("Alice")
        self.dialog.player_name_entries[1].set("Bob")
        self.dialog.game_mode_var.set("701")

        # Button-Klick simulieren
        self.dialog._on_start()

        self.assertFalse(self.dialog.cancelled)
        self.assertEqual(self.dialog.player_names, ["Alice", "Bob"])
        self.assertEqual(self.dialog.game_mode, "701")
        
        # Prüfen, ob die Einstellungen gespeichert wurden
        self.mock_settings_manager.set.assert_called_once_with('last_tournament_players', ["Alice", "Bob"])

    def test_start_button_shows_error_on_duplicate_names(self):
        """Testet, ob ein Fehler angezeigt wird, wenn die Spielernamen nicht eindeutig sind."""
        with patch('core.tournament_dialog.messagebox.showerror') as mock_showerror:
            self.dialog.player_count_var.set("2")
            self.dialog._update_player_entries()
            self.dialog.player_name_entries[0].set("SameName")
            self.dialog.player_name_entries[1].set("SameName")

            self.dialog._on_start()

            self.assertTrue(self.dialog.cancelled) # Sollte nicht fortfahren
            mock_showerror.assert_called_once_with("Fehler", "Spielernamen müssen eindeutig sein.", parent=self.dialog)

    def test_update_available_profiles_removes_selected_names(self):
        """Testet, ob die Profilliste korrekt gefiltert wird."""
        # "ProfA" ist bereits durch setUp ausgewählt.
        # Die Liste für die zweite Combobox sollte "ProfA" nicht enthalten.
        available_for_second = tuple(self.dialog.player_name_entries[1]['values'])
        self.assertNotIn("ProfA", available_for_second)
        self.assertIn("ProfB", available_for_second)
        
        # Die erste Box sollte "ProfA" aber noch zur Auswahl haben.
        available_for_first = tuple(self.dialog.player_name_entries[0]['values'])
        self.assertIn("ProfA", available_for_first)