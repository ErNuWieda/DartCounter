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

from tkinter import Menu


class AppMenu:
    """Erstellt und verwaltet die Hauptmenüleiste der Anwendung."""

    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self._create_menu()

    def _create_menu(self):
        menu_bar = Menu(self.root)

        # Datei Menü
        file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Neues Turnier", command=self.controller.new_tournament)
        file_menu.add_command(label="Turnier laden", command=self.controller.load_tournament)
        file_menu.add_command(label="Turnier speichern", command=self.controller.save_tournament)
        file_menu.add_separator()
        file_menu.add_command(label="Neues Spiel", command=self.controller.new_game)
        file_menu.add_command(label="Spiel laden", command=self.controller.load_game)
        file_menu.add_command(label="Spiel speichern", command=self.controller.save_game)
        file_menu.add_separator()
        file_menu.add_command(
            label="Spielerprofile verwalten",
            command=self.controller.open_profile_manager,
        )
        file_menu.add_command(label="Einstellungen", command=self.controller.open_settings_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Spielerstatistiken", command=self.controller.show_player_stats)
        file_menu.add_command(label="Highscores", command=self.controller.show_highscores)
        file_menu.add_separator()
        file_menu.add_command(label="Spiel beenden", command=self.controller.quit_game)

        # Über Menü
        about_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Über", menu=about_menu)
        about_menu.add_command(label="Über Dartcounter", command=self.controller.about)
        about_menu.add_separator()
        about_menu.add_command(
            label="Entwicklung unterstützen...",
            command=self.controller.open_donate_link,
        )

        self.root.config(menu=menu_bar)
