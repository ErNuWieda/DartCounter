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
from unittest.mock import patch, MagicMock, mock_open, ANY
import json

# Klasse, die getestet wird
from core.save_load_manager import SaveLoadManager

# Klassen, die als Abhängigkeiten gemockt werden
from core.game import Game
from core.game_options import GameOptions
from core.player import Player


@pytest.fixture
def slm_setup(monkeypatch):
    """
    Eine pytest-Fixture, die eine Testumgebung für den SaveLoadManager einrichtet.
    Erstellt ein gemocktes Spiel mit Spielern und patcht UI-Abhängigkeiten.
    """
    # Mock für ein Game-Objekt mit Spielern und Daten
    mock_game = MagicMock(spec=Game)
    mock_game.current = 1
    mock_game.round = 5
    # Das Game-Objekt hat jetzt ein 'options'-Attribut
    mock_game.options = GameOptions(
        name="501",
        opt_in="Double",
        opt_out="Double",
        opt_atc="Single",
        count_to=501,
        lifes=3,
        rounds=7,
        legs_to_win=1,
        sets_to_win=1,
    )
    mock_game.is_leg_set_match = False  # Wichtig für den Restore-Test

    mock_player1 = MagicMock(spec=Player)
    mock_player1.name = "P1"
    mock_player1.id = 1
    mock_player1.score = 140
    mock_player1.throws = [("Triple", 20, None)]
    mock_player1.stats = {"total_darts_thrown": 10}
    mock_player1.state = {
        "has_opened": True,
        "hits": {},
    }  # Muss ein serialisierbares Dict sein
    mock_player1.sb = MagicMock()

    mock_player2 = MagicMock(spec=Player)
    mock_player2.name = "P2"
    mock_player2.id = 2
    mock_player2.score = 200
    mock_player2.throws = []
    mock_player2.stats = {"total_darts_thrown": 9}
    mock_player2.state = {
        "has_opened": True,
        "hits": {},
    }  # Muss ein serialisierbares Dict sein
    mock_player2.sb = MagicMock()

    mock_game.players = [mock_player1, mock_player2]

    # Mock für das Parent-Fenster (für Dialoge)
    mock_parent = MagicMock()

    # Patch für messagebox, um UI-Popups zu verhindern
    mock_ui_utils = MagicMock()
    monkeypatch.setattr("core.save_load_manager.ui_utils", mock_ui_utils)

    return mock_game, mock_parent, mock_ui_utils


@patch(
    "core.save_load_manager.filedialog.asksaveasfilename",
    return_value="/dummy/path/save.json",
)
@patch("core.save_load_manager.JsonIOHandler.write_json", return_value=True)
def test_save_state_success(mock_write_json, mock_asksaveasfilename, slm_setup):
    """Testet den erfolgreichen Speichervorgang."""
    mock_game, mock_parent, mock_ui_utils = slm_setup
    # Konfiguriere die Mocks, damit sie serialisierbare Daten zurückgeben
    mock_game.to_dict.return_value = {
        "name": "501",
        "opt_out": "Double",
        "current_player_index": 1,
        "players": [{"name": "P1", "score": 140, "state": {"has_opened": True}}],
    }
    mock_game.get_save_meta.return_value = {
        "title": "Test Save",
        "filetypes": (("All", "*.*"),),
        "defaultextension": ".json",
        "save_type": "game",
    }

    result = SaveLoadManager.save_state(mock_game, mock_parent)

    assert result is True
    mock_asksaveasfilename.assert_called_once()
    mock_write_json.assert_called_once()

    # Überprüfen, ob write_json mit den korrekten, gesammelten Daten aufgerufen wurde
    saved_data = mock_write_json.call_args.kwargs["data"]
    assert saved_data["name"] == "501"
    assert saved_data["opt_out"] == "Double"
    assert saved_data["save_format_version"] == SaveLoadManager.SAVE_FORMAT_VERSION

    # Die Erfolgsmeldung wird jetzt vom JsonIOHandler angezeigt
    # mock_ui_utils.show_message.assert_called_once_with('info', ANY, ANY, parent=mock_parent)


@patch("core.save_load_manager.filedialog.asksaveasfilename", return_value="")
def test_save_state_cancelled(mock_asksaveasfilename, slm_setup):
    """Testet, was passiert, wenn der Benutzer den Speicherdialog abbricht."""
    mock_game, mock_parent, mock_ui_utils = slm_setup
    result = SaveLoadManager.save_state(mock_game, mock_parent)
    assert result is False
    mock_asksaveasfilename.assert_called_once()
    mock_ui_utils.show_message.assert_not_called()


@patch(
    "core.save_load_manager.filedialog.askopenfilename",
    return_value="/dummy/path/load.json",
)
@patch("core.save_load_manager.JsonIOHandler.read_json")
def test_load_game_data_success(mock_read_json, mock_askopenfilename, slm_setup):
    """Testet den erfolgreichen Ladevorgang."""
    _, mock_parent, mock_ui_utils = slm_setup
    mock_data_content = {
        "save_format_version": SaveLoadManager.SAVE_FORMAT_VERSION,
        "save_type": SaveLoadManager.GAME_SAVE_TYPE,
        "name": "301",
        "players": [{"name": "P1"}],
    }
    # Füge einen gültigen Checksum hinzu
    checksum = SaveLoadManager._calculate_checksum(mock_data_content)
    mock_data_with_checksum = {**mock_data_content, "checksum": checksum}
    mock_read_json.return_value = mock_data_with_checksum

    result = SaveLoadManager.load_game_data(mock_parent)

    assert result == mock_data_content
    mock_askopenfilename.assert_called_once()
    mock_read_json.assert_called_once()
    mock_ui_utils.show_message.assert_not_called()


@patch("core.save_load_manager.JsonIOHandler.read_json")
def test_load_game_data_version_mismatch(mock_read_json, slm_setup):
    """Testet, ob eine inkompatible Speicherversion korrekt abgelehnt wird."""
    _, mock_parent, mock_ui_utils = slm_setup
    mock_data_content = {
        "save_format_version": 999,  # Zukünftige Version
        "save_type": "game",
        "name": "301",
    }
    checksum = SaveLoadManager._calculate_checksum(mock_data_content)
    mock_data_with_checksum = {**mock_data_content, "checksum": checksum}
    mock_read_json.return_value = mock_data_with_checksum

    # Da der Dateidialog nicht gemockt ist, müssen wir den read_json-Aufruf direkt testen
    with patch(
        "core.save_load_manager.filedialog.askopenfilename",
        return_value="/dummy/path/load.json",
    ):
        result = SaveLoadManager.load_game_data(mock_parent)

    assert result is None
    mock_ui_utils.show_message.assert_called_once_with(
        "error", "Inkompatibler Spielstand", ANY, parent=mock_parent
    )


def test_restore_game_state(slm_setup):
    """Testet, ob der Spielzustand korrekt aus den geladenen Daten wiederhergestellt wird."""
    mock_game, _, _ = slm_setup

    loaded_data = {
        "round": 10,
        "current_player_index": 1,
        "players": [
            {
                "name": "P1_loaded",
                "id": 1,
                "score": 50,
                "throws": [("T", 20, None)],
                "stats": {"s1": 1},
                "state": {"hits": {"20": 1}},
            },
            {
                "name": "P2_loaded",
                "id": 2,
                "score": 75,
                "throws": [],
                "stats": {"s2": 2},
                "state": {"hits": {"19": 2}},
            },
        ],
    }
    player1, player2 = mock_game.players

    # Teste den 'else'-Zweig für player1 (hat kein update_display)
    del player1.sb.update_display

    # Rufe die Funktion erst auf, nachdem die Mocks konfiguriert sind
    SaveLoadManager.restore_game_state(mock_game, loaded_data)

    assert mock_game.round == 10
    assert mock_game.current == 1

    assert player1.name == "P1_loaded"
    assert player1.score == 50
    assert player1.state["hits"] == {"20": 1}
    player1.sb.update_score.assert_called_once_with(50)

    # Teste den 'if'-Zweig für player2 (hat update_display)
    player2.sb.update_display.assert_called_once_with({"19": 2}, 75)
