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
from unittest.mock import MagicMock, ANY

# Import the class to be tested AND the dictionary to be patched
from core.game import Game, GAME_LOGIC_MAP
from core.game_options import GameOptions
# Import classes that are dependencies and will be mocked
from core.player import Player


@pytest.fixture
def game_with_mocks(monkeypatch):
    """
    Eine pytest-Fixture, die eine Game-Instanz mit allen notwendigen Mocks einrichtet.
    Ersetzt die komplexe setUp-Methode aus der unittest-Version.
    """
    # Mock für die X01-Klasse
    mock_x01_class = MagicMock()
    # Patch the dictionary directly by importing it
    monkeypatch.setitem(GAME_LOGIC_MAP, '301', mock_x01_class)

    # Mock für UI-Utilities und GameUI
    mock_ui_utils = MagicMock()
    monkeypatch.setattr('core.game.ui_utils', mock_ui_utils)

    # Mock die gesamte UI-Setup-Funktion, um TclError zu vermeiden.
    # Weisen jedem Spieler ein Mock-Scoreboard zu.
    def mock_setup_scoreboards(game_controller):
        for p in game_controller.players:
            p.sb = MagicMock()
        return [] # Gibt eine leere Liste zurück, da wir die SBs nicht brauchen
    monkeypatch.setattr('core.game.setup_scoreboards', mock_setup_scoreboards)
    monkeypatch.setattr('core.game.DartBoard', MagicMock())
    
    # Konfiguration für das Spiel
    game_options_dict = {
        'name': '301', 'opt_in': 'Single', 'opt_out': 'Single', 'opt_atc': 'Single',
        'count_to': 301, 'lifes': 3, 'rounds': 7
    }
    player_names = ["Alice", "Bob"]

    # Mock-Spieler-Instanzen
    mock_players = []
    for i, name in enumerate(player_names):
        player = MagicMock(spec=Player)
        player.name = name
        player.id = i + 1
        player.throws = []
        player.sb = MagicMock()
        player.reset_turn = MagicMock()
        player.profile = None
        mock_players.append(player)

    # Patch die Player-Klasse
    monkeypatch.setattr('core.game.Player', MagicMock(side_effect=mock_players))

    # Initialisiere die Game-Klasse
    game = Game(
        root=MagicMock(),
        game_options=GameOptions.from_dict(game_options_dict),
        player_names=player_names,
        sound_manager=MagicMock(),
        highscore_manager=MagicMock(),
        player_stats_manager=MagicMock(),
        profile_manager=MagicMock()
    )

    # Weisen die erstellten Mock-Spieler der Instanz zu
    game.players = mock_players
    # Mock die Methode, die UI-Interaktionen auslöst
    game.announce_current_player_turn = MagicMock()

    # Gib die game-Instanz und die Mocks für die Tests zurück
    return game, {'ui_utils': mock_ui_utils, 'x01_class': mock_x01_class}


def test_initialization(game_with_mocks):
    """Testet, ob das Spiel korrekt initialisiert wird."""
    game, mocks = game_with_mocks
    assert len(game.players) == 2
    assert game.players[0].name == "Alice"
    assert game.current == 0
    assert game.round == 1
    assert not game.end
    # Prüfen, ob die Spiellogik-Klasse (X01) instanziiert wurde
    mocks['x01_class'].assert_called_once_with(game)


def test_current_player_returns_correct_player(game_with_mocks):
    """Testet, ob current_player() den richtigen Spieler zurückgibt."""
    game, _ = game_with_mocks
    game.current = 0
    assert game.current_player() == game.players[0]

    game.current = 1
    assert game.current_player() == game.players[1]


def test_next_player_advances_turn(game_with_mocks):
    """Testet den einfachen Wechsel zum nächsten Spieler innerhalb einer Runde."""
    game, _ = game_with_mocks
    player1 = game.current_player()
    
    game.next_player()

    assert game.current == 1
    assert game.round == 1
    player1.reset_turn.assert_called_once()
    game.announce_current_player_turn.assert_called_once()


def test_next_player_increments_round(game_with_mocks):
    """Testet, ob die Runde erhöht wird, wenn der letzte Spieler seinen Zug beendet."""
    game, _ = game_with_mocks
    game.current = len(game.players) - 1 # Setze auf den letzten Spieler (Bob)
    last_player = game.current_player()

    game.next_player()

    assert game.current == 0
    assert game.round == 2
    last_player.reset_turn.assert_called_once()
    game.announce_current_player_turn.assert_called_once()


def test_leave_game_current_player_advances_turn(game_with_mocks):
    """Testet, was passiert, wenn der aktuelle Spieler das Spiel verlässt."""
    game, _ = game_with_mocks
    player_to_leave = game.players[0]
    
    game.leave(player_to_leave)

    assert len(game.players) == 1
    assert player_to_leave not in game.players
    assert game.current == 0
    assert game.players[0].name == "Bob"
    game.announce_current_player_turn.assert_called_once()


def test_leave_game_non_current_player_adjusts_index(game_with_mocks):
    """Testet das Verlassen eines Spielers, der nicht am Zug ist."""
    game, _ = game_with_mocks
    game.current = 1 # Bob ist am Zug
    player_to_leave = game.players[0] # Alice verlässt das Spiel

    game.leave(player_to_leave)

    assert len(game.players) == 1
    assert player_to_leave not in game.players
    assert game.current == 0
    game.announce_current_player_turn.assert_not_called()


def test_leave_game_last_player_ends_game(game_with_mocks):
    """Testet, ob das Spiel endet, wenn der letzte Spieler geht."""
    game, mocks = game_with_mocks
    # Reduziere die Spielerliste auf einen
    game.players = [game.players[0]]
    game.current = 0
    player_to_leave = game.players[0]
    # Mock die destroy-Methode, um ihren Aufruf zu prüfen
    game.destroy = MagicMock()

    game.leave(player_to_leave)

    assert len(game.players) == 0
    assert game.end is True
    mocks['ui_utils'].show_message.assert_called_once_with(
        'info', "Spielende", "Alle Spieler haben das Spiel verlassen.", parent=ANY
    )
    game.destroy.assert_called_once()