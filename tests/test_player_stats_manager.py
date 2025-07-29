import unittest
from unittest.mock import MagicMock, patch, call
import sys
import os
from datetime import datetime

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mocke UI- und Plotting-Bibliotheken, BEVOR sie importiert werden
mock_tk = MagicMock()
sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = mock_tk.ttk
sys.modules['tkinter.messagebox'] = mock_tk.messagebox

mock_matplotlib = MagicMock()
sys.modules['matplotlib'] = mock_matplotlib
sys.modules['matplotlib.pyplot'] = mock_matplotlib.pyplot
sys.modules['matplotlib.figure'] = mock_matplotlib.figure
sys.modules['matplotlib.backends'] = MagicMock()
sys.modules['matplotlib.backends.backend_tkagg'] = MagicMock()

# Wir patchen die DatabaseManager-Klasse an der Stelle, an der sie importiert wird
@patch('core.player_stats_manager.DatabaseManager')
class TestPlayerStatsManager(unittest.TestCase):

    def setUp(self, MockDatabaseManager):
        """Wird vor jedem Test ausgeführt."""
        # Setze alle Mocks zurück, um saubere Tests zu gewährleisten
        mock_tk.reset_mock()
        mock_matplotlib.pyplot.reset_mock()
        MockDatabaseManager.reset_mock()

        # Erstelle eine Mock-Instanz des DatabaseManager
        self.mock_db_instance = MockDatabaseManager.return_value
        self.mock_db_instance.is_connected = True

        # Importiere die zu testende Klasse, nachdem die Mocks eingerichtet sind
        from core.player_stats_manager import PlayerStatsManager
        self.stats_manager = PlayerStatsManager()

    def test_initialization_and_player_loading(self, MockDatabaseManager):
        """Testet, dass beim Initialisieren die Spielernamen geladen werden."""
        self.mock_db_instance.get_all_player_names_from_records.return_value = ["Alice", "Bob"]
        
        from core.player_stats_manager import PlayerStatsManager
        stats_manager = PlayerStatsManager()

        self.mock_db_instance.get_all_player_names_from_records.assert_called_once()
        self.assertEqual(stats_manager.player_names, ["Alice", "Bob"])

    def test_add_game_record_delegation(self, MockDatabaseManager):
        """Testet, dass das Hinzufügen eines Datensatzes an den DB-Manager delegiert wird."""
        self.mock_db_instance.is_connected = True
        stats_data = {'win': True, 'average': 80.0}
        self.stats_manager.add_game_record("Charlie", stats_data)
        self.mock_db_instance.add_game_record.assert_called_once_with("Charlie", stats_data)

    def test_show_stats_window_db_not_connected(self, MockDatabaseManager):
        """Testet, dass eine Warnung angezeigt wird, wenn keine DB-Verbindung besteht."""
        self.stats_manager.db_manager.is_connected = False
        self.stats_manager.show_stats_window(MagicMock())
        mock_tk.messagebox.showwarning.assert_called_once()
        mock_tk.Toplevel.assert_not_called()

    def test_show_stats_window_no_players(self, MockDatabaseManager):
        """Testet, dass eine Info angezeigt wird, wenn keine Spielerdaten vorhanden sind."""
        self.stats_manager.player_names = []
        self.stats_manager.show_stats_window(MagicMock())
        mock_tk.messagebox.showinfo.assert_called_once()
        mock_tk.Toplevel.assert_not_called()

    def test_show_stats_window_successful_creation(self, MockDatabaseManager):
        """Testet die erfolgreiche Erstellung des UI-Fensters."""
        self.stats_manager.player_names = ["Alice"]
        mock_root = MagicMock()
        self.stats_manager.show_stats_window(mock_root)

        mock_tk.Toplevel.assert_called_once_with(mock_root)
        mock_tk.ttk.Combobox.assert_called_once()
        combobox_instance = mock_tk.ttk.Combobox.return_value
        combobox_instance.config.assert_called_with(values=["Alice"])
        mock_matplotlib.pyplot.subplots.assert_called()

    def test_on_player_select_flow(self, MockDatabaseManager):
        """Testet den logischen Ablauf, wenn ein Spieler ausgewählt wird."""
        # Richte zuerst das Fenster und die Mocks ein
        self.stats_manager.player_names = ["Alice"]
        self.stats_manager.show_stats_window(MagicMock())

        mock_records = [
            {'game_date': datetime(2023, 1, 1), 'average': 60.5, 'win': True, 'mpr': None, 'checkout_percentage': 25.0, 'highest_finish': 80}
        ]
        self.mock_db_instance.get_records_for_player.return_value = mock_records

        # Mocke die internen Update-Methoden, um den Flow zu testen
        self.stats_manager._update_average_plot = MagicMock()
        self.stats_manager._update_win_loss_pie = MagicMock()
        self.stats_manager._update_stats_labels = MagicMock()

        # Simuliere das Event
        self.stats_manager.player_combo.get.return_value = "Alice"
        self.stats_manager._on_player_select(MagicMock())

        self.mock_db_instance.get_records_for_player.assert_called_once_with("Alice")
        self.stats_manager._update_average_plot.assert_called_once_with(mock_records)
        self.stats_manager._update_win_loss_pie.assert_called_once_with(mock_records)
        self.stats_manager._update_stats_labels.assert_called_once_with(mock_records)

    def test_update_average_plot_logic(self, MockDatabaseManager):
        """Testet die Logik zur Erstellung des Liniendiagramms."""
        self.stats_manager.show_stats_window(MagicMock())

        mock_records = [
            {'game_date': datetime(2023, 1, 5, 11, 0), 'average': 70.0, 'mpr': None},
            {'game_date': datetime(2023, 1, 1, 10, 0), 'average': 60.5, 'mpr': None},
            {'game_date': datetime(2023, 1, 2, 12, 0), 'average': None, 'mpr': 2.5}
        ]
        
        mock_ax = self.stats_manager.ax_avg
        self.stats_manager._update_average_plot(mock_records)

        mock_ax.clear.assert_called_once()
        # Es sollten zwei Plots erstellt werden: einer für Average, einer für MPR
        self.assertEqual(mock_ax.plot.call_count, 2)
        
        # Überprüfe die Daten für den Average-Plot (sollten nach Datum sortiert sein)
        avg_call = mock_ax.plot.call_args_list[0]
        dates_avg, values_avg = avg_call.args[0], avg_call.args[1]
        self.assertEqual(dates_avg, [datetime(2023, 1, 1, 10, 0), datetime(2023, 1, 5, 11, 0)])
        self.assertEqual(values_avg, [60.5, 70.0])

        mock_ax.set_title.assert_called()
        self.stats_manager.canvas_avg.draw.assert_called_once()

    def test_update_win_loss_pie_logic(self, MockDatabaseManager):
        """Testet die Logik zur Erstellung des Kuchendiagramms."""
        self.stats_manager.show_stats_window(MagicMock())

        mock_records = [{'win': True}, {'win': True}, {'win': False}]
        mock_ax = self.stats_manager.ax_pie

        self.stats_manager._update_win_loss_pie(mock_records)

        mock_ax.clear.assert_called_once()
        mock_ax.pie.assert_called_once()
        
        # Überprüfe die an pie() übergebenen Daten
        sizes = mock_ax.pie.call_args.args[0]
        labels = mock_ax.pie.call_args.kwargs['labels']
        self.assertEqual(sizes, [2, 1]) # 2 Siege, 1 Niederlage
        self.assertEqual(labels, ['Siege', 'Niederlagen'])

        self.stats_manager.canvas_pie.draw.assert_called_once()

    def test_update_stats_labels_logic(self, MockDatabaseManager):
        """Testet die Berechnung und Anzeige der Text-Statistiken."""
        self.stats_manager.show_stats_window(MagicMock())

        mock_records = [
            {'win': True, 'average': 80.0, 'mpr': None, 'checkout_percentage': 50.0, 'highest_finish': 120},
            {'win': False, 'average': 70.0, 'mpr': None, 'checkout_percentage': 10.0, 'highest_finish': 40},
            {'win': True, 'average': None, 'mpr': 2.5, 'checkout_percentage': None, 'highest_finish': None},
        ]

        self.stats_manager._update_stats_labels(mock_records)

        # Erwartete Texte für die Labels
        expected_texts = {
            'total_games': "Gespielte Spiele: 3",
            'win_rate': "Siegesquote: 66.7%",
            'best_avg': "Bester 3-Dart-Avg (X01): 80.00",
            'best_mpr': "Bester MPR (Cricket): 2.50",
            'best_checkout': "Höchstes Finish: 120"
        }

        # Überprüfe, ob jedes Label mit dem korrekten Text konfiguriert wurde
        for key, label_mock in self.stats_manager.stats_labels.items():
            actual_text = label_mock.config.call_args.kwargs['text']
            self.assertEqual(actual_text, expected_texts[key])

if __name__ == '__main__':
    unittest.main()