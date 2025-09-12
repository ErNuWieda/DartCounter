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
from unittest.mock import Mock, patch, MagicMock
from core.ai_player import AIPlayer
from core.player_profile import PlayerProfile
from core.player import Player
from core.game import Game
from core.ai_strategy import AIStrategy
from core.ai_strategy import (
    X01AIStrategy,
    CricketAIStrategy,
    DefaultAIStrategy,
    KillerAIStrategy,
    ShanghaiAIStrategy,
)


@pytest.fixture
def ai_player_with_mocks():
    """
    Eine pytest-Fixture, die eine AIPlayer-Instanz mit allen notwendigen Mocks einrichtet.
    """
    mock_game = Mock(spec=Game)
    mock_game.dartboard = Mock()
    mock_game.dartboard.root = Mock()
    mock_game.dartboard.root.winfo_exists.return_value = True  # Wichtig für .after()
    mock_game.dartboard.skaliert = {
        "triple_outer": 520,
        "triple_inner": 470,
        "double_outer": 835,
        "double_inner": 785,
    }
    mock_game.dartboard.center_x = 250
    mock_game.dartboard.center_y = 250
    mock_game.dartboard.get_coords_for_target.return_value = (300, 300)

    # FIX: Füge das fehlende settings_manager-Attribut hinzu, das vom AIPlayer-Konstruktor benötigt wird.
    mock_game.settings_manager = MagicMock(get=MagicMock(return_value=1000))

    mock_game.targets = []  # Fehlendes Attribut hinzufügen

    # Mock die get_score Methode, da die Strategie sie verwendet
    def mock_get_score(ring, segment):
        if ring == "Triple":
            return segment * 3
        if ring == "Double":
            return segment * 2
        if ring == "Single":
            return segment
        if ring == "Bullseye":
            return 50
        if ring == "Bull":
            return 25
        return 0

    mock_game.get_score.side_effect = mock_get_score

    mock_game.game = Mock()
    mock_game.end = False
    mock_game.options = Mock()  # Wichtig für die Strategie-Logik

    ai_profile = PlayerProfile(name="RoboCop", is_ai=True, difficulty="Fortgeschritten")

    ai_player = AIPlayer(name="RoboCop", game=mock_game, profile=ai_profile)
    ai_player.score = 501
    ai_player.turn_is_over = False

    mock_game.players = [ai_player]

    return ai_player, mock_game


@pytest.fixture
def x01_ai_player(ai_player_with_mocks):
    """Fixture for an AI player specifically configured for X01 games."""
    ai_player, mock_game = ai_player_with_mocks
    mock_game.options.name = "501"
    mock_game.options.opt_out = "Double"
    ai_player.strategy = X01AIStrategy(ai_player)
    return ai_player, mock_game


@pytest.fixture
def cricket_ai_player(ai_player_with_mocks):
    """Fixture for an AI player specifically configured for Cricket games."""
    ai_player, mock_game = ai_player_with_mocks
    mock_game.options.name = "Cricket"
    mock_game.game.get_targets.return_value = [
        "20",
        "19",
        "18",
        "17",
        "16",
        "15",
        "Bull",
    ]
    ai_player.strategy = CricketAIStrategy(ai_player)
    return ai_player, mock_game


@pytest.fixture
def killer_ai_player(ai_player_with_mocks):
    """Fixture for an AI player specifically configured for Killer games."""
    ai_player, mock_game = ai_player_with_mocks
    mock_game.options.name = "Killer"

    # Setup opponents for the tests
    opponent1 = Mock(spec=Player)
    opponent1.name = "Opponent1"
    opponent1.score = 3
    opponent1.state = {"life_segment": "19", "can_kill": True}

    opponent2 = Mock(spec=Player)
    opponent2.name = "Opponent2"
    opponent2.score = 2
    opponent2.state = {"life_segment": "18", "can_kill": True}

    mock_game.players = [ai_player, opponent1, opponent2]
    ai_player.strategy = KillerAIStrategy(ai_player)
    return ai_player, mock_game


def test_initialization(ai_player_with_mocks):
    """Testet, ob der AIPlayer korrekt initialisiert wird."""
    ai_player, _ = ai_player_with_mocks
    assert isinstance(ai_player, AIPlayer)
    assert ai_player.is_ai()
    assert ai_player.name == "RoboCop"
    assert ai_player.difficulty == "Fortgeschritten"
    assert ai_player.throw_radius == 60
    assert ai_player.throw_delay == 1000


def test_get_strategic_target_for_x01_high_score(x01_ai_player):
    """Testet die Zielauswahl für X01 bei hohem Punktestand (kein Finish)."""
    ai_player, _ = x01_ai_player
    ai_player.score = 181  # T20 -> 121 (ok), T19 -> 124 (ok). T20 is higher score.
    target = ai_player.strategy.get_target(throw_number=1)
    assert target == ("Triple", 20)


@patch("core.ai_strategy.CheckoutCalculator.get_checkout_suggestion")
def test_get_strategic_target_for_x01_checkout_path(mock_get_suggestion, x01_ai_player):
    """Testet die Zielauswahl, wenn ein Checkout-Pfad verfügbar ist."""
    ai_player, mock_game = x01_ai_player

    # Szenario 1: 100 Rest, 3 Darts -> T20, D20
    ai_player.score = 100
    mock_get_suggestion.return_value = "T20, D20"
    target = ai_player.strategy.get_target(throw_number=1)
    assert target == ("Triple", 20)
    mock_get_suggestion.assert_called_with(100, "Double", 3, preferred_double=None)

    # Szenario 2: 40 Rest, 2 Darts -> D20
    ai_player.score = 40
    mock_get_suggestion.reset_mock()
    mock_get_suggestion.return_value = "D20"
    target = ai_player.strategy.get_target(throw_number=2)
    assert target == ("Double", 20)


@patch(
    "core.ai_strategy.CheckoutCalculator.get_checkout_suggestion",
    return_value="-",
)
def test_get_strategic_target_for_x01_no_checkout_path(mock_get_suggestion, x01_ai_player):
    """Testet die Zielauswahl, wenn kein Checkout-Pfad gefunden wird (Fallback)."""
    ai_player, mock_game = x01_ai_player
    ai_player.score = 169  # Kein 2-Dart-Finish

    target = ai_player.strategy.get_target(
        throw_number=2
    )  # 2 Darts übrig, sollte auf S19 zielen (150 Rest)
    assert target == (
        "Single",
        19,
    )  # KI sollte auf S19 zielen, um geraden Rest zu hinterlassen
    mock_get_suggestion.assert_any_call(169, "Double", 2, preferred_double=None)


def test_apply_strategic_offset(ai_player_with_mocks):
    """
    Testet, ob der strategische Offset korrekt angewendet wird, um auf den
    sichereren, inneren Teil eines Segments zu zielen.
    """
    ai_player, _ = ai_player_with_mocks
    # --- Szenario 1: Champion zielt auf T20 (vertikal oben) ---
    ai_player.difficulty = "Champion"

    # Ziel ist T20, direkt über dem Zentrum (250, 250)
    center_coords_t20 = (250, 50)

    new_coords = ai_player._apply_strategic_offset(center_coords_t20, "Triple")

    # Erwartung: Zielpunkt wird nach unten verschoben (Richtung Board-Mitte)
    assert new_coords[0] == 250
    assert new_coords[1] > center_coords_t20[1]

    # --- Szenario 2: Anfänger zielt auf D11 (horizontal rechts) ---
    ai_player.difficulty = "Anfänger"

    center_coords_d11 = (450, 250)
    new_coords_beginner = ai_player._apply_strategic_offset(center_coords_d11, "Double")

    # Erwartung: Zielpunkt wird nach links verschoben (Richtung Board-Mitte)
    assert new_coords_beginner[0] < center_coords_d11[0]
    assert new_coords_beginner[1] == 250

    # --- Szenario 3: Kein Offset für Single-Würfe ---
    no_offset_coords = ai_player._apply_strategic_offset(center_coords_t20, "Single")
    assert no_offset_coords == center_coords_t20


def test_get_strategic_target_for_cricket_opening(cricket_ai_player):
    """Testet die Zielauswahl für Cricket, wenn noch Ziele offen sind."""
    ai_player, _ = cricket_ai_player

    # KI hat noch nichts getroffen
    ai_player.state["hits"] = {}
    target = ai_player.strategy.get_target(throw_number=1)
    assert target == ("Triple", 20)

    # KI hat die 20 geschlossen und sollte nun auf die 19 zielen
    ai_player.state["hits"] = {"20": 3}
    target = ai_player.strategy.get_target(throw_number=1)
    assert target == ("Triple", 19)


def test_get_strategic_target_for_cricket_scoring(cricket_ai_player):
    """Testet die Zielauswahl für Cricket, wenn die eigenen Ziele geschlossen sind."""
    ai_player, mock_game = cricket_ai_player

    # Mock für einen Gegner, der die '19' noch nicht geschlossen hat
    mock_opponent = Mock(spec=Player)
    # Wichtig: state muss ein Dictionary sein, das 'hits' enthält,
    # damit der '>=' Vergleich in der Strategie funktioniert.
    mock_opponent.state = {
        "hits": {
            "20": 3,
            "19": 2,
            "18": 3,
            "17": 3,
            "16": 3,
            "15": 3,
            "Bull": 3,
        }
    }
    mock_opponent.hits = mock_opponent.state["hits"]  # Property simulieren

    # KI hat alle Ziele geschlossen
    ai_player.state["hits"] = {t: 3 for t in mock_game.game.get_targets()}
    mock_game.players = [ai_player, mock_opponent]

    # Die KI sollte nun versuchen, auf dem offenen Ziel '19' des Gegners zu punkten
    target = ai_player.strategy.get_target(throw_number=1)
    assert target == (
        "Triple",
        19,
    ), "KI sollte auf das höchste offene Ziel des Gegners punkten."


def test_get_strategic_target_for_cricket_defensive_move(cricket_ai_player):
    """Testet, ob die KI defensiv ein gefährliches Ziel des Gegners schließt."""
    ai_player, mock_game = cricket_ai_player

    # Gegner hat die 20 geschlossen und kann punkten.
    mock_opponent = Mock(spec=Player)
    mock_opponent.state = {
        "hits": {
            "20": 3,
            "19": 0,
            "18": 0,
            "17": 0,
            "16": 0,
            "15": 0,
            "Bull": 0,
        }
    }
    mock_opponent.hits = mock_opponent.state["hits"]

    # KI hat die 20 noch offen, aber die 19 schon zu.
    # Ohne defensive Logik würde die KI auf die 18 zielen.
    ai_player.state["hits"] = {
        "20": 1,
        "19": 3,
        "18": 0,
        "17": 0,
        "16": 0,
        "15": 0,
        "Bull": 0,
    }
    mock_game.players = [ai_player, mock_opponent]

    # Erwartung: Die KI muss defensiv die 20 schließen, um zu verhindern,
    # dass der Gegner weiter punktet.
    target = ai_player.strategy.get_target(throw_number=1)
    assert target == (
        "Triple",
        20,
    ), "KI sollte das gefährlichste offene Ziel des Gegners schließen."


def test_get_strategic_target_fallback(ai_player_with_mocks):
    """Testet die Fallback-Zielauswahl."""
    ai_player, mock_game = ai_player_with_mocks
    # Verwendet einen Spielmodus ohne implementierte Strategie
    ai_player.strategy = DefaultAIStrategy(ai_player)
    mock_game.options.name = "Unknown Game"
    target = ai_player.strategy.get_target(throw_number=1)
    assert target == ("Bullseye", 50)


# --- Tests for KillerAIStrategy ---


def test_killer_ai_determines_life_segment(killer_ai_player):
    """Testet, ob die KI ein freies, hohes Segment als Lebensfeld wählt."""
    ai_player, mock_game = killer_ai_player
    ai_player.state["life_segment"] = None

    # Opponent1 hat '19', Opponent2 hat '18'. KI sollte '20' wählen.
    target = ai_player.strategy.get_target(throw_number=1)
    assert target == ("Single", 20)


def test_killer_ai_avoids_taken_life_segment(killer_ai_player):
    """Testet, ob die KI ein bereits vergebenes Lebensfeld meidet."""
    ai_player, mock_game = killer_ai_player
    ai_player.state["life_segment"] = None

    # Blockiere die Top-Segmente
    mock_game.players[1].state["life_segment"] = "20"
    mock_game.players[2].state["life_segment"] = "19"

    target = ai_player.strategy.get_target(throw_number=1)
    # Da 20 und 19 belegt sind, sollte die KI auf 18 ausweichen.
    assert target == ("Single", 18)


def test_killer_ai_becomes_killer(killer_ai_player):
    """Testet, ob die KI auf ihr eigenes Lebensfeld zielt, um Killer zu werden."""
    ai_player, _ = killer_ai_player
    ai_player.state["life_segment"] = "17"
    ai_player.state["can_kill"] = False

    target = ai_player.strategy.get_target(throw_number=1)
    assert target == ("Double", 17)


def test_killer_ai_targets_opponent_with_most_lives(killer_ai_player):
    """Testet, ob die KI als Killer den Gegner mit den meisten Leben angreift."""
    ai_player, mock_game = killer_ai_player
    ai_player.state["life_segment"] = "20"
    ai_player.state["can_kill"] = True

    # Opponent1 hat 3 Leben, Opponent2 hat 2. KI sollte Opponent1 angreifen.
    # Das Lebensfeld von Opponent1 ist '19'.
    target = ai_player.strategy.get_target(throw_number=1)
    assert target == ("Double", 19)


def test_killer_ai_prioritizes_attacking_other_killers(killer_ai_player):
    """
    Testet, ob die KI als Killer vorrangig andere Killer angreift,
    auch wenn ein Nicht-Killer-Gegner mehr Leben hat.
    """
    ai_player, mock_game = killer_ai_player
    ai_player.state["life_segment"] = "20"
    ai_player.state["can_kill"] = True

    # Opponent1 (Nicht-Killer) hat mehr Leben als Opponent2 (Killer)
    mock_game.players[1].score = 5
    mock_game.players[1].state["can_kill"] = False
    mock_game.players[1].state["life_segment"] = "19"

    mock_game.players[2].score = 2
    mock_game.players[2].state["can_kill"] = True
    mock_game.players[2].state["life_segment"] = "18"

    # Die KI sollte den gefährlicheren Gegner (Opponent2) angreifen, obwohl er weniger Leben hat.
    target = ai_player.strategy.get_target(throw_number=1)

    # Das Lebensfeld von Opponent2 ist '18'.
    assert target == ("Double", 18)


# --- Tests for Adaptive AI Logic ---


def test_adaptive_ai_uses_specific_model(ai_player_with_mocks):
    """Testet, ob die adaptive KI das spezifische Modell für ein Ziel verwendet."""
    ai_player, _ = ai_player_with_mocks
    ai_player.difficulty = "Adaptive"

    # Ein detailliertes Modell für T20
    ai_player.profile.accuracy_model = {
        "T20": {
            "mean_offset_x": 10,
            "mean_offset_y": -5,
            "std_dev_x": 2,
            "std_dev_y": 3,
        }
    }
    target_coords = (100, 100)

    with patch("core.ai_player.random.gauss") as mock_gauss:
        mock_gauss.side_effect = lambda mean, std: mean  # Gibt den Mittelwert zurück
        throw_x, throw_y = ai_player._get_adaptive_throw_coords(target_coords, "T20")

    assert throw_x == 110  # 100 + 10
    assert throw_y == 95  # 100 - 5


def test_adaptive_ai_fallback_if_no_specific_model(ai_player_with_mocks):
    """Testet, ob die adaptive KI auf Standardwerte zurückfällt, wenn kein spezifisches Modell existiert."""
    ai_player, _ = ai_player_with_mocks
    ai_player.difficulty = "Adaptive"
    ai_player.profile.accuracy_model = {
        "T20": {
            "mean_offset_x": 10,
            "mean_offset_y": -5,
            "std_dev_x": 2,
            "std_dev_y": 3,
        }
    }
    target_coords = (150, 150)

    with patch("core.ai_player.random.gauss") as mock_gauss:
        mock_gauss.side_effect = lambda mean, std: mean
        throw_x, throw_y = ai_player._get_adaptive_throw_coords(target_coords, "T19")

    assert throw_x == 150
    assert throw_y == 150


def test_parse_target_string(ai_player_with_mocks):
    """Testet die Hilfsmethode zum Parsen von Ziel-Strings."""
    strategy_instance = ai_player_with_mocks[0].strategy
    assert strategy_instance._parse_target_string("T20") == ("Triple", 20)
    assert strategy_instance._parse_target_string("D18") == ("Double", 18)
    assert strategy_instance._parse_target_string("S1") == ("Single", 1)
    # Unterscheide klar zwischen dem 25er Bull und dem 50er Bullseye, konsistent mit dem Rest der App.
    assert strategy_instance._parse_target_string("BULL") == (
        "Bull",
        25,
    )  # Dieser Test schlug vorher fehl
    assert strategy_instance._parse_target_string("Bullseye") == (
        "Bullseye",
        50,
    )
    assert strategy_instance._parse_target_string("BE") == ("Bullseye", 50)
    assert strategy_instance._parse_target_string("17") == ("Single", 17)
    assert strategy_instance._parse_target_string("INVALID") == ("Triple", 20)


@patch(
    "core.ai_strategy.CheckoutCalculator.get_checkout_suggestion",
    return_value="-",
)
@patch("core.ai_player.random.uniform")
@patch("core.ai_player.math.cos")
@patch("core.ai_player.math.sin")
def test_execute_throw_simulates_click(
    mock_sin, mock_cos, mock_uniform, mock_get_suggestion, ai_player_with_mocks
):
    """Testet, ob _execute_throw einen Dartwurf korrekt simuliert."""
    ai_player, mock_game = ai_player_with_mocks
    mock_game.options.name = "501"  # Setze einen Spielmodus, um die Logik zu steuern

    # Konfiguriert die Mocks für vorhersagbare "Zufälligkeit"
    mock_uniform.side_effect = [1.5708, 10]  # Winkel = pi/2, Distanz = 10px
    mock_cos.return_value = 0  # cos(pi/2) ≈ 0
    mock_sin.return_value = 1  # sin(pi/2) = 1

    # Zielmitte ist (300, 300). Wurf-Offset ist x=0, y=10. Erwartet: x=300, y=310
    expected_x, expected_y = 300, 310

    # Patch the strategic offset method for this test to isolate the throw simulation
    with patch.object(
        ai_player,
        "_apply_strategic_offset",
        side_effect=lambda coords, ring: coords,
    ):
        # Führt den Wurf aus
        ai_player._execute_throw(1)

    # Verifiziert, dass die Klick-Simulation des Dartboards mit den korrekten Koordinaten aufgerufen wurde
    mock_game.dartboard.on_click_simulated.assert_called_once_with(expected_x, expected_y)


def test_execute_throw_stops_on_bust(ai_player_with_mocks):
    """Testet, ob die KI aufhört zu werfen, wenn der Zug vorbei ist (z.B. Bust)."""
    ai_player, mock_game = ai_player_with_mocks
    ai_player.turn_is_over = True  # Simuliert einen Bust

    ai_player._execute_throw(1)  # Versucht, den ersten Wurf auszuführen

    # Die KI sollte keinen Klick simulieren
    mock_game.dartboard.on_click_simulated.assert_not_called()
    # Die KI sollte sofort den nächsten Spieler aufrufen
    mock_game.dartboard.root.after.assert_called_once_with(
        ai_player.throw_delay, mock_game.next_player
    )


def test_take_turn_initiates_sequence(ai_player_with_mocks):
    """Testet, ob take_turn die Wurfsequenz startet."""
    ai_player, mock_game = ai_player_with_mocks
    ai_player.take_turn()
    # Es sollte der erste Wurf geplant werden
    mock_game.dartboard.root.after.assert_called_once_with(
        ai_player.throw_delay, ai_player._execute_throw, 1
    )
