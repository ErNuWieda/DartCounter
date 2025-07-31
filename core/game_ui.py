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

import tkinter as tk 
from .dartboard import DartBoard
from .scoreboard import ScoreBoard

class GameUI:
    """
    Verwaltet alle UI-Komponenten für eine einzelne Spielsitzung.

    Diese Klasse ist verantwortlich für die Erstellung, Positionierung und
    Zerstörung des Dartboards und aller Scoreboards. Sie entkoppelt die
    UI-Verwaltung von der Spiellogik in der Game-Klasse.
    """
    def __init__(self, game_controller):
        self.game = game_controller
        self.root = game_controller.root

        # Erstellt das Dartboard und speichert eine Referenz darauf.
        # Das Dartboard selbst kommuniziert weiterhin direkt mit dem game_controller.
        self.db = DartBoard(self.game)

        # Erstellt und positioniert die Scoreboards.
        self.setup_scoreboards()

    def setup_scoreboards(self):
        """
        Erstellt und positioniert die Scoreboards für alle Spieler.

        Die Positionierung erfolgt dynamisch relativ zum zentrierten
        Dartboard-Fenster, um eine aufgeräumte und überlappungsfreie
        Anzeige auf verschiedenen Bildschirmgrößen zu gewährleisten.
        """
        if not self.db or not self.db.root.winfo_exists():
            return

        self.db.root.update_idletasks()

        db_x = self.db.root.winfo_x()
        db_y = self.db.root.winfo_y()
        db_width = self.db.root.winfo_width()
        
        scoreboard_width = 340
        scoreboard_height = self.game.game.get_scoreboard_height()
        gap = 10

        positions = [
            (db_x - scoreboard_width - gap, db_y),
            (db_x - scoreboard_width - gap, db_y + scoreboard_height + gap),
            (db_x + db_width + gap, db_y),
            (db_x + db_width + gap, db_y + scoreboard_height + gap),
        ]

        for i, player in enumerate(self.game.players):
            if i < len(positions):
                pos_x, pos_y = positions[i]
                player.sb = ScoreBoard(self.root, player, self.game, pos_x, pos_y, scoreboard_width, scoreboard_height, profile=player.profile)

    def announce_turn(self, player):
        """Führt alle UI-Aktionen aus, um den Zug eines Spielers anzukündigen."""
        if not player:
            return

        # Dart-Farbe für den aktuellen Spieler setzen
        if self.db:
            dart_color = player.profile.dart_color if player.profile else "#ff0000"
            self.db.update_dart_image(dart_color)
            self.db.clear_dart_images_from_canvas()

        # Sicherstellen, dass Scoreboard existiert und fokussiert werden kann
        if player.sb and player.sb.score_window.winfo_exists():
            player.sb.score_window.lift()
            player.sb.score_window.focus_force()
            player.sb.set_active(True)

        # Button-Zustände für den neuen Zug initialisieren
        if self.db:
            self.db.update_button_states()

    def destroy(self):
        """Zerstört alle UI-Elemente, die zu diesem Spiel gehören, sicher."""
        if self.db and self.db.root and self.db.root.winfo_exists():
            self.db.root.destroy()
        
        for player in self.game.players:
            if player.sb and player.sb.score_window and player.sb.score_window.winfo_exists():
                player.sb.score_window.destroy()
        
        self.db = None
