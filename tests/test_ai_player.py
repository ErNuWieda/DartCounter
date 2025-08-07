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

# Fügt das Hauptverzeichnis zum Python-Pfad hinzu, damit die core-Module gefunden werden.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.ai_player import AIPlayer
from core.player_profile import PlayerProfile
from core.player import Player
from core.game import Game
from core.checkout_calculator import CheckoutCalculator

@pytest.fixture
def ai_player_with_mocks():
    """
    Eine pytest-Fixture, die eine AIPlayer-Instanz mit allen notwendigen Mocks einrichtet.
    """
    mock_game = Mock(spec=Game)
    mock_game.dartboard = Mock()
    mock_game.dartboard.root = Mock()
    mock_game.dartboard.root.winfo_exists.return_value = True # Wichtig für .after()
    mock_game.dartboard.skaliert = {
        'triple_outer': 520, 'triple_inner': 470,
        'double_outer': 835, 'double_inner': 785
    }
    mock_game.dartboard.center_x = 250
    mock_game.dartboard.center_y = 250
    mock_game.dartboard.get_coords_for_target.return_value = (300, 300)

    mock_game.targets = [] # Fehlendes Attribut hinzufügen
    mock_game.game = Mock()
    mock_game.end = False
    mock_game.options = Mock() # Wichtig für die Strategie-Logik

    ai_profile = PlayerProfile(
        name="RoboCop",
        is_ai=True,
        difficulty='Fortgeschritten'
    )

    ai_player = AIPlayer(name="RoboCop", game=mock_game, profile=ai_profile)
    ai_player.score = 501
    ai_player.turn_is_over = False

    mock_game.players = [ai_player]

    return ai_player, mock_game

def test_initialization(ai_player_with_mocks):
    """Testet, ob der AIPlayer korrekt initialisiert wird."""
    ai_player, _ = ai_player_with_mocks
    assert isinstance(ai_player, AIPlayer)
    assert ai_player.is_ai()
    assert ai_player.name == "RoboCop"
    assert ai_player.difficulty == 'Fortgeschritten'
    assert 'radius' in ai_player.settings
    assert ai_player.settings['radius'] == 60
    assert ai_player.settings['delay'] == 1200

def test_get_strategic_target_for_x01_high_score(ai_player_with_mocks):
    """Testet die Zielauswahl für X01 bei hohem Punktestand (kein Finish)."""
    ai_player, mock_game = ai_player_with_mocks
    mock_game.options.name = "501"
    ai_player.score = 171 # Knapp über dem Finish-Bereich
    target = ai_player._get_strategic_target(throw_number=1)
    assert target == ("Triple", 20)

@patch('core.ai_player.CheckoutCalculator.get_checkout_suggestion')
def test_get_strategic_target_for_x01_checkout_path(mock_get_suggestion, ai_player_with_mocks):
    """Testet die Zielauswahl, wenn ein Checkout-Pfad verfügbar ist."""
    ai_player, mock_game = ai_player_with_mocks
    mock_game.options.name = "501"
    mock_game.options.opt_out = "Double"
    
    # Szenario 1: 100 Rest, 3 Darts -> T20, D20
    ai_player.score = 100
    mock_get_suggestion.return_value = "T20, D20"
    target = ai_player._get_strategic_target(throw_number=1)
    assert target == ("Triple", 20)
    mock_get_suggestion.assert_called_once_with(100, "Double", 3)

    # Szenario 2: 40 Rest, 2 Darts -> D20
    ai_player.score = 40
    mock_get_suggestion.reset_mock()
    mock_get_suggestion.return_value = "D20"
    target = ai_player._get_strategic_target(throw_number=2)
    assert target == ("Double", 20)
    mock_get_suggestion.assert_called_once_with(40, "Double", 2)

@patch('core.ai_player.CheckoutCalculator.get_checkout_suggestion')
def test_get_strategic_target_for_x01_no_checkout_path(mock_get_suggestion, ai_player_with_mocks):
    """Testet die Zielauswahl, wenn kein Checkout-Pfad gefunden wird (Fallback)."""
    ai_player, mock_game = ai_player_with_mocks
    mock_game.options.name = "501"
    ai_player.score = 169 # Kein 2-Dart-Finish
    mock_game.options.opt_out = "Double"
    mock_get_suggestion.return_value = "Kein Finish möglich"

    target = ai_player._get_strategic_target(throw_number=2) # 2 Darts übrig
    assert target == ("Triple", 20) # Fallback auf Standardstrategie
    mock_get_suggestion.assert_called_once_with(169, "Double", 2)

@patch('core.ai_player.CheckoutCalculator.get_checkout_suggestion')
def test_get_strategic_target_for_x01_setup_throw(mock_get_suggestion, ai_player_with_mocks):
    """Testet, ob die KI einen intelligenten Setup-Wurf wählt, wenn kein Finish möglich ist."""
    ai_player, mock_game = ai_player_with_mocks
    mock_game.options.name = "501"
    mock_game.options.opt_out = "Double"
    ai_player.score = 59 # Ein klassischer Setup-Score
    mock_get_suggestion.return_value = "-" # Simuliert, dass kein direkter Checkout möglich ist

    # Die KI sollte versuchen, S19 zu treffen, um 40 (D20) zu lassen.
    target = ai_player._get_strategic_target(throw_number=1)
    
    assert target == ("Single", 19)
    mock_get_suggestion.assert_called_once_with(59, "Double", 3)

def test_apply_strategic_offset(ai_player_with_mocks):
    """
    Testet, ob der strategische Offset korrekt angewendet wird, um auf den
    sichereren, inneren Teil eines Segments zu zielen.
    """
    ai_player, _ = ai_player_with_mocks
    # --- Szenario 1: Champion zielt auf T20 (vertikal oben) ---
    ai_player.difficulty = 'Champion'
    ai_player.settings = ai_player.DIFFICULTY_SETTINGS['Champion']
    
    # Ziel ist T20, direkt über dem Zentrum (250, 250)
    center_coords_t20 = (250, 50) 
    
    new_coords = ai_player._apply_strategic_offset(center_coords_t20, "Triple")
    
    # Erwartung: Zielpunkt wird nach unten verschoben (Richtung Board-Mitte)
    assert new_coords[0] == 250
    assert new_coords[1] > center_coords_t20[1]
    
    # --- Szenario 2: Anfänger zielt auf D11 (horizontal rechts) ---
    ai_player.difficulty = 'Anfänger'
    ai_player.settings = ai_player.DIFFICULTY_SETTINGS['Anfänger']
    
    center_coords_d11 = (450, 250)
    new_coords_beginner = ai_player._apply_strategic_offset(center_coords_d11, "Double")
    
    # Erwartung: Zielpunkt wird nach links verschoben (Richtung Board-Mitte)
    assert new_coords_beginner[0] < center_coords_d11[0]
    assert new_coords_beginner[1] == 250
    
    # --- Szenario 3: Kein Offset für Single-Würfe ---
    no_offset_coords = ai_player._apply_strategic_offset(center_coords_t20, "Single")
    assert no_offset_coords == center_coords_t20

def test_get_strategic_target_for_cricket_opening(ai_player_with_mocks):
    """Testet die Zielauswahl für Cricket, wenn noch Ziele offen sind."""
    ai_player, mock_game = ai_player_with_mocks
    mock_game.options.name = "Cricket"
    mock_game.game.get_targets.return_value = ['20', '19', '18', '17', '16', '15', 'Bull']
    
    # KI hat noch nichts getroffen
    ai_player.state['hits'] = {}
    target = ai_player._get_strategic_target(throw_number=1)
    assert target == ("Triple", 20)

    # KI hat die 20 geschlossen und sollte nun auf die 19 zielen
    ai_player.state['hits'] = {'20': 3}
    target = ai_player._get_strategic_target(throw_number=1)
    assert target == ("Triple", 19)

def test_get_strategic_target_for_cricket_scoring(ai_player_with_mocks):
    """Testet die Zielauswahl für Cricket, wenn die eigenen Ziele geschlossen sind."""
    ai_player, mock_game = ai_player_with_mocks
    mock_game.options.name = "Cricket"
    targets = ['20', '19', 'Bull']
    mock_game.game.get_targets.return_value = targets

    # Mock für einen Gegner, der die '19' noch nicht geschlossen hat
    mock_opponent = Mock(spec=Player)
    mock_opponent.state = {'hits': {'20': 3, '19': 2, 'Bull': 3}}
    
    # KI hat alle Ziele geschlossen
    ai_player.state['hits'] = {'20': 3, '19': 3, 'Bull': 3}
    mock_game.players = [ai_player, mock_opponent]

    # Die KI sollte nun versuchen, auf dem offenen Ziel '19' des Gegners zu punkten
    target = ai_player._get_strategic_target(throw_number=1)
    assert target == ("Triple", 19)

def test_get_strategic_target_for_cricket_defensive_move(ai_player_with_mocks):
    """Testet, ob die KI defensiv ein gefährliches Ziel des Gegners schließt."""
    ai_player, mock_game = ai_player_with_mocks
    mock_game.options.name = "Cricket"
    targets = ['20', '19', '18', 'Bull']
    mock_game.game.get_targets.return_value = targets

    # Gegner hat die 20 geschlossen und kann punkten.
    mock_opponent = Mock(spec=Player)
    mock_opponent.state = {'hits': {'20': 3, '19': 0, '18': 0, 'Bull': 0}}
    
    # KI hat die 20 noch offen, aber die 19 schon zu.
    # Ohne defensive Logik würde die KI auf die 18 zielen.
    ai_player.state['hits'] = {'20': 1, '19': 3, '18': 0, 'Bull': 0}
    mock_game.players = [ai_player, mock_opponent]

    # Erwartung: Die KI muss defensiv die 20 schließen, um zu verhindern,
    # dass der Gegner weiter punktet.
    target = ai_player._get_strategic_target(throw_number=1)
    assert target == ("Triple", 20)

def test_get_strategic_target_fallback(ai_player_with_mocks):
    """Testet die Fallback-Zielauswahl."""
    ai_player, mock_game = ai_player_with_mocks
    # Verwendet einen Spielmodus ohne implementierte Strategie
    mock_game.options.name = "Unknown Game"
    target = ai_player._get_strategic_target(throw_number=1)
    assert target == ("Bullseye", 50)

def test_parse_target_string(ai_player_with_mocks):
    """Testet die Hilfsmethode zum Parsen von Ziel-Strings."""
    ai_player, _ = ai_player_with_mocks
    assert ai_player._parse_target_string("T20") == ("Triple", 20)
    assert ai_player._parse_target_string("D18") == ("Double", 18)
    assert ai_player._parse_target_string("S1") == ("Single", 1)
    assert ai_player._parse_target_string("BULL") == ("Bullseye", 50)
    assert ai_player._parse_target_string("Bullseye") == ("Bullseye", 50)
    assert ai_player._parse_target_string("17") == ("Single", 17)
    assert ai_player._parse_target_string("INVALID") == ("Triple", 20)

@patch('core.ai_player.CheckoutCalculator.get_checkout_suggestion', return_value='-')
@patch('core.ai_player.random.uniform')
@patch('core.ai_player.math.cos')
@patch('core.ai_player.math.sin')
def test_execute_throw_simulates_click(mock_sin, mock_cos, mock_uniform, mock_get_suggestion, ai_player_with_mocks):
    """Testet, ob _execute_throw einen Dartwurf korrekt simuliert."""
    ai_player, mock_game = ai_player_with_mocks
    mock_game.options.name = "501" # Setze einen Spielmodus, um die Logik zu steuern

    # Konfiguriert die Mocks für vorhersagbare "Zufälligkeit"
    mock_uniform.side_effect = [1.5708, 10]  # Winkel = pi/2, Distanz = 10px
    mock_cos.return_value = 0  # cos(pi/2) ≈ 0
    mock_sin.return_value = 1  # sin(pi/2) = 1

    # Zielmitte ist (300, 300). Wurf-Offset ist x=0, y=10.
    # Erwartete Wurfkoordinaten: x=300, y=310
    expected_x, expected_y = 300, 310

    # Patch the strategic offset method for this test to isolate the throw simulation
    with patch.object(ai_player, '_apply_strategic_offset', side_effect=lambda coords, ring: coords):
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
        ai_player.settings['delay'],
        mock_game.next_player
    )

def test_take_turn_initiates_sequence(ai_player_with_mocks):
    """Testet, ob take_turn die Wurfsequenz startet."""
    ai_player, mock_game = ai_player_with_mocks
    ai_player.take_turn()
    # Es sollte der erste Wurf geplant werden
    mock_game.dartboard.root.after.assert_called_once_with(
        ai_player.settings['delay'],
        ai_player._execute_throw,
        1
    )