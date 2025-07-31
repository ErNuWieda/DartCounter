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
from core.killer import Killer
# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player

# Die geteilte 'mock_game' Fixture ist automatisch aus conftest.py verfügbar.

@pytest.fixture
def killer_logic(mock_game):
    """Erstellt eine Instanz der Killer-Logik mit dem gemockten Spiel."""
    mock_game.name = "Killer"
    mock_game.lifes = 3
    mock_game.next_player = MagicMock()
    return Killer(mock_game)

@pytest.fixture
def players(mock_game, killer_logic):
    """Erstellt eine Liste von zwei initialisierten Spielern für Killer."""
    player_list = []
    for i in range(2):
        p = Player(name=f"Player {i+1}", game=mock_game)
        killer_logic.initialize_player_state(p)
        p.sb = MagicMock()
        player_list.append(p)
    # Wichtig: Die Killer-Logik muss die Spielerliste kennen
    killer_logic.set_players(player_list)
    return player_list

def test_initialization(players, mock_game):
    """Testet, ob ein Spieler korrekt für Killer initialisiert wird."""
    player1 = players[0]
    assert player1.score == mock_game.lifes
    assert player1.state['life_segment'] is None
    assert player1.state['can_kill'] is False

def test_set_life_segment_success(killer_logic, players):
    """Testet das erfolgreiche Festlegen eines Lebensfeldes."""
    player1 = players[0]
    status, message = killer_logic._handle_throw(player1, "Single", 15, players)
    assert player1.state['life_segment'] == "15"
    assert player1.game.next_player.called
    assert status == 'info'
    assert "hat Lebensfeld" in message

def test_set_life_segment_fails_on_taken_segment(killer_logic, players):
    """Testet, dass das Festlegen eines bereits vergebenen Feldes fehlschlägt."""
    player1, player2 = players
    player2.state['life_segment'] = "15"

    status, message = killer_logic._handle_throw(player1, "Single", 15, players)

    assert player1.state['life_segment'] is None
    assert not player1.game.next_player.called
    assert status == 'warning'
    assert "bereits an" in message

def test_become_killer_success(killer_logic, players):
    """Testet, ob ein Spieler durch Treffen seines Doubles zum Killer wird."""
    player1 = players[0]
    player1.state['life_segment'] = "20"

    status, message = killer_logic._handle_throw(player1, "Double", 20, [])

    assert player1.state['can_kill'] is True
    assert status == 'info'
    assert "ist jetzt ein KILLER" in message

def test_killer_takes_opponent_life(killer_logic, players):
    """Testet, ob ein Killer einem Gegner ein Leben nehmen kann."""
    killer, victim = players
    killer.state['life_segment'] = "20"
    killer.state['can_kill'] = True
    victim.state['life_segment'] = "19"
    victim_initial_lives = victim.score

    status, _ = killer_logic._handle_throw(killer, "Double", 19, players)

    assert victim.score == victim_initial_lives - 1
    assert status == 'info'

def test_win_condition_last_player_standing(killer_logic, players):
    """Testet die Gewinnbedingung, wenn nur noch ein Spieler übrig ist."""
    killer, victim = players
    killer.state['life_segment'] = "20"
    killer.state['can_kill'] = True
    victim.state['life_segment'] = "19"
    victim.score = 1

    status, _ = killer_logic._handle_throw(killer, "Double", 19, players)

    assert victim.score == 0
    assert killer.game.end is True
    assert status == 'info'

def test_undo_take_life_restores_victim_life(killer_logic, players, mock_game):
    """Testet, ob das Rückgängigmachen einer 'take_life'-Aktion das Leben wiederherstellt."""
    killer, victim = players
    killer.state['life_segment'] = "20"
    killer.state['can_kill'] = True
    victim.state['life_segment'] = "19"

    killer_logic._handle_throw(killer, "Double", 19, players)
    assert victim.score == mock_game.lifes - 1

    killer_logic._handle_throw_undo(killer, "Double", 19, players)

    assert victim.score == mock_game.lifes