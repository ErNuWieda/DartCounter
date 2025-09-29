# Dartcounter Deluxe
# Copyright (C) 2025 Martin Hehl (airnooweeda)
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

import tkinter as tk
import pytest
from unittest.mock import MagicMock, ANY, patch
from datetime import datetime
from tkinter import ttk

from core.player_stats_manager import PlayerStatsManager


@pytest.fixture
def mock_db_manager():
    """Fixture für einen gemockten DatabaseManager."""
    return MagicMock()


@pytest.fixture
def stats_manager(mock_db_manager):
    """Fixture, die eine PlayerStatsManager-Instanz mit einem Mock-DB-Manager erstellt."""
    return PlayerStatsManager(mock_db_manager)


class TestPlayerStatsManagerLogic:
    """
    Testet die reine Daten- und Berechnungslogik des PlayerStatsManager,
    isoliert von der UI.
    """

    def test_add_game_record_calls_db_manager(self, stats_manager, mock_db_manager):
        """
        Testet, ob `add_game_record` die korrekte Methode des DB-Managers
        mit einem hinzugefügten Zeitstempel aufruft.
        """
        player_name = "Alice"
        game_stats = {"game_mode": "501", "win": True, "average": 85.5}

        stats_manager.add_game_record(player_name, game_stats)

        # Überprüfen, ob die DB-Methode aufgerufen wurde
        mock_db_manager.add_game_record.assert_called_once()

        # Überprüfen der Argumente, die an die DB-Methode übergeben wurden
        call_args, _ = mock_db_manager.add_game_record.call_args
        assert call_args[0] == player_name
        # Das zweite Argument sollte das game_stats-Dict sein, ergänzt um das Datum
        assert call_args[1]["game_mode"] == "501"
        assert "date" in call_args[1]
        assert isinstance(call_args[1]["date"], datetime)

    def test_add_game_record_db_disconnected(self, stats_manager, mock_db_manager):
        """
        Testet, dass nichts passiert, wenn die DB nicht verbunden ist.
        """
        mock_db_manager.is_connected = False
        stats_manager.add_game_record("Bob", {"game_mode": "301", "win": False})
        mock_db_manager.add_game_record.assert_not_called()

    def test_get_all_player_names(self, stats_manager, mock_db_manager):
        """
        Testet, ob `get_all_player_names` den Aufruf korrekt an den DB-Manager delegiert.
        """
        expected_names = ["Alice", "Bob", "Charlie"]
        mock_db_manager.get_all_player_names_from_records.return_value = expected_names

        names = stats_manager.get_all_player_names()

        assert names == expected_names
        mock_db_manager.get_all_player_names_from_records.assert_called_once()

    @pytest.mark.parametrize(
        "records, expected_streak",
        [
            ([], 0),  # Leere Liste
            ([{"is_win": True}], 1),  # Einzelner Sieg
            ([{"is_win": False}], 0),  # Einzelne Niederlage
            (
                [{"is_win": True}, {"is_win": True}, {"is_win": False}, {"is_win": True}],
                2,
            ),  # Streak am Anfang
            (
                [{"is_win": False}, {"is_win": True}, {"is_win": True}, {"is_win": True}],
                3,
            ),  # Streak am Ende
            (
                [
                    {"is_win": True},
                    {"is_win": False},
                    {"is_win": True},
                    {"is_win": True},
                ],
                2,
            ),  # Streak in der Mitte
        ],
    )
    def test_calculate_streaks(self, stats_manager, records, expected_streak):
        """Testet die Logik zur Berechnung von Siegesserien mit verschiedenen Szenarien."""
        # Die Datensätze müssen für den Test mit einem Datum versehen werden
        for i, rec in enumerate(records):
            rec["game_date"] = datetime(2024, 1, i + 1)

        result = stats_manager._calculate_streaks(records)
        assert result["best_win_streak"] == expected_streak


@pytest.mark.ui
class TestPlayerStatsManagerUI:
    """Testet die UI-Logik des PlayerStatsManager, insbesondere das Statistik-Fenster."""

    # Nutze die session-weite, unsichtbare tk_root_session Fixture aus conftest.py
    # anstelle einer eigenen Tk-Instanz pro Testklasse.
    # Dies wird automatisch an die Methoden übergeben, die es benötigen.
    # Wir müssen es hier nur deklarieren, damit pytest es erkennt.

    @pytest.fixture(autouse=True)
    def setup_method(self, tk_root_session, monkeypatch):
        """Richtet vor jedem Test eine saubere Umgebung mit Mocks ein."""
        # Mocke matplotlib, um die Erstellung echter Diagramme zu verhindern
        patcher_matplotlib = patch("core.player_stats_manager.MATPLOTLIB_AVAILABLE", True)
        self.mock_matplotlib = patcher_matplotlib.start()

        patcher_figure = patch("core.player_stats_manager.Figure")
        self.mock_figure = patcher_figure.start()

        patcher_canvas = patch("core.player_stats_manager.FigureCanvasTkAgg")
        self.mock_canvas = patcher_canvas.start()

        # Mocke messagebox, um Dialoge abzufangen
        patcher_messagebox = patch("core.player_stats_manager.messagebox")
        self.mock_messagebox = patcher_messagebox.start()

        # Mocke den DatabaseManager
        self.mock_db_manager = MagicMock()
        self.mock_db_manager.is_connected = True  # Standardmäßig verbunden

        # Erstelle die zu testende Instanz
        self.stats_manager = PlayerStatsManager(self.mock_db_manager)
        self.windows_to_destroy = []
        self.root = tk_root_session
        yield
        # --- Teardown ---
        patcher_matplotlib.stop()
        patcher_figure.stop()
        patcher_canvas.stop()
        patcher_messagebox.stop()
        for window in self.windows_to_destroy:
            if window and window.winfo_exists():
                window.destroy()

    def test_show_stats_window_db_disconnected(self, setup_method):
        """Testet, dass bei fehlender DB-Verbindung eine Fehlermeldung angezeigt wird."""
        self.mock_db_manager.is_connected = False
        self.stats_manager.show_stats_window(self.root)
        self.mock_messagebox.showerror.assert_called_once()

    def test_show_stats_window_loads_players_into_combobox(self, setup_method):
        """
        Testet, ob das Statistik-Fenster erstellt wird und die Spielernamen
        aus der Datenbank korrekt in die Combobox geladen werden.
        """
        # Mock-Daten, die von der DB zurückgegeben werden
        expected_players = ["Alice", "Bob", "Charlie"]
        self.mock_db_manager.get_all_player_names_from_records.return_value = expected_players

        # Öffne das Fenster
        win = self.stats_manager.show_stats_window(self.root)
        self.windows_to_destroy.append(win)
        win.update()  # Wichtig, damit Widgets gezeichnet werden

        # Finde die Combobox im Fenster
        player_combo = None
        for widget in win.winfo_children():
            # Wir müssen rekursiv suchen, da die Combobox in einem Frame ist
            for sub_widget in widget.winfo_children():
                if isinstance(sub_widget, ttk.Combobox):
                    player_combo = sub_widget
                    break
            if player_combo:
                break

        assert player_combo is not None, "Spieler-Combobox wurde nicht gefunden."
        # Überprüfe, ob die Werte in der Combobox mit den Mock-Daten übereinstimmen
        assert list(player_combo["values"]) == expected_players

    def test_player_selection_updates_stats(self, setup_method):
        """
        Testet, ob die Auswahl eines Spielers in der Combobox die Statistik-Anzeige aktualisiert.
        """
        # 1. Mock-Daten für die DB-Aufrufe vorbereiten
        self.mock_db_manager.get_all_player_names_from_records.return_value = ["Alice", "Bob"]
        # Die `get_records_for_player` Methode wird von `_update_stats_display` aufgerufen,
        # die wir hier patchen. Daher müssen wir ihren Return-Value nicht mocken.

        # 2. Fenster öffnen
        win = self.stats_manager.show_stats_window(self.root)
        self.windows_to_destroy.append(win)
        win.update()

        # 3. Die interne Update-Methode patchen, um ihren Aufruf zu überprüfen
        # KORREKTUR: Wir patchen nicht eine nicht-existente Methode, sondern prüfen,
        # ob der Event-Handler die korrekte DB-Abfrage auslöst.
        # 4. Die Combobox finden und die Auswahl eines Spielers simulieren
        player_combo = None
        for widget in win.winfo_children():
            if isinstance(widget, ttk.Frame):
                for sub_widget in widget.winfo_children():
                    if isinstance(sub_widget, ttk.Combobox):
                        player_combo = sub_widget
                        break
            if player_combo:
                break
        assert player_combo is not None, "Spieler-Combobox konnte nicht gefunden werden."
        player_combo.set("Bob")
        # Das Event auslösen, das an die Combobox gebunden ist
        player_combo.event_generate("<<ComboboxSelected>>")
        # UI-Events verarbeiten, damit der Callback ausgeführt wird
        win.update_idletasks()

        # 5. Überprüfen, ob die korrekte DB-Methode aufgerufen wurde
        self.mock_db_manager.get_records_for_player.assert_called_once_with("Bob")

