import unittest
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock, patch

from core.settings_dialog import AppSettingsDialog

class TestAppSettingsDialog(unittest.TestCase):
    """
    Testet die UI-Logik des AppSettingsDialog isoliert.
    """
    @classmethod
    def setUpClass(cls):
        """Erstellt eine einzige Tk-Wurzel für alle Tests in dieser Klasse."""
        cls.root = tk.Tk()
        cls.root.geometry("+5000+5000")

    @classmethod
    def tearDownClass(cls):
        """Zerstört die Tk-Wurzel, nachdem alle Tests in dieser Klasse ausgeführt wurden."""
        cls.root.destroy()

    def setUp(self):
        """Setzt für jeden Test einen neuen Dialog in einer Test-Umgebung auf."""
        # Erstelle Mocks für die Manager-Abhängigkeiten
        self.mock_settings_manager = MagicMock()
        self.mock_settings_manager.get.return_value = 'light' # Simuliere das geladene Theme

        self.mock_sound_manager = MagicMock()
        self.mock_sound_manager.sounds_enabled = True # Simuliere, dass Sound an ist

        self.dialog = AppSettingsDialog(self.root, self.mock_settings_manager, self.mock_sound_manager)
        # Wichtig, damit UI-Updates im Test verarbeitet werden. update() ist robuster.
        self.dialog.update()

    def tearDown(self):
        """Räumt nach jedem Test auf."""
        self.dialog.destroy() # Zerstört nur den Dialog, nicht die Wurzel

    def test_initialization_sets_widgets_correctly(self):
        """Testet, ob die Widgets mit den Werten der Manager initialisiert werden."""
        # Finde den Checkbutton und prüfe seinen Zustand
        sound_check = [w for w in self.dialog.winfo_children() if isinstance(w, ttk.Checkbutton)][0]
        self.assertTrue(sound_check.instate(['selected']), "Sound-Checkbutton sollte standardmäßig aktiviert sein.")

        # Finde die Combobox und prüfe ihren Wert
        theme_combo = self.dialog.nametowidget(self.dialog.winfo_children()[1].winfo_children()[0])
        self.assertEqual(theme_combo.get(), 'Light', "Theme-Combobox sollte 'Light' anzeigen.")

    def test_sound_checkbutton_toggles_sound(self):
        """Testet, ob das Klicken des Checkbuttons die Sound-Manager-Methode aufruft."""
        sound_check = [w for w in self.dialog.winfo_children() if isinstance(w, ttk.Checkbutton)][0]
        sound_check.invoke() # Simuliert einen Klick, der den Zustand von True auf False ändert
        self.mock_sound_manager.toggle_sounds.assert_called_once_with(False)

    @patch('core.settings_dialog.sv_ttk.set_theme')
    def test_theme_combobox_changes_theme(self, mock_set_theme):
        """Testet, ob das Ändern der Combobox das Theme setzt und speichert."""
        theme_combo = self.dialog.nametowidget(self.dialog.winfo_children()[1].winfo_children()[0])
        theme_combo.set("Dark")
        theme_combo.event_generate("<<ComboboxSelected>>")

        self.mock_settings_manager.set.assert_called_once_with('theme', 'dark')
        mock_set_theme.assert_called_once_with('dark')

if __name__ == '__main__':
    unittest.main()