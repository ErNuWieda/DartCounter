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
from core.micky import Micky
# Klassen, die als Abhängigkeiten gemockt werden
from core.player import Player
from core.game import Game


@pytest.fixture
def mock_game():
    """Erstellt eine gemockte Game-Instanz mit den für die Micky-Logik benötigten Attributen."""
    game = MagicMock(spec=Game)
    game.options = MagicMock()
    game.options.name = "Micky Mouse"
    game.round = 1 # Fehlte, wird für die Gewinnprüfung benötigt
    game.end = False
    game.winner = None
    game.sound_manager = MagicMock()
    game.highscore_manager = MagicMock()

    # Die get_score Methode des Spiels simulieren
    def mock_get_score(ring, segment):
        if ring == "Single": return segment
        if ring == "Double": return segment * 2
        if ring == "Triple": return segment * 3
        if ring == "Bull": return 25
        if ring == "Bullseye": return 50
        return 0
    game.get_score.side_effect = mock_get_score
    return game


@pytest.fixture
def micky_logic(mock_game):
    """Erstellt eine Instanz der Micky-Logik mit dem gemockten Spiel."""
    logic = Micky(mock_game)
    # Wichtig, damit der Player korrekt initialisiert werden kann
    mock_game.targets = logic.get_targets()
    return logic


@pytest.fixture
def player(mock_game, micky_logic):
    """Erstellt eine echte Player-Instanz, die für die Tests konfiguriert ist."""
    p = Player(name="Tester", game=mock_game)
    micky_logic.initialize_player_state(p)
    p.sb = MagicMock()
    return p


def test_initialization(player):
    """Testet, ob ein Spieler korrekt für Micky Maus initialisiert wird."""
    assert player.score == 0
    assert player.state['next_target'] == "20"
    assert player.state['hits'].get("20") == 0


def test_correct_hit_increases_marks(micky_logic, player):
    """Testet, ob ein Treffer auf das korrekte Ziel die Treffer erhöht."""
    player.state['next_target'] = "20"
    
    result = micky_logic._handle_throw(player, "Single", 20, [])
    
    assert player.state['hits']["20"] == 1
    assert result is None


def test_incorrect_hit_returns_error(micky_logic, player):
    """Testet, ob ein Treffer auf ein falsches Ziel einen Fehler zurückgibt."""
    player.state['next_target'] = "20"

    status, message = micky_logic._handle_throw(player, "Single", 19, [])
    
    assert player.state['hits']["20"] == 0
    assert player.state['next_target'] == "20"
    assert status == 'invalid_target'
    assert message is not None


def test_closing_target_advances_to_next(micky_logic, player):
    """Testet, ob das Schließen eines Ziels zum nächsten Ziel fortschreitet."""
    player.state['next_target'] = "20"
    player.state['hits']["20"] = 2 # Bereits 2 Treffer

    micky_logic._handle_throw(player, "Single", 20, [])
    
    assert player.state['hits']["20"] == 3
    assert player.state['next_target'] == "19"


def test_win_condition(micky_logic, player):
    """Testet die Gewinnbedingung, wenn das letzte Ziel (Bull) geschlossen wird."""
    # Alle Ziele außer Bull schließen
    for target in micky_logic.get_targets():
        if target != "Bull":
            player.state['hits'][target] = 3
    
    # Das nächste Ziel sollte Bull sein
    player.state['next_target'] = "Bull"
    player.state['hits']["Bull"] = 2 # Zwei Treffer auf Bull

    # Der letzte Wurf, der das Spiel gewinnt
    status, message = micky_logic._handle_throw(player, "Bull", 25, [])

    assert player.game.end is True
    assert status == 'win' and "gewinnt" in message


def test_undo_restores_marks_and_target(micky_logic, player):
    """Testet, ob Undo die Treffer und das nächste Ziel korrekt wiederherstellt."""
    # Treffer auf 20, nächstes Ziel ist 19
    micky_logic._handle_throw(player, "Triple", 20, [])
    assert player.state['hits']["20"] == 3
    assert player.state['next_target'] == "19"

    # Aktion: Rückgängig machen
    micky_logic._handle_throw_undo(player, "Triple", 20, [])

    # Überprüfung
    assert player.state['hits']["20"] == 0
    assert player.state['next_target'] == "20"