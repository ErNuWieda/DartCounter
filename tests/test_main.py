# Dartcounter Deluxe
# Copyright (C) 2025 Martin Hehl (airnooweeda)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pytest
from unittest.mock import patch, MagicMock
import pathlib

# Wichtig: Wir müssen die zu testenden Klassen und Funktionen importieren.
from main import App, get_asset_path

# Wir müssen auch die Klassen importieren, die wir mocken wollen,
# damit 'isinstance' in den Tests funktioniert.
from core.game import Game
from core.tournament_manager import TournamentManager


# --- Tests for get_asset_path ---

@patch('main.sys.hasattr', return_value=False)
def test_get_asset_path_dev_mode(mock_hasattr):
    """Testet den Pfad im normalen Entwicklungsmodus."""
    path = get_asset_path(pathlib.Path("assets/test.png"))
    assert str(path).endswith(str(pathlib.Path('assets/test.png')))

@patch('main.sys.hasattr', return_value=True)
@patch('main.sys._MEIPASS', '/tmp/_MEI12345', create=True)
def test_get_asset_path_pyinstaller_mode(mock_hasattr):
    """Testet den Pfad, wenn die Anwendung gepackt ist (PyInstaller)."""
    path = get_asset_path(pathlib.Path("assets/test.png"))
    assert str(path) == str(pathlib.Path('/tmp/_MEI12345/assets/test.png'))


# --- Fixture for App tests ---

@pytest.fixture
def app_with_mocks():
    """
    Eine pytest-Fixture, die die App-Instanz mit allen notwendigen Mocks einrichtet.
    Dies ersetzt die repetitive setUp-Methode aus unittest.
    """
    patches = {
        'sv_ttk_set_theme': patch('main.sv_ttk.set_theme'),
        'image_open': patch('main.Image.open'),
        'image_tk': patch('main.ImageTk.PhotoImage'),
        'canvas': patch('main.tk.Canvas'),
        'menu': patch('main.tk.Menu'),
        'ui_utils': patch('main.ui_utils'),
        'game_manager': patch('main.GameManager'),
        'save_load_manager': patch('main.SaveLoadManager'),
        'highscore_manager': patch('main.HighscoreManager'),
        'player_stats_manager': patch('main.PlayerStatsManager'),
        'app_settings_dialog': patch('main.AppSettingsDialog'),
        'tournament_view': patch('main.TournamentView'),
        'tournament_manager_from_dict': patch('main.TournamentManager.from_dict'),
    }
    
    mocks = {name: p.start() for name, p in patches.items()}
    mock_root = MagicMock()
    app_instance = App(mock_root)
    
    yield app_instance, mocks
    
    for p in patches.values():
        p.stop()


# --- App Tests ---

def test_initialization(app_with_mocks):
    """Testet, ob die App korrekt mit all ihren Managern initialisiert wird."""
    app, _ = app_with_mocks
    assert app.settings_manager is not None
    assert app.sound_manager is not None
    assert app.highscore_manager is not None
    assert app.player_stats_manager is not None
    assert app.game_instance is None
    with patch('main.__version__', "9.9.9"):
        re_app = App(MagicMock())
        assert re_app.version == "v9.9.9"

@patch('main.App._initialize_game_session')
def test_new_game_starts_successfully(mock_init_session, app_with_mocks):
    """Testet den 'Neues Spiel'-Workflow, wenn der Benutzer das Spiel startet."""
    app, mocks = app_with_mocks
    mock_game_manager = mocks['game_manager']

    mock_gm_instance = mock_game_manager.return_value
    mock_gm_instance.configure_game.return_value = True
    mock_gm_instance.game = "501"
    mock_gm_instance.players = ["Player 1"]

    mock_game_instance = MagicMock(spec=Game)
    mock_game_instance.ui = MagicMock()
    mock_game_instance.ui.db.root = MagicMock()
    mock_init_session.return_value = mock_game_instance

    app.new_game()

    mock_game_manager.assert_called_once_with(app.sound_manager, app.settings_manager, app.profile_manager)
    mock_gm_instance.configure_game.assert_called_once_with(app.root)
    mock_init_session.assert_called_once()
    assert app.game_instance is not None
    app.root.wait_window.assert_called_once_with(mock_game_instance.ui.db.root)

@patch('main.App._initialize_game_session')
def test_new_game_aborted_by_user(mock_init_session, app_with_mocks):
    """Testet den 'Neues Spiel'-Workflow, wenn der Benutzer den Dialog abbricht."""
    app, mocks = app_with_mocks
    mock_game_manager = mocks['game_manager']

    mock_gm_instance = mock_game_manager.return_value
    mock_gm_instance.configure_game.return_value = False

    app.new_game()

    mock_game_manager.assert_called_once_with(app.sound_manager, app.settings_manager, app.profile_manager)
    mock_gm_instance.configure_game.assert_called_once_with(app.root)
    mock_init_session.assert_not_called()
    app.root.wait_window.assert_not_called()
    assert app.game_instance is None

def test_check_and_close_existing_game_confirmed(app_with_mocks):
    """Testet, ob ein laufendes Spiel beendet wird, wenn der Benutzer bestätigt."""
    app, mocks = app_with_mocks
    mock_ui_utils = mocks['ui_utils']
    mock_ui_utils.ask_question.return_value = True

    mock_game = MagicMock(spec=Game)
    mock_game.end = False
    app.game_instance = mock_game

    result = app._check_and_close_existing_game("Titel", "Nachricht")

    mock_ui_utils.ask_question.assert_called_once()
    mock_game.destroy.assert_called_once()
    assert app.game_instance is None
    assert result is True

def test_check_and_close_existing_game_cancelled(app_with_mocks):
    """Testet, ob ein laufendes Spiel NICHT beendet wird, wenn der Benutzer abbricht."""
    app, mocks = app_with_mocks
    mock_ui_utils = mocks['ui_utils']
    mock_ui_utils.ask_question.return_value = False

    mock_game = MagicMock(spec=Game)
    mock_game.end = False
    app.game_instance = mock_game

    result = app._check_and_close_existing_game("Titel", "Nachricht")

    mock_ui_utils.ask_question.assert_called_once()
    mock_game.destroy.assert_not_called()
    assert app.game_instance is not None
    assert result is False

@patch('main.App._check_and_close_existing_game', return_value=True)
@patch('main.App._initialize_game_session')
def test_load_game_successful(mock_init_session, mock_check_close, app_with_mocks):
    """Testet den erfolgreichen Ladevorgang eines Spiels."""
    app, mocks = app_with_mocks
    mock_slm = mocks['save_load_manager']
    mock_load_data = mock_slm.load_game_data
    mock_restore = mock_slm.restore_game_state

    mock_data = {
        'save_type': 'game',
        'game_name': '301', 'opt_in': 'Single', 'opt_out': 'Double',
        'opt_atc': 'Single', 'count_to': '301', 'lifes': '3', 'rounds': '7',
        'players': [{'name': 'P1'}]
    }
    mock_load_data.return_value = mock_data

    mock_game_instance = MagicMock(spec=Game)
    mock_game_instance.ui = MagicMock()
    mock_game_instance.ui.db.root = MagicMock()
    mock_init_session.return_value = mock_game_instance

    app.load_game()

    mock_check_close.assert_called_once()
    mock_load_data.assert_called_once_with(app.root)
    mock_init_session.assert_called_once()
    mock_restore.assert_called_once_with(mock_game_instance, mock_data)
    assert app.game_instance == mock_game_instance
    app.root.wait_window.assert_called_once_with(mock_game_instance.ui.db.root)

def test_save_game_with_no_active_game(app_with_mocks):
    """Testet, dass das Speichern fehlschlägt, wenn kein Spiel läuft."""
    app, mocks = app_with_mocks
    mock_save = mocks['save_load_manager'].save_game_state
    mock_showinfo = mocks['ui_utils'].show_message

    app.game_instance = None
    app.save_game()

    mock_save.assert_not_called()
    mock_showinfo.assert_called_once_with(
        'info', "Spiel speichern", "Es läuft kein aktives Spiel, das gespeichert werden könnte.", parent=app.root
    )

def test_save_game_with_active_game(app_with_mocks):
    """Testet, dass die Speichern-Funktion bei einem aktiven Spiel aufgerufen wird."""
    app, mocks = app_with_mocks
    mock_save = mocks['save_load_manager'].save_game_state

    app.game_instance = MagicMock(spec=Game)
    app.game_instance.end = False
    app.game_instance.ui = MagicMock()
    app.game_instance.ui.db = MagicMock()

    app.save_game()

    mock_save.assert_called_once_with(app.game_instance, app.root)

def test_quit_game_confirmed(app_with_mocks):
    """Testet, ob die Anwendung bei Bestätigung beendet wird."""
    app, mocks = app_with_mocks
    mock_ask_question = mocks['ui_utils'].ask_question
    mock_ask_question.return_value = True

    app.root.quit = MagicMock()
    app.settings_manager.save_settings = MagicMock()
    app.db_manager.close_connection = MagicMock()

    app.quit_game()

    mock_ask_question.assert_called_once_with('yesno', "Programm beenden", "DartCounter wirklich beenden?", parent=app.root)
    app.settings_manager.save_settings.assert_called_once()
    app.db_manager.close_connection.assert_called_once()
    app.root.quit.assert_called_once()

def test_show_highscores_calls_manager(app_with_mocks):
    """Testet, ob das Anzeigen der Highscores an den Manager delegiert wird."""
    app, mocks = app_with_mocks
    mock_highscore_manager = mocks['highscore_manager']
    app.highscore_manager = mock_highscore_manager

    app.show_highscores()
    mock_highscore_manager.show_highscores_window.assert_called_once_with(app.root)

def test_show_player_stats_calls_manager(app_with_mocks):
    """Testet, ob das Anzeigen der Statistiken an den Manager delegiert wird."""
    app, mocks = app_with_mocks
    mock_player_stats_manager = mocks['player_stats_manager']
    app.player_stats_manager = mock_player_stats_manager

    app.show_player_stats()
    mock_player_stats_manager.show_stats_window.assert_called_once_with(app.root)


# --- Tournament Flow Tests ---

def test_save_tournament_with_active_tournament(app_with_mocks):
    """Testet, dass save_tournament den Manager aufruft, wenn ein Turnier aktiv ist."""
    app, mocks = app_with_mocks
    mock_save = mocks['save_load_manager'].save_tournament_state
    mock_show_message = mocks['ui_utils'].show_message

    app.tournament_manager = MagicMock(spec=TournamentManager)
    app.tournament_manager.is_finished = False

    app.save_tournament()

    mock_save.assert_called_once_with(app.tournament_manager, app.root)
    mock_show_message.assert_not_called()

def test_save_tournament_with_no_active_tournament(app_with_mocks):
    """Testet, dass save_tournament eine Nachricht anzeigt, wenn kein Turnier aktiv ist."""
    app, mocks = app_with_mocks
    mock_save = mocks['save_load_manager'].save_tournament_state
    mock_show_message = mocks['ui_utils'].show_message

    app.tournament_manager = None
    app.save_tournament()

    mock_save.assert_not_called()
    mock_show_message.assert_called_once()

@patch('main.App._check_and_close_existing_game', return_value=True)
def test_load_tournament_successful(mock_check_close, app_with_mocks):
    """Testet den erfolgreichen Ladevorgang eines Turniers."""
    app, mocks = app_with_mocks
    mock_load_data = mocks['save_load_manager'].load_tournament_data
    mock_from_dict = mocks['tournament_manager_from_dict']
    mock_view_class = mocks['tournament_view']

    mock_data = {'some': 'data'}
    mock_load_data.return_value = mock_data
    mock_tm_instance = MagicMock(spec=TournamentManager)
    mock_from_dict.return_value = mock_tm_instance

    app.load_tournament()

    mock_check_close.assert_called_once()
    mock_load_data.assert_called_once_with(app.root)
    mock_from_dict.assert_called_once_with(mock_data)
    assert app.tournament_manager == mock_tm_instance
    mock_view_class.assert_called_once_with(app.root, mock_tm_instance, app.start_next_tournament_match)
    assert app.tournament_view is not None