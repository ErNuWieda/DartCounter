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
from unittest.mock import MagicMock

# Klasse, die getestet wird
from core.cricket import Cricket
# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player

# Die geteilte 'mock_game' Fixture ist automatisch aus conftest.py verfügbar.

@pytest.fixture
def cricket_logic(mock_game):
    """Erstellt eine Cricket-Logik-Instanz, konfiguriert für Standard-Cricket."""
    mock_game.name = "Cricket"
    logic = Cricket(mock_game)
    mock_game.targets = logic.get_targets()
    return logic

@pytest.fixture
def cut_throat_logic(mock_game):
    """Erstellt eine Cricket-Logik-Instanz, konfiguriert für Cut Throat."""
    mock_game.name = "Cut Throat"
    logic = Cricket(mock_game)
    mock_game.targets = logic.get_targets()
    return logic

@pytest.fixture
def players(mock_game, cricket_logic):
    """Erstellt eine Liste von zwei initialisierten Spielern für ein Standard-Cricket-Spiel."""
    player_list = []
    for i in range(2):
        p = Player(name=f"Player {i+1}", game=mock_game)
        cricket_logic.initialize_player_state(p)
        p.sb = MagicMock()
        player_list.append(p)
    return player_list

@pytest.fixture
def cut_throat_players(mock_game, cut_throat_logic):
    """Erstellt eine Liste von drei initialisierten Spielern für ein Cut-Throat-Spiel."""
    player_list = []
    for i in range(3):
        p = Player(name=f"Player {i+1}", game=mock_game)
        cut_throat_logic.initialize_player_state(p)
        p.sb = MagicMock()
        player_list.append(p)
    return player_list


def test_initialization(players):
    player1 = players[0]
    assert player1.score == 0
    assert player1.state['hits'].get("20") == 0
    assert "15" in player1.state['hits']
    assert "14" not in player1.state['hits']

def test_valid_hit_adds_marks(cricket_logic, players):
    player1 = players[0]
    status, _ = cricket_logic._handle_throw(player1, "Single", 20, players)
    assert player1.state['hits']["20"] == 1
    assert status == 'ok'
    
    status, _ = cricket_logic._handle_throw(player1, "Double", 20, players)
    assert player1.state['hits']["20"] == 3
    assert status == 'ok'

def test_hit_on_closed_target_scores_points(cricket_logic, players):
    player1, player2 = players
    player1.state['hits']["20"] = 3
    
    status, _ = cricket_logic._handle_throw(player1, "Single", 20, players)
    
    assert status == 'ok'
    assert player1.score == 20
    assert player2.score == 0

def test_no_points_if_all_opponents_closed_target(cricket_logic, players):
    player1, player2 = players
    player1.state['hits']["20"] = 3
    player2.state['hits']["20"] = 3

    status, _ = cricket_logic._handle_throw(player1, "Single", 20, players)
    
    assert status == 'ok'
    assert player1.score == 0

def test_bullseye_counts_as_two_marks(cricket_logic, players):
    player1 = players[0]
    assert player1.state['hits']["Bull"] == 0
    status, _ = cricket_logic._handle_throw(player1, "Bullseye", 50, players)
    assert player1.state['hits']["Bull"] == 2
    assert status == 'ok'

def test_win_condition_all_targets_closed_and_highest_score(cricket_logic, players):
    player1, player2 = players
    for target in cricket_logic.get_targets():
        player1.state['hits'][target] = 3
    player1.score = 100
    player2.score = 50

    result = cricket_logic._handle_throw(player1, "Single", 20, players)

    assert player1.game.end is True
    assert isinstance(result, str) and "gewinnt" in result

def test_no_win_if_score_is_lower(cricket_logic, players):
    player1, player2 = players
    for target in cricket_logic.get_targets():
        player1.state['hits'][target] = 3
    player1.score = 50
    player2.score = 100

    status, _ = cricket_logic._handle_throw(player1, "Single", 20, players)

    assert player1.game.end is False
    assert status == 'ok'

def test_win_on_equal_score(cricket_logic, players):
    player1, player2 = players
    player1.score = 100
    for target in cricket_logic.get_targets():
        player2.state['hits'][target] = 3
    player2.score = 80

    result = cricket_logic._handle_throw(player2, "Single", 20, players)

    assert player2.game.end is True
    assert isinstance(result, str) and "gewinnt" in result

def test_undo_simple_hit_restores_marks(cricket_logic, players):
    player1 = players[0]
    cricket_logic._handle_throw(player1, "Double", 20, players)
    assert player1.state['hits']["20"] == 2

    cricket_logic._handle_throw_undo(player1, "Double", 20, players)
    assert player1.state['hits']["20"] == 0

def test_undo_scoring_hit_restores_score_and_marks(cricket_logic, players):
    player1, _ = players
    player1.state['hits']["20"] = 3
    cricket_logic._handle_throw(player1, "Single", 20, players)
    assert player1.score == 20
    assert player1.state['hits']["20"] == 4

    cricket_logic._handle_throw_undo(player1, "Single", 20, players)
    assert player1.score == 0
    assert player1.state['hits']["20"] == 3

# --- Cut Throat Specific Tests ---

def test_cut_throat_scoring_adds_points_to_opponents(cut_throat_logic, cut_throat_players):
    player1, player2, player3 = cut_throat_players
    player1.state['hits']["20"] = 3
    player2.state['hits']["20"] = 1
    player3.state['hits']["20"] = 3

    cut_throat_logic._handle_throw(player1, "Single", 20, cut_throat_players)

    assert player1.score == 0
    assert player2.score == 20
    assert player3.score == 0

def test_cut_throat_win_condition_lowest_score(cut_throat_logic, players):
    player1, player2 = players
    for target in cut_throat_logic.get_targets():
        player1.state['hits'][target] = 3
    player1.score = 50
    player2.score = 100

    result = cut_throat_logic._handle_throw(player1, "Single", 20, players)

    assert player1.game.end is True
    assert isinstance(result, str) and "gewinnt" in result

def test_cut_throat_no_win_if_score_is_higher(cut_throat_logic, players):
    player1, player2 = players
    for target in cut_throat_logic.get_targets():
        player1.state['hits'][target] = 3
    player1.score = 100
    player2.score = 50

    status, _ = cut_throat_logic._handle_throw(player1, "Single", 20, players)

    assert player1.game.end is False
    assert status == 'ok'

def test_undo_cut_throat_scoring_hit_restores_opponent_score(cut_throat_logic, players):
    player1, player2 = players
    player1.state['hits']["19"] = 3
    cut_throat_logic._handle_throw(player1, "Double", 19, players)
    assert player2.score == 38

    cut_throat_logic._handle_throw_undo(player1, "Double", 19, players)
    assert player2.score == 0
    assert player1.state['hits']["19"] == 3