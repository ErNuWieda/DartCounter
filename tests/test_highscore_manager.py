import unittest
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock, patch, call, ANY
import sys
import os
from datetime import date

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.highscore_manager import HighscoreManager

class TestHighscoreManager(unittest.TestCase):
    """
    Testet den HighscoreManager.
    Verwendet eine echte, aber versteckte Tk-Instanz, um UI-Interaktionen
    zuverlässig zu testen, ohne Fenster anzuzeigen oder Tests aufzuhängen.
    """

    @classmethod
    def setUpClass(cls):
        """Erstellt eine einzige Tk-Wurzel für alle Tests in dieser Klasse."""
        cls.root = tk.Tk()
        cls.root.withdraw() # Verhindert, dass das Hauptfenster angezeigt wird

    @classmethod
    def tearDownClass(cls):
        """Zerstört die Tk-Wurzel, nachdem alle Tests beendet sind."""
        if cls.root:
            cls.root.destroy()
            cls.root = None

    def setUp(self):
        """Wird vor jedem Test ausgeführt."""
        # Patch wait_window, um zu verhindern, dass modale Dialoge den Test blockieren.
        patcher_wait = patch('tkinter.Toplevel.wait_window')
        patcher_wait.start()
        self.addCleanup(patcher_wait.stop)

        # Wrapper, um neu erstellte Toplevel-Dialoge (wie den Reset-Dialog) abzufangen.
        # Dies ist entscheidend, um mit modalen Dialogen in Tests interagieren zu können.
        self.created_dialogs = []
        original_toplevel = tk.Toplevel
        def toplevel_wrapper(*args, **kwargs):
            dialog = original_toplevel(*args, **kwargs)
            self.created_dialogs.append(dialog)
            return dialog
        self.patcher_toplevel = patch('tkinter.Toplevel', new=toplevel_wrapper)
        self.patcher_toplevel.start()
        self.addCleanup(self.patcher_toplevel.stop)

        # Patch für die neuen UI-Utilities
        patcher_ui_utils = patch('core.highscore_manager.ui_utils')
        self.mock_ui_utils = patcher_ui_utils.start()
        self.addCleanup(patcher_ui_utils.stop)

        # Patch für die DatabaseManager-Abhängigkeit
        patcher_db = patch('core.highscore_manager.DatabaseManager')
        MockDatabaseManager = patcher_db.start()

        # Setze alle Mocks zurück, um saubere Tests zu gewährleisten
        MockDatabaseManager.reset_mock()

        # Erstelle eine Mock-Instanz des DatabaseManager
        self.mock_db_instance = MockDatabaseManager.return_value
        self.mock_db_instance.is_connected = True  # Standardmäßig verbunden

        self.highscore_manager = HighscoreManager(self.mock_db_instance)
        self.windows_to_destroy = []

    def tearDown(self):
        """Räumt nach jedem Test alle erstellten Fenster auf."""
        for window in self.windows_to_destroy:
            if window and window.winfo_exists():
                window.destroy()

    def test_initialization_handles_no_db_connection(self):
        """
        Testet, dass der Manager auch ohne DB-Verbindung initialisiert werden kann.
        """
        # Wir erstellen eine neue, getrennte Instanz für diesen spezifischen Testfall,
        # um die in setUp() erstellte Instanz nicht zu stören.
        mock_db_instance_disconnected = MagicMock()
        mock_db_instance_disconnected.is_connected = False

        highscore_manager = HighscoreManager(mock_db_instance_disconnected)

        # Die einzige Behauptung ist, dass die Initialisierung nicht abstürzt
        self.assertIsNotNone(highscore_manager)

    def test_show_highscores_window_db_not_connected(self):
        """Testet das Verhalten, wenn das Fenster ohne DB-Verbindung geöffnet wird."""
        self.mock_db_instance.is_connected = False
        window = self.highscore_manager.show_highscores_window(self.root)
        self.assertIsNone(window, "Es sollte kein Fenster erstellt werden.")
        self.mock_ui_utils.show_message.assert_called_once_with('warning', ANY, ANY, parent=self.root)

    def test_show_highscores_window_successful(self):
        """Testet die korrekte Erstellung des Highscore-Fensters und die Datenanzeige."""
        # Mock-Daten für verschiedene Spielmodi
        mock_scores_301 = [{'player_name': 'Alice', 'score_metric': 18, 'date': date(2023, 1, 1)}]
        mock_scores_cricket = [{'player_name': 'Bob', 'score_metric': 2.57, 'date': date(2023, 1, 2)}]
        self.mock_db_instance.get_scores.side_effect = [
            mock_scores_301,  # für 301
            [],  # für 501
            [],  # für 701
            mock_scores_cricket,  # für Cricket
            [], [],  # für Cut Throat, Tactics
        ]

        window = self.highscore_manager.show_highscores_window(self.root)
        self.windows_to_destroy.append(window)
        window.update() # Widgets zeichnen

        # Überprüfe den Widget-Typ über winfo_class(), das ist robuster in Tests.
        self.assertEqual(window.winfo_class(), 'Toplevel')
        notebook = window.winfo_children()[0]
        self.assertEqual(notebook.winfo_class(), 'TNotebook')

        # Überprüfen, ob die Daten im ersten Tab (301) korrekt sind
        tree_301 = notebook.tabs()[0]
        treeview_301 = window.nametowidget(tree_301).winfo_children()[0]
        self.assertEqual(len(treeview_301.get_children()), 1)
        item = treeview_301.item(treeview_301.get_children()[0])
        self.assertEqual(item['values'], ['1.', 'Alice', 18, '2023-01-01'])

        # Überprüfen, ob die Daten im Cricket-Tab korrekt sind
        tree_cricket = notebook.tabs()[3]
        treeview_cricket = window.nametowidget(tree_cricket).winfo_children()[0]
        self.assertEqual(len(treeview_cricket.get_children()), 1)
        item_cricket = treeview_cricket.item(treeview_cricket.get_children()[0])
        self.assertEqual(item_cricket['values'], ['1.', 'Bob', '2.57', '2023-01-02'])

    def _find_button_by_text(self, window, text):
        """
        Sucht rekursiv nach einem Button-Widget innerhalb eines Parent-Widgets
        anhand seines Textes.
        """
        for widget in window.winfo_children():
            if isinstance(widget, ttk.Button) and text in widget.cget("text"):
                return widget
            found = self._find_button_by_text(widget, text)
            if found:
                return found
        return None

    def test_prompt_and_reset_single_mode_confirmed(self):
        """Testet das Zurücksetzen eines einzelnen Modus nach Bestätigung."""
        # Simuliere "Ja" im finalen Bestätigungsdialog
        self.mock_ui_utils.ask_question.return_value = True

        # Öffne das Highscore-Fenster
        window = self.highscore_manager.show_highscores_window(self.root)
        self.windows_to_destroy.append(window)
        window.update()

        # 1. Wähle den zweiten Tab (501) im Hauptfenster aus, BEVOR der Dialog geöffnet wird.
        notebook = window.winfo_children()[0]
        notebook.select(1)

        # 2. Klicke den Haupt-Reset-Button, um den Auswahl-Dialog zu öffnen
        reset_button = self._find_button_by_text(window, "zurücksetzen")
        self.assertIsNotNone(reset_button)
        reset_button.invoke()

        # 3. Finde den neu erstellten modalen Dialog
        self.assertGreaterEqual(len(self.created_dialogs), 1, "Der Reset-Dialog wurde nicht erstellt.")
        reset_dialog = self.created_dialogs[-1]
        self.windows_to_destroy.append(reset_dialog)

        # 4. Finde den "Nur '501'"-Button im modalen Dialog und klicke ihn
        single_reset_button = self._find_button_by_text(reset_dialog, "Nur '501'")
        self.assertIsNotNone(single_reset_button, "Button zum Zurücksetzen des einzelnen Modus nicht gefunden.")
        single_reset_button.invoke()

        # Überprüfe die Ergebnisse
        self.mock_ui_utils.ask_question.assert_called_once()
        self.mock_db_instance.reset_scores.assert_called_once_with("501")
        self.mock_ui_utils.show_message.assert_called_once()
        self.assertFalse(window.winfo_exists(), "Das Highscore-Fenster sollte nach dem Reset geschlossen sein.")
        self.assertFalse(reset_dialog.winfo_exists(), "Der Reset-Dialog sollte nach dem Reset geschlossen sein.")

    def test_prompt_and_reset_all_modes_confirmed(self):
        """Testet das Zurücksetzen aller Modi nach Bestätigung."""
        self.mock_ui_utils.ask_question.return_value = True
        window = self.highscore_manager.show_highscores_window(self.root)
        self.windows_to_destroy.append(window)
        window.update()

        # 1. Klicke den Haupt-Reset-Button
        reset_button = self._find_button_by_text(window, "zurücksetzen")
        reset_button.invoke()

        # 2. Finde den modalen Dialog
        self.assertGreaterEqual(len(self.created_dialogs), 1, "Der Reset-Dialog wurde nicht erstellt.")
        reset_dialog = self.created_dialogs[-1]
        self.windows_to_destroy.append(reset_dialog)

        # 3. Finde den "Alle zurücksetzen"-Button und klicke ihn
        all_reset_button = self._find_button_by_text(reset_dialog, "Alle zurücksetzen")
        self.assertIsNotNone(all_reset_button)
        all_reset_button.invoke()

        self.mock_db_instance.reset_scores.assert_called_once_with(None)
        self.mock_ui_utils.show_message.assert_called_once()
        self.assertFalse(window.winfo_exists())
        self.assertFalse(reset_dialog.winfo_exists())

    def test_prompt_and_reset_cancelled(self):
        """Testet, dass nichts passiert, wenn der Benutzer den Reset abbricht."""
        window = self.highscore_manager.show_highscores_window(self.root)
        self.windows_to_destroy.append(window)
        window.update()

        # 1. Klicke den Haupt-Reset-Button
        reset_button = self._find_button_by_text(window, "zurücksetzen")
        reset_button.invoke()

        # 2. Finde den modalen Dialog
        self.assertGreaterEqual(len(self.created_dialogs), 1, "Der Reset-Dialog wurde nicht erstellt.")
        reset_dialog = self.created_dialogs[-1]
        self.windows_to_destroy.append(reset_dialog)

        # 3. Finde den "Abbrechen"-Button und klicke ihn
        cancel_button = self._find_button_by_text(reset_dialog, "Abbrechen")
        self.assertIsNotNone(cancel_button)
        cancel_button.invoke()

        self.mock_db_instance.reset_scores.assert_not_called()
        self.mock_ui_utils.show_message.assert_not_called()
        self.assertTrue(window.winfo_exists(), "Das Highscore-Fenster sollte nach dem Abbrechen geöffnet bleiben.")
        self.assertFalse(reset_dialog.winfo_exists(), "Der Reset-Dialog sollte nach dem Abbrechen geschlossen sein.")

if __name__ == '__main__':
    unittest.main(verbosity=2)