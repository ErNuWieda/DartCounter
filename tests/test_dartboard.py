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
import math
from unittest.mock import Mock, MagicMock, patch
from core.dartboard import DartBoard
from core.player import Player
from core.throw_result import ThrowResult


@pytest.fixture
def dartboard_instance(tk_root_session):
    """
    Erstellt eine echte DartBoard-Instanz für Tests.
    Das tk_root_session-Fixture stellt sicher, dass ein gültiges, aber
    unsichtbares Tkinter-Fenster für die Canvas-Erstellung existiert.
    """
    # Mocke die Game-Instanz, die vom DartBoard-Konstruktor benötigt wird
    mock_game = Mock()
    mock_game.options.name = "Test"
    mock_game.root = tk_root_session
    # Mock den on_throw_processed Callback, der von der Game-Klasse übergeben wird
    mock_game.on_throw_processed = MagicMock()
    # Mock den aktuellen Spieler
    mock_game.current_player.return_value = MagicMock(spec=Player, throws=[])

    # Erstelle die DartBoard-Instanz. Der __init__-Konstruktor ruft
    # _create_board auf, was die notwendigen Attribute wie `canvas`,
    # `center_x`, `center_y` und `skaliert` initialisiert.
    db = DartBoard(mock_game, parent_root=tk_root_session)
    yield db
    # Das Fenster wird vom tk_root_session-Fixture am Ende des Testlaufs zerstört.


def get_coords_from_polar(dartboard, angle_deg, radius_px):
    """Hilfsfunktion zur Umrechnung von Polarkoordinaten in kartesische Canvas-Koordinaten."""
    angle_rad = math.radians(angle_deg)
    center_x = dartboard.center_x
    center_y = dartboard.center_y
    # Die y-Koordinate wird subtrahiert, da die y-Achse im Canvas nach unten zeigt.
    x = center_x + radius_px * math.cos(angle_rad)
    y = center_y - radius_px * math.sin(angle_rad)
    return int(x), int(y)


@pytest.mark.parametrize(
    "description, get_test_coords, expected_ring, expected_segment",
    [
        (
            "Mitte des T20-Feldes (exakt 90 Grad)",
            lambda db: get_coords_from_polar(
                db, 90, (db.skaliert["triple_inner"] + db.skaliert["triple_outer"]) / 2
            ),
            "Triple",
            20,
        ),
        (
            "Grenze 20/1 (innerhalb von 1)",
            lambda db: get_coords_from_polar(
                db, 80.5, (db.skaliert["triple_inner"] + db.skaliert["triple_outer"]) / 2
            ),
            "Triple",
            1,
        ),
        (
            "Grenze 20/1 (innerhalb von 20)",
            lambda db: get_coords_from_polar(
                db, 81.5, (db.skaliert["triple_inner"] + db.skaliert["triple_outer"]) / 2
            ),
            "Triple",
            20,
        ),
        (
            "Mitte des D3-Feldes (exakt 270 Grad)",
            lambda db: get_coords_from_polar(
                db, 270, (db.skaliert["double_inner"] + db.skaliert["double_outer"]) / 2
            ),
            "Double",
            3,
        ),
        (
            "Mitte des S6-Feldes (exakt 0 Grad)",
            lambda db: get_coords_from_polar(
                db, 0, (db.skaliert["bull"] + db.skaliert["triple_inner"]) / 2
            ),
            "Single",
            6,
        ),
        ("Bullseye (genaues Zentrum)", lambda db: (db.center_x, db.center_y), "Bullseye", 50),
        (
            "Bull (knapp außerhalb des Bullseye)",
            lambda db: get_coords_from_polar(db, 45, db.skaliert["bullseye"] + 2),
            "Bull",
            25,
        ),
        (
            "Null-Punkte-Ring (zwischen Double und Rand)",
            lambda db: get_coords_from_polar(
                db, 180, (db.skaliert["double_outer"] + db.skaliert["outer_edge"]) / 2
            ),
            "Miss",  # Korrigiert: Dieser Bereich wird nun als Miss gewertet.
            0,       # Der Punktwert bleibt 0.
        ),
        ("Miss (knapp außerhalb des Boards)", lambda db: (db.center_x - db.skaliert["outer_edge"] - 5, db.center_y), "Miss", 0),
    ],
)
def test_hit_detection_precision(
    dartboard_instance, description, get_test_coords, expected_ring, expected_segment
):
    """
    Testet die Präzision der Treffererkennung an verschiedenen kritischen Punkten.
    """
    coords = get_test_coords(dartboard_instance)
    ring, segment = dartboard_instance.get_ring_segment(coords[0], coords[1])

    assert ring == expected_ring, f"Fehler bei '{description}': Falscher Ring"
    assert segment == expected_segment, f"Fehler bei '{description}': Falsches Segment"


@pytest.mark.ui
class TestDartboardInteractions:
    """Testet die UI-Interaktionen des Dartboards wie Button-Klicks und Fenster-Events."""

    def test_on_click_calls_game_throw(self, dartboard_instance):
        """Testet, ob ein Klick auf das Canvas die throw-Methode des Spiels aufruft."""
        db = dartboard_instance
        mock_game = db.spiel

        # Simuliere einen Klick-Event
        mock_event = MagicMock()
        mock_event.x = 300
        mock_event.y = 150

        # Mocke die Treffererkennung, um den Test zu isolieren
        db.get_ring_segment = MagicMock(return_value=("Triple", 20))

        db.on_click(mock_event)

        # Überprüfe, ob spiel.throw mit den korrekten, normalisierten Koordinaten aufgerufen wurde
        canvas_width = db.canvas.winfo_width()
        canvas_height = db.canvas.winfo_height()
        expected_norm_x = 300 / canvas_width
        expected_norm_y = 150 / canvas_height

        mock_game.throw.assert_called_once_with(
            "Triple", 20, (expected_norm_x, expected_norm_y)
        )

    def test_quit_game_when_game_is_over(self, dartboard_instance):
        """Testet, ob das Fenster ohne Nachfrage schließt, wenn das Spiel bereits beendet ist."""
        db = dartboard_instance
        db.spiel.end = True  # Spiel ist vorbei

        with patch("core.dartboard.ui_utils.ask_question") as mock_ask:
            db.quit_game()
            mock_ask.assert_not_called()
            db.spiel.destroy.assert_called_once()

    def test_quit_game_save_confirmed(self, dartboard_instance):
        """Testet den "Speichern und Beenden"-Pfad."""
        db = dartboard_instance
        db.spiel.end = False
        db.spiel.is_tournament_match = False

        with patch("core.dartboard.ui_utils.ask_question", return_value=True) as mock_ask, patch(
            "core.dartboard.SaveLoadManager.save_state", return_value=True
        ) as mock_save:
            db.quit_game()

            mock_ask.assert_called_once()
            mock_save.assert_called_once()
            db.spiel.destroy.assert_called_once()

    def test_quit_game_no_save_confirmed(self, dartboard_instance):
        """Testet den "Nicht Speichern und Beenden"-Pfad."""
        db = dartboard_instance
        db.spiel.end = False
        db.spiel.is_tournament_match = False

        with patch("core.dartboard.ui_utils.ask_question", return_value=False) as mock_ask, patch(
            "core.dartboard.SaveLoadManager.save_state"
        ) as mock_save:
            db.quit_game()

            mock_ask.assert_called_once()
            mock_save.assert_not_called()
            db.spiel.destroy.assert_called_once()

    def test_quit_game_cancelled(self, dartboard_instance):
        """Testet, was passiert, wenn der Benutzer den Dialog abbricht."""
        db = dartboard_instance
        db.spiel.end = False
        db.spiel.is_tournament_match = False

        with patch("core.dartboard.ui_utils.ask_question", return_value=None) as mock_ask:
            db.quit_game()
            mock_ask.assert_called_once()
            db.spiel.destroy.assert_not_called()

    @pytest.mark.parametrize(
        "num_throws, turn_is_over, game_is_over, expected_done_state, expected_undo_state",
        [
            (0, False, False, "disabled", "disabled"),  # Rundenstart
            (1, False, False, "disabled", "normal"),  # Ein Wurf gemacht
            (2, False, False, "disabled", "normal"),  # Zwei Würfe gemacht
            (3, False, False, "normal", "normal"),  # Drei Würfe gemacht
            (2, True, False, "normal", "normal"),  # Bust nach 2 Würfen
            (2, False, True, "normal", "normal"),  # Spielgewinn nach 2 Würfen
        ],
    )
    def test_update_button_states(
        self, dartboard_instance, num_throws, turn_is_over, game_is_over, expected_done_state, expected_undo_state
    ):
        """Testet die Logik zur Aktivierung/Deaktivierung der Buttons."""
        db = dartboard_instance
        db.spiel.end = game_is_over
        db.spiel.current_player.return_value.throws = [("T", 20, None)] * num_throws
        db.spiel.current_player.return_value.turn_is_over = turn_is_over

        db.update_button_states()

        assert str(db.done_button.cget("state")) == expected_done_state
        assert str(db.undo_button.cget("state")) == expected_undo_state