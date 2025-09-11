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
from unittest.mock import Mock, MagicMock

# Klasse, die getestet wird
from core.x01 import X01

# Klassen, die als Abhängigkeiten gemockt werden
from core.game_options import GameOptions

# --- Fixtures für Mocks ---


@pytest.fixture
def mock_player():
    """Erstellt einen Mock-Spieler für Testzwecke."""
    player = MagicMock()
    player.name = "TestPlayer"
    player.score = 501
    player.throws = []
    player.state = {"has_opened": False}
    player.stats = {
        "checkout_opportunities": 0,
        "checkouts_successful": 0,
        "successful_finishes": [],
        "highest_finish": 0,
        "total_darts_thrown": 0,
        "total_score_thrown": 0,
    }
    player.sb = MagicMock()
    player.profile = None
    player.game = MagicMock()
    player.game.options.name = "501"

    type(player).has_opened = property(
        fget=lambda p: p.state.get("has_opened", False),
        fset=lambda p, v: p.state.update({"has_opened": v}),
    )

    def update_score_value(score, subtract=True):
        if subtract:
            player.score -= score
        else:
            player.score += score

    player.update_score_value = Mock(side_effect=update_score_value)

    return player


@pytest.fixture
def mock_game():
    """Erstellt ein Mock-Spiel für Testzwecke."""
    game = MagicMock()
    game.options = GameOptions(
        name="501",
        opt_in="Single",
        opt_out="Double",
        count_to=501,
        opt_atc="Single",
        lifes=3,
        rounds=7,
        legs_to_win=1,
        sets_to_win=1,
    )
    game.get_score = lambda ring, segment: {
        "Single": segment,
        "Double": segment * 2,
        "Triple": segment * 3,
        "Bull": 25,
        "Bullseye": 50,
        "Miss": 0,
    }.get(ring, 0)
    game.round = 1
    game.end = False
    game.winner = None
    game.shanghai_finish = False
    game._handle_leg_win = Mock()
    return game


class TestX01Logic:

    def test_handle_throw_normal_score(self, mock_game, mock_player):
        """Testet einen normalen Wurf, der nur den Punktestand reduziert."""
        x01_logic = X01(mock_game)
        mock_player.score = 140
        mock_player.has_opened = True

        status, msg = x01_logic._handle_throw(mock_player, "Triple", 20, [])

        assert status == "ok"
        assert msg is None
        assert mock_player.score == 80
        assert (
            mock_player.stats["total_score_thrown"] == 60
        ), "Der geworfene Score wurde nicht korrekt zur Statistik hinzugefügt."

    def test_handle_throw_bust_score_is_one(self, mock_game, mock_player):
        """Testet einen Bust, weil der Restscore 1 ist (bei Double Out)."""
        x01_logic = X01(mock_game)
        mock_player.score = 61
        mock_player.state["has_opened"] = True

        status, msg = x01_logic._handle_throw(mock_player, "Triple", 20, [])

        assert status == "bust"
        assert "überworfen" in msg
        assert mock_player.score == 61

    def test_handle_throw_bust_invalid_finish(self, mock_game, mock_player):
        """Testet einen Bust, weil auf einem Single gefinished wurde (bei Double Out)."""
        x01_logic = X01(mock_game)
        mock_player.score = 20
        mock_player.state["has_opened"] = True

        status, msg = x01_logic._handle_throw(mock_player, "Single", 20, [])

        assert status == "bust"
        assert "überworfen" in msg
        assert mock_player.score == 20

    def test_handle_throw_win_condition(self, mock_game, mock_player):
        """Testet einen gültigen Gewinnwurf."""
        x01_logic = X01(mock_game)
        mock_player.score = 40
        mock_player.has_opened = True

        status, msg = x01_logic._handle_throw(mock_player, "Double", 20, [])

        assert status == "win"
        assert "gewinnt" in msg if msg else False
        assert mock_player.score == 0
        assert mock_player.stats["checkouts_successful"] == 1
        assert mock_player.stats["highest_finish"] == 40
        mock_game._handle_leg_win.assert_called_once_with(mock_player)

    def test_handle_throw_opt_in_fail(self, mock_game, mock_player):
        """Testet einen ungültigen Eröffnungswurf (bei Double In)."""
        mock_game.options.opt_in = "Double"
        x01_logic = X01(mock_game)
        mock_player.has_opened = False

        status, msg = x01_logic._handle_throw(mock_player, "Single", 20, [])

        assert status == "invalid_open"
        assert "Double zum Start" in msg
        assert mock_player.state["has_opened"] is False

    def test_handle_throw_opt_in_success(self, mock_game, mock_player):
        """Testet einen gültigen Eröffnungswurf (bei Double In)."""
        mock_game.options.opt_in = "Double"
        x01_logic = X01(mock_game)
        mock_player.has_opened = False
        mock_player.score = 501

        status, msg = x01_logic._handle_throw(mock_player, "Double", 20, [])

        assert status == "ok"
        assert mock_player.state["has_opened"] is True
        assert mock_player.score == 461

    def test_handle_throw_shanghai_finish(self, mock_game, mock_player):
        """Testet die Erkennung eines 120er Shanghai-Finishs."""
        x01_logic = X01(mock_game)
        mock_player.score = 40  # Score nach den ersten beiden Würfen
        mock_player.has_opened = True
        # Wichtig: Der aktuelle Wurf muss in der Liste sein, BEVOR _handle_throw aufgerufen wird.
        mock_player.throws = [
            ("Triple", 20, None),
            ("Single", 20, None),
            ("Double", 20, None),
        ]

        status, msg = x01_logic._handle_throw(mock_player, "Double", 20, [])

        assert status == "win", "Ein Shanghai-Finish sollte als 'win' zurückgegeben werden."
        assert mock_game.shanghai_finish is True

    def test_handle_throw_undo_simple_score(self, mock_game, mock_player):
        """Testet das Rückgängigmachen eines einfachen Wurfs."""
        x01_logic = X01(mock_game)
        mock_player.score = 100
        mock_player.stats["total_score_thrown"] = 60
        mock_player.stats["total_darts_thrown"] = 1
        mock_player.state["has_opened"] = True

        x01_logic._handle_throw_undo(mock_player, "Triple", 20, [])

        assert mock_player.score == 160
        assert mock_player.stats["total_score_thrown"] == 0
        assert mock_player.stats["total_darts_thrown"] == 0

    def test_handle_throw_undo_opening_throw(self, mock_game, mock_player):
        """Testet das Rückgängigmachen eines Eröffnungswurfs."""
        mock_game.options.opt_in = "Double"
        x01_logic = X01(mock_game)

        mock_player.score = 501
        mock_player.state["has_opened"] = False
        x01_logic._handle_throw(mock_player, "Double", 20, [])
        assert mock_player.score == 461
        assert mock_player.has_opened is True

        x01_logic._handle_throw_undo(mock_player, "Double", 20, [])

        assert mock_player.score == 501
        assert mock_player.has_opened is False
