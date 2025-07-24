import unittest
import tkinter as tk
from unittest.mock import patch, MagicMock, ANY
import pathlib # Import pathlib für plattformunabhängige Pfad-Tests

# Wichtig: Wir müssen die zu testenden Klassen und Funktionen importieren.
from main import App, get_asset_path

# Wir müssen auch die Klassen importieren, die wir mocken wollen,
# damit 'isinstance' in den Tests funktioniert.
from core.game import Game
from core.gamemgr import GameManager
from core.save_load_manager import SaveLoadManager


class TestGetAssetPath(unittest.TestCase):
    """Testet die Hilfsfunktion get_asset_path."""

    @patch('sys.hasattr', return_value=False)
    def test_dev_mode_path(self, mock_hasattr):
        """Testet den Pfad im normalen Entwicklungsmodus."""
        path = get_asset_path(pathlib.Path("assets/test.png"))
        # Erwartet, dass der Pfad relativ zum Projektverzeichnis ist
        self.assertTrue(str(path).endswith(str(pathlib.Path('assets/test.png'))))

    @patch('sys.hasattr', return_value=True)
    @patch('sys._MEIPASS', '/tmp/_MEI12345', create=True)
    def test_pyinstaller_mode_path(self, mock_hasattr):
        """Testet den Pfad, wenn die Anwendung gepackt ist (PyInstaller)."""
        path = get_asset_path(pathlib.Path("assets/test.png"))
        # Erwartet, dass der Pfad vom _MEIPASS-Verzeichnis ausgeht
        self.assertEqual(str(path), str(pathlib.Path('/tmp/_MEI12345/assets/test.png')))


class TestApp(unittest.TestCase):
    """Testet die Hauptanwendungsklasse 'App'."""

    @patch('main.sv_ttk.set_theme')
    @patch('main.Image.open')
    @patch('main.ImageTk.PhotoImage')
    @patch('tkinter.Canvas')
    @patch('tkinter.Menu')
    def setUp(self, mock_menu, mock_canvas, mock_photo, mock_img_open, mock_theme):
        """
        Setzt eine Testumgebung für jeden Test auf.
        Initialisiert die App mit gemockten UI-Komponenten, um zu verhindern,
        dass echte Fenster erstellt werden.
        """
        self.root = tk.Tk()
        # Verhindert, dass das Hauptfenster während der Tests erscheint
        self.root.withdraw()
        self.app = App(self.root)

    def tearDown(self):
        """Räumt nach jedem Test auf."""
        # Zerstört das root-Fenster sicher
        if self.root:
            self.root.destroy()

    def test_initialization(self):
        """Testet, ob die App korrekt mit all ihren Managern initialisiert wird."""
        self.assertIsNotNone(self.app.settings_manager)
        self.assertIsNotNone(self.app.sound_manager)
        self.assertIsNotNone(self.app.highscore_manager)
        self.assertIsNotNone(self.app.player_stats_manager)
        self.assertIsNone(self.app.game_instance)
        self.assertEqual(self.app.version, "v1.2.0")

    @patch('main.GameManager')
    @patch('main.App._initialize_game_session')
    def test_new_game_starts_successfully(self, mock_init_session, mock_game_manager):
        """Testet den 'Neues Spiel'-Workflow, wenn der Benutzer das Spiel startet."""
        # Konfiguriere den Mock für GameManager
        mock_gm_instance = mock_game_manager.return_value
        mock_gm_instance.configure_game.return_value = True # Simuliert, dass der User "Start" klickt
        mock_gm_instance.game = "501"
        mock_gm_instance.players = ["Player 1"]
        # ... weitere Optionen hier hinzufügen, falls nötig

        self.app.new_game()

        # Prüfen, ob der GameManager aufgerufen wurde
        mock_game_manager.assert_called_once_with(self.app.sound_manager, self.app.settings_manager)
        # Prüfen, ob die Konfigurationsmethode aufgerufen wurde
        mock_gm_instance.configure_game.assert_called_once_with(self.app.root)
        # Prüfen, ob die Spiel-Session mit den korrekten Optionen initialisiert wurde
        mock_init_session.assert_called_once()
        # Prüfen, ob die game_instance gesetzt wurde
        self.assertIsNotNone(self.app.game_instance)

    @patch('main.GameManager')
    @patch('main.App._initialize_game_session')
    def test_new_game_aborted_by_user(self, mock_init_session, mock_game_manager):
        """Testet den 'Neues Spiel'-Workflow, wenn der Benutzer den Dialog abbricht."""
        mock_gm_instance = mock_game_manager.return_value
        mock_gm_instance.configure_game.return_value = False # Simuliert, dass der User den Dialog abbricht

        self.app.new_game()

        mock_game_manager.assert_called_once_with(self.app.sound_manager, self.app.settings_manager)
        mock_gm_instance.configure_game.assert_called_once_with(self.app.root)
        # Die Spiel-Session darf nicht initialisiert worden sein
        mock_init_session.assert_not_called()
        self.assertIsNone(self.app.game_instance)

    @patch('tkinter.messagebox.askyesno', return_value=True)
    def test_check_and_close_existing_game_confirmed(self, mock_askyesno):
        """Testet, ob ein laufendes Spiel beendet wird, wenn der Benutzer bestätigt."""
        # Erstelle ein Mock-Spiel
        mock_game = MagicMock(spec=Game) # Lokale Referenz
        mock_game.end = False
        self.app.game_instance = mock_game

        result = self.app._check_and_close_existing_game("Titel", "Nachricht")

        mock_askyesno.assert_called_once()
        # Prüfe den Aufruf auf der lokalen Referenz, nicht auf self.app.game_instance.
        mock_game.destroy.assert_called_once() 
        self.assertIsNone(self.app.game_instance)
        self.assertTrue(result)

    @patch('tkinter.messagebox.askyesno', return_value=False)
    def test_check_and_close_existing_game_cancelled(self, mock_askyesno):
        """Testet, ob ein laufendes Spiel NICHT beendet wird, wenn der Benutzer abbricht."""
        mock_game = MagicMock(spec=Game)
        mock_game.end = False
        self.app.game_instance = mock_game

        result = self.app._check_and_close_existing_game("Titel", "Nachricht")

        mock_askyesno.assert_called_once()
        mock_game.destroy.assert_not_called()
        self.assertIsNotNone(self.app.game_instance)
        self.assertFalse(result)

    @patch('main.SaveLoadManager.load_game_data')
    @patch('main.App._initialize_game_session', return_value=MagicMock(spec=Game))
    @patch('main.SaveLoadManager.restore_game_state')
    def test_load_game_successful(self, mock_restore, mock_init_session, mock_load_data):
        """Testet den erfolgreichen Ladevorgang eines Spiels."""
        # Simuliere geladene Spieldaten
        mock_data = {
            'game_name': '301', 'opt_in': 'Single', 'opt_out': 'Double',
            'opt_atc': 'Single', 'count_to': '301', 'lifes': '3', 'rounds': '7',
            'players': [{'name': 'P1'}]
        }
        mock_load_data.return_value = mock_data

        self.app.load_game()

        mock_load_data.assert_called_once_with(self.app.root)
        mock_init_session.assert_called_once()
        mock_restore.assert_called_once_with(mock_init_session.return_value, mock_data)
        self.assertEqual(self.app.game_instance, mock_init_session.return_value)


    @patch('main.SaveLoadManager.save_game_state')
    @patch('tkinter.messagebox.showinfo')
    def test_save_game_with_no_active_game(self, mock_showinfo, mock_save):
        """Testet, dass das Speichern fehlschlägt, wenn kein Spiel läuft."""
        self.app.game_instance = None

        self.app.save_game()

        mock_save.assert_not_called()
        mock_showinfo.assert_called_once_with(
            "Spiel speichern",
            "Es läuft kein aktives Spiel, das gespeichert werden könnte.",
            parent=self.app.root
        )

    @patch('main.SaveLoadManager.save_game_state')
    def test_save_game_with_active_game(self, mock_save):
        """Testet, dass die Speichern-Funktion bei einem aktiven Spiel aufgerufen wird."""
        # Ein Mock-Spiel mit einem Mock-Dartboard erstellen
        self.app.game_instance = MagicMock(spec=Game)
        self.app.game_instance.end = False
        self.app.game_instance.db = MagicMock() # Dartboard muss existieren

        self.app.save_game()

        mock_save.assert_called_once_with(self.app.game_instance, self.app.root)

    @patch('tkinter.messagebox.askyesno', return_value=True)
    def test_quit_game_confirmed(self, mock_askyesno):
        """Testet, ob die Anwendung bei Bestätigung beendet wird."""
        # Mocken die Methoden, die innerhalb von quit_game aufgerufen werden
        self.app.root.quit = MagicMock()
        self.app.settings_manager.save_settings = MagicMock()

        # Rufen die zu testende Methode direkt auf
        self.app.quit_game()

        mock_askyesno.assert_called_once()
        self.app.settings_manager.save_settings.assert_called_once()
        self.app.root.quit.assert_called_once()

    def test_show_highscores_calls_manager(self):
        """Testet, ob das Anzeigen der Highscores an den Manager delegiert wird."""
        self.app.highscore_manager.show_highscores_window = MagicMock()
        self.app.show_highscores()
        self.app.highscore_manager.show_highscores_window.assert_called_once_with(self.app.root)

    def test_show_player_stats_calls_manager(self):
        """Testet, ob das Anzeigen der Statistiken an den Manager delegiert wird."""
        self.app.player_stats_manager.show_stats_window = MagicMock()
        self.app.show_player_stats()
        self.app.player_stats_manager.show_stats_window.assert_called_once_with(self.app.root)

if __name__ == '__main__':
    unittest.main(verbosity=2)