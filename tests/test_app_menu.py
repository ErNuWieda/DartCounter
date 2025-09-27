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
import tkinter as tk
from unittest.mock import MagicMock

# Die zu testende Klasse
from core.app_menu import AppMenu


@pytest.fixture
def tk_root():
    """Fixture zum Erstellen und Zerstören eines tk-Root-Fensters."""
    root = tk.Tk()
    root.withdraw()  # Fenster ausblenden
    yield root
    if root.winfo_exists():
        root.destroy()


@pytest.fixture
def menu_setup(tk_root):
    """Richtet die AppMenu mit einem Mock-Controller für den Test ein."""
    # Erstelle einen Mock-Controller mit allen Methoden, die das Menü aufrufen wird
    mock_controller = MagicMock()
    # Instanziiere die AppMenu mit der echten Wurzel und dem Mock-Controller
    AppMenu(tk_root, mock_controller, db_available=True)
    yield tk_root, mock_controller


class TestAppMenu:
    """Testet die AppMenu-Klasse."""

    def test_initialization_creates_menu(self, menu_setup):
        """Testet, ob das Menü erfolgreich erstellt und an das Root-Fenster angehängt wird."""
        tk_root, _ = menu_setup
        # Wir können prüfen, ob das Root-Fenster ein Menü konfiguriert hat.
        assert tk_root.cget("menu") != ""

    @pytest.mark.parametrize(
        "menu_name, item_index, expected_command_name",
        [
            # Datei-Menü
            ("Datei", 0, "new_game"),
            ("Datei", 1, "load_game"),
            ("Datei", 2, "save_game"),
            ("Datei", 4, "new_tournament"),
            ("Datei", 5, "load_tournament"),
            ("Datei", 6, "save_tournament"),
            ("Datei", 8, "open_settings_dialog"),
            ("Datei", 10, "quit_game"),
            # Datenbank-Menü
            ("Datenbank", 0, "open_profile_manager"),
            ("Datenbank", 1, "show_player_stats"),
            ("Datenbank", 2, "show_highscores"),
            # Über-Menü
            ("Über", 0, "about"),
            ("Über", 2, "open_donate_link"),
        ],
    )
    def test_menu_item_invokes_correct_command(
        self, menu_setup, menu_name, item_index, expected_command_name
    ):
        """Testet, ob das Aufrufen eines bestimmten Menüpunkts die korrekte Controller-Methode aufruft."""
        tk_root, mock_controller = menu_setup
        menu_bar = tk_root.nametowidget(tk_root.cget("menu"))

        # Finde das spezifische Untermenü (z.B. "Datei" oder "Über")
        submenu_path = menu_bar.entrycget(menu_name, "menu")
        submenu = tk_root.nametowidget(submenu_path)

        # Rufe den Menüpunkt über seinen Index auf
        submenu.invoke(item_index)

        # Überprüfe, ob die entsprechende Mock-Methode auf dem Controller aufgerufen wurde
        getattr(mock_controller, expected_command_name).assert_called_once()
