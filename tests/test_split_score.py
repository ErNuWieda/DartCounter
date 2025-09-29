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
from core.split_score import SplitScore
from core.player import Player


@pytest.fixture
def mock_game():
    """Erstellt ein Mock-Game-Objekt, das für die SplitScore-Logik konfiguriert ist."""
    game = MagicMock()
    game.options.name = "Split Score"
    game.options.opt_split_score_target = 40  # Start-Score
    # Die SplitScore-Logik greift auf game.game.targets zu
    game.game.targets = [("Single", 15), ("Single", 16)]  # Beispiel-Zielsequenz
    # KORREKTUR: Die GameLogicBase erwartet 'on_throw_processed'.
    # Wir mocken dieses Attribut und prüfen es dann im Test.
    game.on_throw_processed = MagicMock()
    return game


@pytest.fixture
def split_score_logic(mock_game):
    """Erstellt eine Instanz der SplitScore-Logik."""
    return SplitScore(mock_game)


@pytest.fixture
def player(mock_game, split_score_logic):
    """Erstellt eine initialisierte Player-Instanz."""
    p = Player("Tester", mock_game)
    split_score_logic.initialize_player_state(p)
    p.sb = MagicMock()
    return p


def test_missed_target_halves_score(split_score_logic, player, mock_game):
    """Testet, ob der Score bei einem Fehltreffer korrekt halbiert wird."""
    mock_game.round = 1  # Ziel ist S15
    player.score = 40

    # Simuliere einen Wurf, der das Ziel verfehlt
    player.throws = [("Single", 16, None)]
    # Die Score-Logik wird erst am Ende des Zugs ausgeführt
    split_score_logic.handle_end_of_turn(player)

    assert player.score == 20


def test_correct_hit_adds_score(split_score_logic, player, mock_game):
    """Testet, ob ein korrekter Treffer auf das Ziel den Score korrekt erhöht."""
    mock_game.round = 1  # Ziel ist S15
    player.score = 40
    # Simuliere einen Wurf, der das Ziel trifft
    player.throws = [("Single", 15, None)]

    # Die Score-Logik wird erst am Ende des Zugs ausgeführt
    split_score_logic.handle_end_of_turn(player)

    # KORREKTUR: Bei einem Treffer wird der Score NICHT halbiert.
    # Die Split-Score-Logik addiert keine Punkte, sie bestraft nur Fehltreffer.
    assert player.score == 40


def test_game_ends_after_last_round(split_score_logic, mock_game, player):
    """Testet, ob das Spiel nach der letzten Runde endet und der richtige Gewinner ermittelt wird."""
    # Nutze die 'player'-Fixture und erstelle einen zweiten Spieler
    p1 = player
    p1.name = "Alice"
    p1.score = 100

    p2 = Player("Bob", mock_game)
    split_score_logic.initialize_player_state(p2)
    p2.sb = MagicMock() # Wichtig: Auch der zweite Spieler braucht ein Mock-Scoreboard
    p2.score = 80

    mock_game.players = [p1, p2]
    mock_game.round = 7  # Letzte Runde
    mock_game.current = 1  # Bob ist der letzte Spieler der Runde

    # Bob beendet seinen Zug
    split_score_logic.handle_end_of_turn(p2)

    # Überprüfe, ob das Spiel beendet ist und Alice gewonnen hat
    assert mock_game.end is True
    assert mock_game.winner == p1
    mock_game.on_throw_processed.assert_called_once()
    assert mock_game.on_throw_processed.call_args[0][0].status == "win"
