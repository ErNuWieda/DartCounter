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
from core.elimination import Elimination

# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player

# Die geteilte 'mock_game' Fixture ist automatisch aus conftest.py verfügbar.


@pytest.fixture
def elimination_logic(mock_game):
    """Erstellt eine Instanz der Elimination-Logik mit dem gemockten Spiel."""
    mock_game.options.name = "Elimination"
    mock_game.options.count_to = 301
    mock_game.options.opt_out = "Single"
    return Elimination(mock_game)


@pytest.fixture
def players(mock_game, elimination_logic):
    """Erstellt eine Liste von zwei initialisierten Spielern."""
    player_list = []
    for i in range(2):
        p = Player(name=f"Player {i+1}", game=mock_game)
        elimination_logic.initialize_player_state(p)
        p.sb = MagicMock()
        player_list.append(p)
    return player_list


def test_initialization(players):
    """Testet, ob ein Spieler korrekt für Elimination initialisiert wird."""
    assert players[0].score == 0


def test_valid_throw_increases_score(elimination_logic, players):
    """Testet, ob ein gültiger Wurf den Punktestand korrekt erhöht."""
    player1 = players[0]
    status, _ = elimination_logic._handle_throw(player1, "Triple", 20, [])
    assert player1.score == 60
    assert status == "ok"


def test_bust_if_score_exceeds_target(elimination_logic, players):
    """Testet, ob ein Bust auftritt, wenn der Score das Ziel überschreitet."""
    player1 = players[0]
    player1.score = 300
    status, _ = elimination_logic._handle_throw(player1, "Single", 2, [])
    assert player1.score == 300
    assert status == "bust"


def test_elimination_resets_opponent_score(elimination_logic, players):
    """Testet, ob ein Spieler einen Gegner eliminieren kann."""
    player1, player2 = players
    player1.score = 40
    player2.score = 100

    status, message = elimination_logic._handle_throw(player1, "Triple", 20, players)

    assert player1.score == 100
    assert player2.score == 0
    assert status == "info"
    assert "schickt" in message


def test_win_condition(elimination_logic, players):
    """Testet, ob das Spiel endet, wenn der Zielscore exakt erreicht wird."""
    player1 = players[0]
    player1.score = 241  # 301 - 60
    status, message = elimination_logic._handle_throw(player1, "Triple", 20, [])
    assert player1.score == 301
    assert player1.game.end is True
    assert status == "win" and "gewinnt" in message


def test_undo_elimination_restores_victim_score(elimination_logic, players):
    """Testet, ob Undo eine Eliminierung korrekt rückgängig macht."""
    player1, player2 = players
    player1.score = 40
    player2.score = 100

    elimination_logic._handle_throw(player1, "Triple", 20, players)
    assert player2.score == 0

    elimination_logic._handle_throw_undo(player1, "Triple", 20, players)

    assert player1.score == 40
    assert player2.score == 100

def test_undo_bust_restores_turn_state(elimination_logic, players):
    """Verifiziert, dass das Undo eines Busts den Punktestand nicht korrumpiert."""
    player1 = players[0]
    player1.score = 280
    # Wurf auf T20 (60) -> 340 > 301 (Bust)
    elimination_logic._handle_throw(player1, "Triple", 20, [])
    assert player1.score == 280
    assert player1.turn_is_over is True

    elimination_logic._handle_throw_undo(player1, "Triple", 20, [])
    assert player1.score == 280
    assert player1.turn_is_over is False

def test_elimination_cross_turn_undo(elimination_logic, players):
    """Testet, ob eine Eliminierung über einen Spielerwechsel hinweg rückgängig gemacht werden kann."""
    p1, p2 = players
    p1.score = 100
    p2.score = 40

    # 1. P2 wirft T20 (60) -> Score 100. P1 wird eliminiert (Score 0).
    elimination_logic._handle_throw(p2, "Triple", 20, players)
    assert p1.score == 0
    assert p2.score == 100
    p2.reset_turn() # Spielerwechsel simulieren

    # 2. Undo für P2 aufrufen (der GameController würde P2 als 'previous' wiederherstellen)
    elimination_logic._handle_throw_undo(p2, "Triple", 20, players)

    # 3. Ergebnisse prüfen
    assert p1.score == 100, "P1 hätte seine 100 Punkte zurückerhalten müssen."
    assert p2.score == 40, "P2 hätte wieder auf 40 Punkte fallen müssen."
