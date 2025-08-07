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
from core.atc import AtC
# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player

# Die geteilte 'mock_game' Fixture ist automatisch aus conftest.py verfügbar.

@pytest.fixture
def atc_logic(mock_game):
    """Erstellt eine Instanz der AtC-Logik mit dem gemockten Spiel."""
    mock_game.options.name = "Around the Clock"
    mock_game.options.opt_atc = "Single"  # Standard für die meisten Tests
    logic = AtC(mock_game)
    mock_game.targets = logic.get_targets()
    return logic

@pytest.fixture
def player(mock_game, atc_logic):
    """Erstellt eine echte Player-Instanz, die für ATC-Tests konfiguriert ist."""
    p = Player(name="Tester", game=mock_game)
    atc_logic.initialize_player_state(p)
    p.sb = MagicMock()
    return p

def test_initialization(player):
    """Testet, ob ein Spieler korrekt für ATC initialisiert wird."""
    assert player.score == 0
    assert player.state['next_target'] == "1"
    assert player.state['hits'].get("1") == 0
    assert "20" in player.state['hits']

def test_valid_hit_advances_target(atc_logic, player):
    """Testet, ob ein gültiger Treffer das nächste Ziel korrekt setzt."""
    status, _ = atc_logic._handle_throw(player, "Single", 1, [])
    assert player.state['hits']["1"] == 1
    assert player.state['next_target'] == "2"
    assert status == 'ok'

def test_invalid_hit_returns_error(atc_logic, player):
    """Testet, ob ein Wurf auf das falsche Ziel einen Fehler zurückgibt."""
    status, message = atc_logic._handle_throw(player, "Single", 5, [])
    assert player.state['hits']["1"] == 0
    assert player.state['next_target'] == "1"
    assert status == 'invalid_target'
    assert message is not None

def test_valid_hit_with_double_option(mock_game):
    """Testet einen gültigen Treffer, wenn die Option 'Double' aktiv ist."""
    # Für diesen Test müssen Spiel und Logik manuell konfiguriert werden.
    mock_game.options.name = "Around the Clock"
    mock_game.options.opt_atc = "Double"
    atc_logic = AtC(mock_game)
    mock_game.targets = atc_logic.get_targets()
    player = Player(name="Tester", game=mock_game)
    atc_logic.initialize_player_state(player)
    player.sb = MagicMock()

    status, _ = atc_logic._handle_throw(player, "Double", 1, [])
    assert player.state['hits']["1"] == 1
    assert player.state['next_target'] == "2"
    assert status == 'ok'

def test_win_condition(atc_logic, player):
    """Testet, ob das Spiel endet, wenn alle Ziele getroffen wurden."""
    # Alle Ziele von 1 bis 20 treffen
    for i in range(1, 21):
        atc_logic._handle_throw(player, "Single", i, [])
    
    # Den letzten Wurf auf Bull machen
    status, message = atc_logic._handle_throw(player, "Bull", 25, [])

    assert player.game.end is True
    assert status == 'win'
    assert "gewinnt" in message

def test_undo_restores_target(atc_logic, player):
    """Testet, ob die Undo-Funktion den Zustand korrekt wiederherstellt."""
    atc_logic._handle_throw(player, "Single", 1, [])
    assert player.state['next_target'] == "2"

    atc_logic._handle_throw_undo(player, "Single", 1, [])
    
    assert player.state['next_target'] == "1"
    assert player.state['hits']["1"] == 0