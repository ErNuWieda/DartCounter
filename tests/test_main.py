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
from core.tournament_manager import TournamentManager

# --- Module-level Tkinter setup ---
# To prevent Tcl/Tk interpreter errors on Windows when creating and destroying
# multiple root windows in the same test run, we create a single root window
# for the entire test module.
_module_root = None

def setUpModule():
    """Create a single Tk root for the entire module."""
    global _module_root
    _module_root = tk.Tk()
    _module_root.geometry("+5000+5000")

def tearDownModule():
    """Destroy the single Tk root after all tests in the module have run."""
    if _module_root:
        _module_root.destroy()

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
        """Setzt eine Testumgebung für jeden Test auf."""
        self.app = App(_module_root)

    def tearDown(self):
        """Räumt nach jedem Test auf."""
        # Die App-Instanz wird in jedem setUp neu erstellt. Die Wurzel wird in tearDownModule zerstört.
        pass

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
    @patch.object(tk.Tk, 'wait_window') # Fängt den Aufruf von self.root.wait_window ab
    def test_new_game_starts_successfully(self, mock_wait_window, mock_init_session, mock_game_manager):
        """Testet den 'Neues Spiel'-Workflow, wenn der Benutzer das Spiel startet."""
        # Konfiguriere den Mock für GameManager
        mock_gm_instance = mock_game_manager.return_value
        mock_gm_instance.configure_game.return_value = True # Simuliert, dass der User "Start" klickt
        mock_gm_instance.game = "501"
        mock_gm_instance.players = ["Player 1"]

        # Konfiguriere das Mock-Spiel, um die 'db.root'-Struktur zu haben.
        # Wir erstellen explizit einen Mock mit spec=Game für mehr Testsicherheit,
        # analog zum Test 'test_load_game_successful'.
        mock_game_instance = MagicMock(spec=Game)
        mock_init_session.return_value = mock_game_instance
        mock_game_instance.db = MagicMock()
        mock_game_instance.db.root = MagicMock()

        self.app.new_game()

        # Prüfen, ob der GameManager aufgerufen wurde
        mock_game_manager.assert_called_once_with(self.app.sound_manager, self.app.settings_manager, self.app.profile_manager)
        # Prüfen, ob die Konfigurationsmethode aufgerufen wurde
        mock_gm_instance.configure_game.assert_called_once_with(self.app.root)
        # Prüfen, ob die Spiel-Session mit den korrekten Optionen initialisiert wurde
        mock_init_session.assert_called_once()
        # Prüfen, ob die game_instance gesetzt wurde
        self.assertIsNotNone(self.app.game_instance)
        # Prüfen, ob auf das (gemockte) Spielfenster gewartet wurde
        mock_wait_window.assert_called_once_with(mock_game_instance.db.root)

    @patch('main.GameManager')
    @patch('main.App._initialize_game_session')
    @patch.object(tk.Tk, 'wait_window') # Muss auch hier gepatcht werden, obwohl nicht erwartet
    def test_new_game_aborted_by_user(self, mock_wait_window, mock_init_session, mock_game_manager):
        """Testet den 'Neues Spiel'-Workflow, wenn der Benutzer den Dialog abbricht."""
        mock_gm_instance = mock_game_manager.return_value
        mock_gm_instance.configure_game.return_value = False # Simuliert, dass der User den Dialog abbricht

        self.app.new_game()

        mock_game_manager.assert_called_once_with(self.app.sound_manager, self.app.settings_manager, self.app.profile_manager)
        mock_gm_instance.configure_game.assert_called_once_with(self.app.root)
        # Die Spiel-Session darf nicht initialisiert worden sein
        mock_init_session.assert_not_called()
        mock_wait_window.assert_not_called()
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
    @patch('main.App._initialize_game_session') # Geändert: return_value entfernt, um Test-Isolation zu gewährleisten
    @patch('main.SaveLoadManager.restore_game_state')
    @patch.object(tk.Tk, 'wait_window') # Fängt den Aufruf von self.root.wait_window ab
    def test_load_game_successful(self, mock_wait_window, mock_restore, mock_init_session, mock_load_data): # Reihenfolge der Mocks ist wichtig!
        """Testet den erfolgreichen Ladevorgang eines Spiels."""
        # Simuliere geladene Spieldaten
        mock_data = {
            'save_type': 'game', # Notwendig für die Validierung
            'game_name': '301', 'opt_in': 'Single', 'opt_out': 'Double',
            'opt_atc': 'Single', 'count_to': '301', 'lifes': '3', 'rounds': '7',
            'players': [{'name': 'P1'}]
        }
        mock_load_data.return_value = mock_data

        # Erstelle eine NEUE, saubere Mock-Instanz für das Spiel für DIESEN Test.
        # Dies ist der Kern der Fehlerbehebung, um Seiteneffekte zu vermeiden.
        mock_game_instance = MagicMock(spec=Game)
        mock_init_session.return_value = mock_game_instance

        # Konfiguriere das Mock-Spiel, um die 'db.root'-Struktur zu haben.
        # Das 'db'-Attribut muss explizit hinzugefügt werden, da es von 'spec'
        # als Instanzattribut nicht erkannt wird und der Zugriff sonst fehlschlägt.
        mock_game_instance.db = MagicMock()
        mock_game_instance.db.root = MagicMock()

        self.app.load_game()

        mock_load_data.assert_called_once_with(self.app.root)
        mock_init_session.assert_called_once()
        mock_restore.assert_called_once_with(mock_game_instance, mock_data)
        self.assertEqual(self.app.game_instance, mock_game_instance)
        mock_wait_window.assert_called_once_with(mock_game_instance.db.root)


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

class TestAppTournamentFlows(unittest.TestCase):
    """Tests the tournament-related workflows in the App class."""

    @patch('main.sv_ttk.set_theme')
    @patch('main.Image.open')
    @patch('main.ImageTk.PhotoImage')
    @patch('tkinter.Canvas')
    @patch('tkinter.Menu')
    def setUp(self, mock_menu, mock_canvas, mock_photo, mock_img_open, mock_theme):
        """Set up a test environment for each test."""
        self.app = App(_module_root)

    def tearDown(self):
        """Clean up after each test."""
        pass

    @patch('main.SaveLoadManager.save_tournament_state')
    @patch('tkinter.messagebox.showinfo')
    def test_save_tournament_with_active_tournament(self, mock_showinfo, mock_save):
        """Tests that save_tournament calls the manager when a tournament is active."""
        # Setup: Create a mock tournament manager and assign it
        self.app.tournament_manager = MagicMock(spec=TournamentManager)
        self.app.tournament_manager.is_finished = False

        # Action
        self.app.save_tournament()

        # Assert
        mock_save.assert_called_once_with(self.app.tournament_manager, self.app.root)
        mock_showinfo.assert_not_called()

    @patch('main.SaveLoadManager.save_tournament_state')
    @patch('tkinter.messagebox.showinfo')
    def test_save_tournament_with_no_active_tournament(self, mock_showinfo, mock_save):
        """Tests that save_tournament shows a message if no tournament is active."""
        # Setup: No tournament manager
        self.app.tournament_manager = None

        # Action
        self.app.save_tournament()

        # Assert
        mock_save.assert_not_called()
        mock_showinfo.assert_called_once()

    @patch('main.TournamentView')
    @patch('main.TournamentManager.from_dict')
    @patch('main.SaveLoadManager.load_tournament_data')
    @patch('main.App._check_and_close_existing_game', return_value=True)
    def test_load_tournament_successful(self, mock_check_close, mock_load_data, mock_from_dict, mock_view_class):
        """Tests the successful loading of a tournament."""
        # Setup
        mock_data = {'some': 'data'}
        mock_load_data.return_value = mock_data
        mock_tm_instance = MagicMock(spec=TournamentManager)
        mock_from_dict.return_value = mock_tm_instance

        # Action
        self.app.load_tournament()

        # Assert
        mock_check_close.assert_called_once()
        mock_load_data.assert_called_once_with(self.app.root)
        mock_from_dict.assert_called_once_with(mock_data)
        self.assertEqual(self.app.tournament_manager, mock_tm_instance)
        mock_view_class.assert_called_once_with(self.app.root, mock_tm_instance, self.app.start_next_tournament_match)
        self.assertIsNotNone(self.app.tournament_view)