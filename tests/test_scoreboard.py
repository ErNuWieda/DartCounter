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
from unittest.mock import MagicMock, patch

# Die zu testenden Klassen
from core.scoreboard import (
    BaseScoreBoard,
    X01ScoreBoard,
    TargetBasedScoreBoard,
    SplitScoreBoard,
    ScoreBoard,
    setup_scoreboards,
)


@pytest.fixture
def mock_player(tk_root_session):
    """
    Erstellt einen umfassenden Mock für ein Player-Objekt, der für die
    Initialisierung der Scoreboards benötigt wird.
    """
    player = MagicMock()
    player.name = "Alice"
    player.id = 1
    player.score = 301
    player.profile = None  # Standardmäßig kein Profil

    # Mock für das übergeordnete Game-Objekt
    mock_game = MagicMock()
    mock_game.options.name = "301"  # Standard-Spielmodus

    # Mock für die Spiellogik-Instanz innerhalb des Game-Objekts
    mock_game_logic = MagicMock()
    mock_game_logic.get_scoreboard_height.return_value = 400
    mock_game.game = mock_game_logic

    player.game = mock_game
    return player


@pytest.mark.ui
class TestBaseScoreBoard:
    """Testet die Funktionalität der BaseScoreBoard-Klasse."""

    def test_initialization(self, tk_root_session, mock_player):
        """Testet, ob das Fenster und die Basis-Widgets korrekt erstellt werden."""
        sb = BaseScoreBoard(tk_root_session, mock_player)
        sb.score_window.update()

        assert sb.score_window.winfo_exists()
        assert sb.score_window.title() == "Alice"
        assert sb.player == mock_player

        # Überprüfen, ob die Haupt-Widgets vorhanden sind
        assert isinstance(sb.indicator_label, MagicMock) or sb.indicator_label.winfo_exists()
        assert isinstance(sb.throws_list, MagicMock) or sb.throws_list.winfo_exists()

        sb.score_window.destroy()

    def test_set_active_state(self, tk_root_session, mock_player):
        """Testet, ob der aktive Zustand (Fenstertitel, Indikator) korrekt gesetzt wird."""
        sb = BaseScoreBoard(tk_root_session, mock_player)
        sb.score_window.update()

        # Test 1: Aktiv setzen
        sb.set_active(True)
        assert "► Alice ◄" in sb.score_window.title()
        # Die Farbe wird hier nicht direkt geprüft, da sie vom Theme abhängt.
        # Wir prüfen, ob die Konfiguration versucht wurde.
        assert str(sb.indicator_label.cget("background")) == "green"

        # Test 2: Inaktiv setzen
        sb.set_active(False)
        assert sb.score_window.title() == "Alice"
        # Prüfen, ob die Hintergrundfarbe auf den Standard zurückgesetzt wird
        assert str(sb.indicator_label.cget("background")) == str(sb.score_window.cget("bg"))

        sb.score_window.destroy()

    def test_update_score_updates_display(self, tk_root_session, mock_player):
        """Testet, ob update_score den Score und die Wurfliste aktualisiert."""
        sb = BaseScoreBoard(tk_root_session, mock_player)
        sb.score_window.update()

        # Simuliere Würfe
        mock_player.throws = [("Triple", 20, None), ("Single", 5, None)]

        sb.update_score(236)

        assert sb.score_var.get() == "236"
        # Prüfen, ob die Listbox die korrekten Einträge enthält
        assert sb.throws_list.size() == 2
        assert sb.throws_list.get(0) == "Triple 20"
        assert sb.throws_list.get(1) == "Single 5"

        sb.score_window.destroy()


@pytest.mark.ui
class TestX01ScoreBoard:
    """Testet die spezialisierte X01ScoreBoard-Klasse."""

    @pytest.fixture
    def x01_scoreboard(self, tk_root_session, mock_player):
        """Fixture zum Erstellen eines X01ScoreBoard."""
        # Mock-Methoden, die von X01ScoreBoard.update_score erwartet werden
        mock_player.get_average.return_value = 85.55
        mock_player.get_checkout_percentage.return_value = 33.3
        mock_player.stats = {"highest_finish": 120}
        mock_player.game.game.is_leg_set_match = False  # Standardmäßig kein Leg/Set-Match

        sb = X01ScoreBoard(tk_root_session, mock_player)
        sb.score_window.update()
        yield sb
        sb.score_window.destroy()

    def test_x01_extra_widgets_are_created(self, x01_scoreboard):
        """Testet, ob die X01-spezifischen Statistik-Labels erstellt werden."""
        sb = x01_scoreboard
        assert hasattr(sb, "avg_var")
        assert hasattr(sb, "hf_var")
        assert hasattr(sb, "co_var")
        assert hasattr(sb, "checkout_suggestion_var")

    def test_x01_update_score_updates_all_stats(self, x01_scoreboard, mock_player):
        """Testet, ob update_score alle X01-Statistiken aktualisiert."""
        sb = x01_scoreboard
        mock_player.throws = []  # Leere Würfe für diesen Test

        sb.update_score(140)

        assert sb.score_var.get() == "140"
        assert sb.avg_var.get() == "85.55"
        assert sb.hf_var.get() == "120"
        assert sb.co_var.get() == "33.3%"

    def test_update_checkout_suggestion(self, x01_scoreboard):
        """Testet, ob die Anzeige für den Finish-Vorschlag aktualisiert wird."""
        sb = x01_scoreboard
        sb.update_checkout_suggestion("T20, D20")
        assert sb.checkout_suggestion_var.get() == "T20, D20"


@pytest.mark.ui
class TestTargetBasedScoreBoard:
    """Testet die spezialisierte TargetBasedScoreBoard-Klasse."""

    @pytest.fixture
    def target_scoreboard(self, tk_root_session, mock_player):
        """Fixture zum Erstellen eines TargetBasedScoreBoard für Cricket."""
        # Konfiguriere den Mock-Spieler für ein Cricket-Spiel
        mock_player.game.options.name = "Cricket"
        # Das Scoreboard holt sich die Ziele vom Spieler-Objekt
        cricket_targets = ["20", "19", "18", "17", "16", "15", "Bull"]
        mock_player.targets = cricket_targets
        # Initialisiere die Treffer-Map des Spielers
        mock_player.hits = {target: 0 for target in cricket_targets}

        sb = TargetBasedScoreBoard(tk_root_session, mock_player)
        sb.score_window.update()
        yield sb
        sb.score_window.destroy()

    def test_target_widgets_are_created(self, target_scoreboard):
        """Testet, ob die Checkbutton-Variablen für die Cricket-Ziele korrekt erstellt werden."""
        sb = target_scoreboard
        assert hasattr(sb, "hit_check_vars")
        assert "20" in sb.hit_check_vars
        assert "Bull" in sb.hit_check_vars
        # Für Cricket sollte jedes Ziel 3 BooleanVars für die 3 Treffer haben
        assert len(sb.hit_check_vars["19"]) == 3

    def test_update_display_updates_checkbuttons(self, target_scoreboard, mock_player):
        """Testet, ob update_display die Checkboxen basierend auf den Treffern aktualisiert."""
        sb = target_scoreboard

        # Simuliere einen Spielzustand: 2 Treffer auf die 20, 3 auf die 19
        mock_player.hits = {"20": 2, "19": 3}

        # Rufe die zu testende Methode auf
        sb.update_display(mock_player.hits, 0)

        # Überprüfe den Zustand der BooleanVars
        assert sb.hit_check_vars["20"][0].get() is True
        assert sb.hit_check_vars["20"][1].get() is True
        assert sb.hit_check_vars["20"][2].get() is False  # Der dritte ist noch offen
        assert all(var.get() for var in sb.hit_check_vars["19"])  # Alle 3 sollten True sein


@pytest.mark.parametrize(
    "game_mode, expected_class_name",
    [
        ("501", "X01ScoreBoard"),
        ("Cricket", "TargetBasedScoreBoard"),
        ("Around the Clock", "TargetBasedScoreBoard"),
        ("Shanghai", "TargetBasedScoreBoard"),
        ("Split Score", "SplitScoreBoard"),
        ("Killer", "ScoreBoard"),
        ("Elimination", "ScoreBoard"),
    ],
)
def test_setup_scoreboards_selects_correct_class(game_mode, expected_class_name):
    """
    Testet, ob die Factory-Funktion `setup_scoreboards` die korrekte
    Scoreboard-Klasse für den jeweiligen Spielmodus auswählt.
    """
    # 1. Mock für den Game-Controller erstellen
    mock_game_controller = MagicMock()
    mock_game_controller.options.name = game_mode
    mock_game_controller.players = [MagicMock()]  # Ein Spieler reicht für den Test
    mock_game_controller.dartboard.root.winfo_exists.return_value = True
    mock_game_controller.game.get_scoreboard_height.return_value = 300

    # 2. Alle möglichen Scoreboard-Klassen patchen
    with patch("core.scoreboard.X01ScoreBoard") as MockX01, patch(
        "core.scoreboard.TargetBasedScoreBoard"
    ) as MockTarget, patch("core.scoreboard.SplitScoreBoard") as MockSplit, patch(
        "core.scoreboard.ScoreBoard"
    ) as MockDefault:
        # Map von Klassennamen (Strings) zu den Mock-Objekten
        mock_map = {
            "X01ScoreBoard": MockX01,
            "TargetBasedScoreBoard": MockTarget,
            "SplitScoreBoard": MockSplit,
            "ScoreBoard": MockDefault,
        }

        # 3. Die zu testende Funktion aufrufen
        setup_scoreboards(mock_game_controller)

        # 4. Überprüfen, ob die ERWARTETE Klasse instanziiert wurde
        expected_mock = mock_map[expected_class_name]
        expected_mock.assert_called_once()

        # 5. Überprüfen, ob KEINE der anderen Klassen instanziiert wurde
        for name, mock_class in mock_map.items():
            if name != expected_class_name:
                mock_class.assert_not_called()
