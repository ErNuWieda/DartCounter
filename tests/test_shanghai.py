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
from core.shanghai import Shanghai
# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player

# Die geteilte 'mock_game' Fixture ist automatisch aus conftest.py verfügbar.

@pytest.fixture
def shanghai_logic(mock_game):
    """Erstellt eine Instanz der Shanghai-Logik mit dem gemockten Spiel."""
    mock_game.name = "Shanghai"
    mock_game.rounds = 7
    logic = Shanghai(mock_game)
    mock_game.targets = logic.get_targets()
    return logic

@pytest.fixture
def players(mock_game, shanghai_logic):
    """Erstellt eine Liste von zwei initialisierten Spielern."""
    player_list = []
    for i in range(2):
        p = Player(name=f"Player {i+1}", game=mock_game)
        shanghai_logic.initialize_player_state(p)
        p.sb = MagicMock()
        player_list.append(p)
    return player_list

def test_initialization(players, shanghai_logic):
    """Testet, ob ein Spieler korrekt für Shanghai initialisiert wird."""
    player1 = players[0]
    assert player1.score == 0
    assert player1.state['next_target'] == "1"
    assert player1.state['hits'].get("1") == 0
    assert "7" in shanghai_logic.get_targets()
    assert "8" not in shanghai_logic.get_targets()

def test_correct_hit_scores_points(shanghai_logic, players, mock_game):
    """Testet, ob ein Treffer auf das korrekte Ziel (der Runde) Punkte gibt."""
    mock_game.round = 2
    player1 = players[0]
    
    shanghai_logic._handle_throw(player1, "Triple", 2, [])
    
    assert player1.score == 6
    assert player1.state['hits']["2"] == 1

def test_incorrect_hit_scores_no_points(shanghai_logic, players, mock_game):
    """Testet, ob ein Treffer auf ein falsches Ziel keine Punkte gibt."""
    mock_game.round = 3
    player1 = players[0]

    shanghai_logic._handle_throw(player1, "Single", 4, [])
    
    assert player1.score == 0
    assert player1.state['hits'].get("3") == 0

def test_shanghai_win_condition(shanghai_logic, players, mock_game):
    """Testet, ob ein Shanghai (S, D, T) zum sofortigen Sieg führt."""
    mock_game.round = 5
    player1 = players[0]
    player1.throws = [("Single", 5, None), ("Double", 5, None), ("Triple", 5, None)]
    
    status, message = shanghai_logic._handle_throw(player1, "Triple", 5, [])
    
    assert mock_game.end is True
    assert status == 'win' and "Shanghai auf die 5" in message

def test_end_of_rounds_win_condition(shanghai_logic, players, mock_game):
    """Testet, ob nach der letzten Runde der Spieler mit den meisten Punkten gewinnt."""
    mock_game.options.rounds = 2 # Korrekt das options-Objekt anpassen
    mock_game.round = 3
    player1, player2 = players
    player1.score = 100
    player2.score = 50
    
    # Die Logik gibt bei Spielende nur einen String zurück, kein Tupel.
    status, message = shanghai_logic._handle_throw(player2, "Miss", 0, players)
    
    assert mock_game.end is True
    assert status == 'win'
    assert f"{player1.name} gewinnt mit 100 Punkten" in message

def test_undo_restores_state(shanghai_logic, players, mock_game):
    """Testet, ob das Rückgängigmachen eines Wurfs Score und Treffer korrekt wiederherstellt."""
    mock_game.round = 4
    player1 = players[0]
    shanghai_logic._handle_throw(player1, "Double", 4, [])
    assert player1.score == 8
    assert player1.state['hits'].get("4") == 1
    shanghai_logic._handle_throw_undo(player1, "Double", 4, [])
    assert player1.score == 0
    assert player1.state['hits'].get("4") == 0