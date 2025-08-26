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

import os
import sys
import logging
import tkinter as tk
import pytest
from unittest.mock import MagicMock
from core.game_options import GameOptions
# Wichtig: Wir müssen die zu testenden Klassen importieren.
from core.game import Game
# --- One-time setup for all tests, executed by pytest before test collection ---

# Workaround for TclError on Windows in venv
# In some environments (like Windows virtualenvs), the Python interpreter
# can't find the Tcl/Tk libraries. This block manually sets the
# environment variables to point to the correct location within the
# Python installation directory before any Tkinter modules are imported.
if sys.platform == "win32":  # "win32" is the value for both 32-bit and 64-bit Windows
    # In a venv, sys.prefix points to the venv dir, but the Tcl/Tk libs are
    # in the base Python installation. sys.base_prefix correctly points there.
    tcl_dir = os.path.join(sys.base_prefix, 'tcl')
    if os.path.isdir(tcl_dir):
        # Find the specific tcl8.x and tk8.x directories
        for d in os.listdir(tcl_dir):
            lib_path = os.path.join(tcl_dir, d)
            if os.path.isdir(lib_path):
                if d.startswith('tcl8.') and "TCL_LIBRARY" not in os.environ:
                    os.environ['TCL_LIBRARY'] = lib_path
                elif d.startswith('tk8.') and "TK_LIBRARY" not in os.environ:
                    os.environ['TK_LIBRARY'] = lib_path

def pytest_configure(config):
    """
    Konfiguriert das Logging für die Test-Suite, um die Konsolenausgabe zu unterdrücken.

    Diese Funktion wird von pytest automatisch vor der Testausführung aufgerufen.
    """
    # Hole den Root-Logger, auf dem die Handler in `logger_setup.py` konfiguriert werden.
    root_logger = logging.getLogger()

    # Entferne alle existierenden Handler, um eine saubere Konfiguration zu gewährleisten.
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Füge einen NullHandler hinzu. Dieser "schluckt" alle Log-Nachrichten,
    # ohne sie auszugeben. Dies verhindert, dass Anwendungs-Logs die Testausgabe stören.
    root_logger.addHandler(logging.NullHandler())

@pytest.fixture
def mock_game():
    """
    Eine Fixture, die eine generische, gemockte Game-Instanz bereitstellt.
    Ersetzt die setUp-Logik aus der alten GameLogicTestBase.
    """
    game = MagicMock(spec=Game)
    game.round = 1
    game.end = False
    game.highscore_manager = MagicMock()
    game.sound_manager = MagicMock()
    game.targets = [] # Standard-Fallback
    # Füge das gemockte options-Objekt hinzu, das nach dem Refactoring erforderlich ist.
    # Wichtig: Die Attribute müssen konkrete Werte haben, um TypeErrors zu vermeiden.
    game.options = MagicMock()
    game.options.name = "Test Game"
    game.options.lifes = 3
    game.options.rounds = 7
    game.options.count_to = 301
    game.options.opt_in = "Single"
    game.options.opt_out = "Single"
    game.options.legs_to_win = 1
    game.options.sets_to_win = 1
    # Füge ein gemocktes Logik-Objekt hinzu, das von UI-Komponenten erwartet wird
    game.game = MagicMock()
    game.game.get_scoreboard_height.return_value = 400

    def _get_score_side_effect(ring, segment):
        """Simuliert die get_score Methode der Game-Klasse für die Tests."""
        if ring == "Bullseye": return 50
        if ring == "Bull": return 25

        try:
            segment_val = int(segment)
        except (ValueError, TypeError):
            return 0 # Ungültiges Segment wie 'Miss'

        if ring == "Triple": return segment * 3
        if ring == "Double": return segment * 2
        if ring == "Single": return segment
        return 0

    game.get_score.side_effect = _get_score_side_effect
    return game

@pytest.fixture(scope="session")
def tk_root_session():
    """Erstellt eine einzige, versteckte Tk-Wurzel für die gesamte Test-Session."""
    root = tk.Tk()
    root.withdraw()
    yield root
    if root and root.winfo_exists():
        root.destroy()

@pytest.fixture
def game_factory(tk_root_session, monkeypatch):
    """
    Eine Factory-Fixture zum Erstellen von echten Game-Instanzen mit gemockten Abhängigkeiten.
    Dies ist die zentrale Fixture für alle Integrationstests.
    """
    created_games = []

    def _create_game(game_options_dict: dict, player_names: list[str]):
        # Mock all external dependencies
        monkeypatch.setattr('core.game.ui_utils.show_message', MagicMock())
        monkeypatch.setattr('core.game.ui_utils.ask_question', MagicMock())
        
        # Mock managers
        mock_highscore_manager = MagicMock()
        mock_player_stats_manager = MagicMock()
        mock_profile_manager = MagicMock()
        mock_profile_manager.get_profile_by_name.return_value = None # Default behavior

        # Mock UI components that Game creates
        monkeypatch.setattr('core.game.DartBoard', MagicMock())
        monkeypatch.setattr('core.game.setup_scoreboards', MagicMock(return_value=[]))

        game_options = GameOptions.from_dict(game_options_dict)
        
        game = Game(
            tk_root_session, game_options, player_names,
            on_throw_processed_callback=MagicMock(),
            highscore_manager=mock_highscore_manager, 
            player_stats_manager=mock_player_stats_manager,
            profile_manager=mock_profile_manager
        )
        created_games.append(game)
        return game

    yield _create_game

    for game in created_games:
        if game:
            game.destroy()
