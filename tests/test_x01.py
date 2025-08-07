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
from core.x01 import X01
# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player
from core.game_options import GameOptions

# Die geteilte 'mock_game' Fixture ist automatisch aus conftest.py verfügbar.

@pytest.fixture
def x01_logic(mock_game):
    """Erstellt eine Instanz der X01-Logik mit dem gemockten Spiel."""
    # Spieloptionen vor der Instanziierung der Logik setzen
    mock_game.options = GameOptions(
        name="501", opt_in="Double", opt_out="Double", opt_atc="Single",
        count_to=501, lifes=3, rounds=7
    )
    # Die Player-Klasse greift auf game.options.name zu
    mock_game.options.name = "501"
    return X01(mock_game)

@pytest.fixture
def player(mock_game, x01_logic):
    """Erstellt eine echte Player-Instanz, die für die Tests konfiguriert ist."""
    p = Player(name="Tester", game=mock_game)
    x01_logic.initialize_player_state(p)
    p.sb = MagicMock()
    # Standardwerte, die in Tests überschrieben werden können
    p.score = 501
    p.state['has_opened'] = True
    return p

# --- Opt-In Tests ---

def test_opt_in_double_fails_on_single_throw(x01_logic, player):
    """Testet, ob bei 'Double In' ein Single-Wurf ungültig ist."""
    player.game.options.opt_in = "Double"
    player.score = 501
    player.state['has_opened'] = False

    status, message = x01_logic._handle_throw(player, "Single", 20, [])

    assert player.score == 501
    assert not player.state['has_opened']
    assert status == 'invalid_open'
    assert message is not None

def test_opt_in_double_succeeds_on_double_throw(x01_logic, player):
    """Testet, ob bei 'Double In' ein Double-Wurf gültig ist und das Spiel eröffnet."""
    player.game.options.opt_in = "Double"
    player.score = 501
    player.state['has_opened'] = False

    status, _ = x01_logic._handle_throw(player, "Double", 20, [])

    assert player.score == 461
    assert player.state['has_opened']
    assert status == 'ok'

# --- Bust Tests ---

def test_bust_if_score_goes_below_zero(x01_logic, player):
    """Testet, ob ein Wurf, der den Score unter 0 bringen würde, ein 'Bust' ist."""
    player.score = 20
    status, _ = x01_logic._handle_throw(player, "Triple", 20, []) # Wurf von 60
    assert player.score == 20
    assert player.turn_is_over
    assert status == 'bust'

def test_opt_out_double_busts_if_score_is_one(x01_logic, player):
    """Testet, ob bei 'Double Out' ein Rest von 1 ein 'Bust' ist."""
    player.score = 21
    status, _ = x01_logic._handle_throw(player, "Single", 20, []) # Bringt Score auf 1 -> Bust
    assert player.score == 21
    assert player.turn_is_over
    assert status == 'bust'

def test_opt_out_double_busts_on_single_finish(x01_logic, player):
    """Testet, ob bei 'Double Out' ein Finish mit einem Single-Wurf ein 'Bust' ist."""
    player.score = 20
    status, _ = x01_logic._handle_throw(player, "Single", 20, [])
    assert player.score == 20
    assert player.turn_is_over
    assert status == 'bust'

# --- Gültiger Wurf & Gewinn Tests ---

def test_valid_throw_updates_score_and_stats(x01_logic, player):
    """Testet, ob ein gültiger Wurf den Score und die Statistiken korrekt aktualisiert."""
    player.score = 100
    status, _ = x01_logic._handle_throw(player, "Triple", 20, []) # Wurf von 60
    assert player.score == 40
    assert player.stats['total_darts_thrown'] == 1
    assert player.stats['total_score_thrown'] == 60
    assert status == 'ok'

def test_win_on_double_out_updates_all_stats(x01_logic, player):
    """Testet, ob ein Gewinnwurf bei 'Double Out' alle relevanten Daten korrekt aktualisiert."""
    player.score = 40
    result = x01_logic._handle_throw(player, "Double", 20, [])
    assert player.score == 0
    assert player.game.end is True
    assert player.stats['checkout_opportunities'] == 1
    assert player.stats['checkouts_successful'] == 1
    assert player.stats['highest_finish'] == 40
    assert isinstance(result, str) and "gewinnt" in result

# --- Undo Tests ---

def test_undo_simple_throw_restores_state(x01_logic, player):
    """Testet, ob das Rückgängigmachen eines Wurfs Score und Stats korrekt wiederherstellt."""
    player.score = 100
    x01_logic._handle_throw(player, "Triple", 20, [])
    assert player.score == 40

    x01_logic._handle_throw_undo(player, "Triple", 20, [])

    assert player.score == 100
    assert player.stats['total_darts_thrown'] == 0
    assert player.stats['total_score_thrown'] == 0

def test_undo_winning_throw_restores_player_state(x01_logic, player):
    """Testet, ob das Rückgängigmachen eines Gewinnwurfs den Spieler-Zustand wiederherstellt."""
    player.score = 40
    x01_logic._handle_throw(player, "Double", 20, [])
    assert player.stats['checkouts_successful'] == 1

    x01_logic._handle_throw_undo(player, "Double", 20, [])

    assert player.score == 40
    assert player.stats['checkouts_successful'] == 0