import unittest
from unittest.mock import MagicMock, patch, mock_open, call
import sys
import os
from datetime import date

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mocke tkinter komplett, BEVOR es vom HighscoreManager importiert wird
mock_tk = MagicMock()
sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = mock_tk.ttk
sys.modules['tkinter.messagebox'] = mock_tk.messagebox
sys.modules['tkinter.filedialog'] = mock_tk.filedialog

# Wir patchen die DatabaseManager-Klasse an der Stelle, an der sie importiert wird
@patch('core.highscore_manager.DatabaseManager')
class TestHighscoreManager(unittest.TestCase):

    def setUp(self, MockDatabaseManager):
        """Wird vor jedem Test ausgeführt."""
        # Setze alle Mocks zurück, um saubere Tests zu gewährleisten
        mock_tk.reset_mock()
        MockDatabaseManager.reset_mock()

        # Erstelle eine Mock-Instanz des DatabaseManager
        self.mock_db_instance = MockDatabaseManager.return_value

        # Importiere den HighscoreManager, nachdem die Mocks eingerichtet sind
        from core.highscore_manager import HighscoreManager
        self.highscore_manager = HighscoreManager()

    def test_add_score_successful(self, MockDatabaseManager):
        """Testet das erfolgreiche Hinzufügen eines Scores."""
        self.mock_db_instance.is_connected = True
        self.highscore_manager.add_score("501", "Alice", 22)
        self.mock_db_instance.add_score.assert_called_once_with("501", "Alice", 22)

    def test_add_score_db_not_connected(self, MockDatabaseManager):
        """Testet, dass kein Score hinzugefügt wird, wenn keine DB-Verbindung besteht."""
        self.mock_db_instance.is_connected = False
        self.highscore_manager.add_score("501", "Alice", 22)
        self.mock_db_instance.add_score.assert_not_called()

    def test_add_score_invalid_mode(self, MockDatabaseManager):
        """Testet, dass kein Score für einen ungültigen Spielmodus hinzugefügt wird."""
        self.mock_db_instance.is_connected = True
        self.highscore_manager.add_score("Around the Clock", "Bob", 15)
        self.mock_db_instance.add_score.assert_not_called()

    def test_show_highscores_window_db_not_connected(self, MockDatabaseManager):
        """Testet das Verhalten, wenn das Fenster ohne DB-Verbindung geöffnet wird."""
        self.mock_db_instance.is_connected = False
        self.highscore_manager.show_highscores_window(MagicMock())
        mock_tk.messagebox.showwarning.assert_called_once()
        mock_tk.Toplevel.assert_not_called()

    def test_show_highscores_window_successful(self, MockDatabaseManager):
        """Testet die korrekte Erstellung des Highscore-Fensters und die Datenanzeige."""
        self.mock_db_instance.is_connected = True
        
        # Mock-Daten für verschiedene Spielmodi
        mock_scores_301 = [{'player_name': 'Alice', 'score_metric': 18, 'date': date(2023, 1, 1)}]
        mock_scores_cricket = [{'player_name': 'Bob', 'score_metric': 2.57, 'date': date(2023, 1, 2)}]
        self.mock_db_instance.get_scores.side_effect = [
            mock_scores_301, # für 301
            [], # für 501
            [], # für 701
            mock_scores_cricket, # für Cricket
            [], [], # für Cut Throat, Tactics
        ]

        mock_root = MagicMock()
        self.highscore_manager.show_highscores_window(mock_root)

        # Überprüfen, ob die UI-Elemente erstellt wurden
        mock_tk.Toplevel.assert_called_once_with(mock_root)
        mock_tk.ttk.Notebook.assert_called_once()
        
        # Überprüfen, ob Treeview für jeden Modus erstellt wurde (6 Modi)
        self.assertEqual(mock_tk.ttk.Treeview.call_count, 6)

        # Überprüfen, ob die Daten korrekt in die Treeviews eingefügt wurden
        mock_treeview_instance = mock_tk.ttk.Treeview.return_value
        
        # Erwartete Aufrufe an tree.insert()
        expected_calls = [
            # 301-Score (als int formatiert)
            call('', 'end', values=('1.', 'Alice', 18, '2023-01-01')),
            # Cricket-Score (als float mit 2 Nachkommastellen formatiert)
            call('', 'end', values=('1.', 'Bob', '2.57', '2023-01-02'))
        ]
        mock_treeview_instance.insert.assert_has_calls(expected_calls, any_order=True)

    @patch('builtins.open', new_callable=mock_open)
    @patch('core.highscore_manager.csv')
    def test_export_highscores_successful(self, mock_csv, mock_file, MockDatabaseManager):
        """Testet den erfolgreichen Export von Highscores in eine CSV-Datei."""
        self.mock_db_instance.is_connected = True
        mock_tk.filedialog.asksaveasfilename.return_value = "test_export.csv"
        
        mock_scores = [{'player_name': 'Charlie', 'score_metric': 35, 'date': date(2023, 1, 3)}]
        self.mock_db_instance.get_scores.return_value = mock_scores

        self.highscore_manager.export_highscores_to_csv(MagicMock())

        # Überprüfen, ob die Datei zum Schreiben geöffnet wurde
        mock_file.assert_called_once_with("test_export.csv", 'w', newline='', encoding='utf-8')
        
        # Überprüfen, ob der CSV-Writer korrekt verwendet wurde
        mock_csv.DictWriter.assert_called_once()
        writer_instance = mock_csv.DictWriter.return_value
        writer_instance.writeheader.assert_called_once()
        writer_instance.writerows.assert_called_once()
        
        # Überprüfen, ob eine Erfolgsmeldung angezeigt wurde
        mock_tk.messagebox.showinfo.assert_called_once()

    def test_export_highscores_user_cancels(self, MockDatabaseManager):
        """Testet das Verhalten, wenn der Benutzer den Speicherdialog abbricht."""
        self.mock_db_instance.is_connected = True
        mock_tk.filedialog.asksaveasfilename.return_value = "" # Benutzer klickt "Abbrechen"

        self.highscore_manager.export_highscores_to_csv(MagicMock())

        # Es darf keine Datei geöffnet und keine Erfolgsmeldung angezeigt werden
        self.mock_db_instance.get_scores.assert_not_called()
        mock_tk.messagebox.showinfo.assert_not_called()

    def _simulate_reset_dialog(self, button_index, confirm_reset, MockDatabaseManager):
        """Hilfsmethode zur Simulation des Reset-Dialogs."""
        mock_win = MagicMock()
        mock_notebook = MagicMock()
        mock_notebook.index.return_value = 1
        mock_notebook.tab.return_value = "501"

        mock_reset_dialog = MagicMock()
        mock_tk.Toplevel.return_value = mock_reset_dialog
        mock_tk.messagebox.askyesno.return_value = confirm_reset

        # Rufen Sie die Methode auf, die den Dialog erstellt
        self.highscore_manager._prompt_and_reset(mock_win, mock_notebook)

        # Erfassen Sie die `command`-Argumente der erstellten Buttons
        button_commands = [
            c.kwargs['command'] for c in mock_tk.ttk.Button.call_args_list
        ]

        # Führen Sie den Befehl des ausgewählten Buttons aus
        command_to_run = button_commands[button_index]
        command_to_run()

        return mock_win, mock_reset_dialog

    def test_prompt_and_reset_single_mode_confirmed(self, MockDatabaseManager):
        """Testet das Zurücksetzen eines einzelnen Modus nach Bestätigung."""
        mock_win, mock_reset_dialog = self._simulate_reset_dialog(
            button_index=0, # "Nur '501'" Button
            confirm_reset=True,
            MockDatabaseManager=MockDatabaseManager
        )

        # Überprüfen, ob die richtige DB-Methode aufgerufen wurde
        self.mock_db_instance.reset_scores.assert_called_once_with("501")
        mock_tk.messagebox.showinfo.assert_called_once()
        mock_reset_dialog.destroy.assert_called_once()
        mock_win.destroy.assert_called_once()

    def test_prompt_and_reset_all_modes_confirmed(self, MockDatabaseManager):
        """Testet das Zurücksetzen aller Modi nach Bestätigung."""
        mock_win, mock_reset_dialog = self._simulate_reset_dialog(
            button_index=1, # "Alle zurücksetzen" Button
            confirm_reset=True,
            MockDatabaseManager=MockDatabaseManager
        )

        # Überprüfen, ob die DB-Methode mit None (für alle) aufgerufen wurde
        self.mock_db_instance.reset_scores.assert_called_once_with(None)
        mock_tk.messagebox.showinfo.assert_called_once()
        mock_reset_dialog.destroy.assert_called_once()
        mock_win.destroy.assert_called_once()

    def test_prompt_and_reset_cancelled(self, MockDatabaseManager):
        """Testet, dass nichts passiert, wenn der Benutzer den Reset abbricht."""
        self._simulate_reset_dialog(
            button_index=0, # Spielt keine Rolle, welcher Button
            confirm_reset=False, # Benutzer klickt "Nein"
            MockDatabaseManager=MockDatabaseManager
        )

        # Die Reset-Methode der DB darf nicht aufgerufen werden
        self.mock_db_instance.reset_scores.assert_not_called()
        # Es wird keine Erfolgsmeldung angezeigt
        mock_tk.messagebox.showinfo.assert_not_called()


if __name__ == '__main__':
    unittest.main()