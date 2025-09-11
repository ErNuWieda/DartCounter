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

# Import the class to be tested
from core.player import Player


@pytest.fixture
def player_instance():
    """
    Eine pytest-Fixture, die eine Player-Instanz mit einem gemockten Game-Objekt erstellt.
    """
    # Erstelle einen Mock für die Game-Instanz, die der Player benötigt
    mock_game = MagicMock()
    mock_game.name = "501"
    mock_game.targets = []  # X01 hat keine festen Ziele

    # Erstelle die Player-Instanz, die wir testen wollen
    player = Player(name="TestPlayer", game=mock_game)
    return player


def test_get_average_initial(player_instance):
    """Testet, dass der Average am Anfang 0.0 ist."""
    assert player_instance.get_average() == 0.0


def test_get_average_calculation(player_instance):
    """Testet die korrekte Berechnung des 3-Dart-Average."""
    # Simuliere geworfene Darts und Punkte
    player_instance.stats["total_darts_thrown"] = 6
    player_instance.stats["total_score_thrown"] = 100

    # Erwarteter Average: (100 / 6) * 3 = 50.0
    assert player_instance.get_average() == pytest.approx(50.0)

    # Weiterer Testfall
    player_instance.stats["total_darts_thrown"] = 21
    player_instance.stats["total_score_thrown"] = 450
    # Erwarteter Average: (450 / 21) * 3 = 64.2857...
    assert player_instance.get_average() == pytest.approx(64.29, abs=0.01)


def test_get_checkout_percentage_initial(player_instance):
    """Testet, dass die Checkout-Quote am Anfang 0.0 ist."""
    assert player_instance.get_checkout_percentage() == 0.0


def test_get_checkout_percentage_calculation(player_instance):
    """Testet die korrekte Berechnung der Checkout-Quote."""
    # Simuliere Checkout-Möglichkeiten und erfolgreiche Checkouts
    player_instance.stats["checkout_opportunities"] = 4
    player_instance.stats["checkouts_successful"] = 1

    # Erwartete Quote: (1 / 4) * 100 = 25.0%
    assert player_instance.get_checkout_percentage() == pytest.approx(25.0)


def test_get_checkout_percentage_no_success(player_instance):
    """Testet die Checkout-Quote, wenn es Möglichkeiten, aber keine Erfolge gab."""
    player_instance.stats["checkout_opportunities"] = 5
    player_instance.stats["checkouts_successful"] = 0

    # Erwartete Quote: 0.0%
    assert player_instance.get_checkout_percentage() == 0.0


def test_get_total_darts_in_game(player_instance):
    """Testet die korrekte Berechnung der Gesamtzahl der im Spiel geworfenen Darts."""
    # Fall 1: Anfang des Spiels, Runde 1, 0 Würfe
    player_instance.game.round = 1
    player_instance.throws = []
    assert player_instance.get_total_darts_in_game() == 0

    # Fall 2: Mitte der Runde 1, 2 Würfe
    player_instance.game.round = 1
    player_instance.throws = [("T", 20, None), ("S", 1, None)]
    assert player_instance.get_total_darts_in_game() == 2

    # Fall 3: Anfang von Runde 5, 0 Würfe in dieser Runde
    player_instance.game.round = 5
    player_instance.throws = []
    assert player_instance.get_total_darts_in_game() == 12

    # Fall 4: Mitte von Runde 3, 1 Wurf in dieser Runde
    player_instance.game.round = 3
    player_instance.throws = [("D", 16, None)]
    assert player_instance.get_total_darts_in_game() == 7


def test_get_mpr_calculation(player_instance):
    """Testet die korrekte Berechnung der Marks Per Round (MPR)."""
    # Fall 1: Anfang des Spiels, keine Würfe, keine Marks
    player_instance.game.round = 1
    player_instance.throws = []
    player_instance.stats["total_marks_scored"] = 0
    assert player_instance.get_mpr() == 0.0

    # Fall 2: Einfacher Fall nach einer Runde
    # 5 Marks in 4 Darts (Runde 2, 1 Wurf)
    player_instance.game.round = 2
    player_instance.throws = [("S", 20, None)]
    player_instance.stats["total_marks_scored"] = 5
    # Erwartete MPR: (5 / 4) * 3 = 3.75
    assert player_instance.get_mpr() == pytest.approx(3.75)

    # Fall 3: Komplexerer Fall
    # 15 Marks in 11 Darts (Runde 4, 2 Würfe)
    player_instance.game.round = 4
    player_instance.throws = [("D", 18, None), ("S", 17, None)]
    player_instance.stats["total_marks_scored"] = 15
    # Erwartete MPR: (15 / 11) * 3 = 4.0909...
    assert player_instance.get_mpr() == pytest.approx(4.09, abs=0.01)
