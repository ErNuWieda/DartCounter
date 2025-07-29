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

class BracketCanvas(tk.Canvas):
    """
    Ein spezialisiertes Canvas-Widget zur grafischen Darstellung eines Turnierbaums.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        # Kein hartkodierter Hintergrund, erbt vom übergeordneten Frame
        self.config(highlightthickness=0)

        # --- Theme-abhängige Konfiguration ---
        # Theme wird durch die Helligkeit der Hintergrundfarbe erkannt
        bg_color = self.cget("background")
        try:
            r, g, b = (int(bg_color[i:i+2], 16) for i in (1, 3, 5))
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            is_dark_theme = luminance < 0.5
        except (ValueError, IndexError):
            is_dark_theme = False # Fallback auf helles Theme

        # --- Allgemeines Layout ---
        self.PADDING = 25
        self.ROUND_WIDTH = 160
        self.MATCH_HEIGHT = 65
        self.BOX_WIDTH = 120
        self.BOX_HEIGHT = 45

        # --- Theme-spezifische Einstellungen ---
        if is_dark_theme:
            self.LINE_COLOR = "#555555"
            self.TEXT_COLOR = "#cccccc"
            self.WINNER_COLOR = "#66bb6a"  # Material Design Green 300
            self.LOSER_COLOR = "#777777"
            self.NEXT_MATCH_COLOR = "#003c6b" # Dunkleres Blau
        else: # Helles Theme
            self.LINE_COLOR = "#cccccc"
            self.TEXT_COLOR = "#212121"
            self.WINNER_COLOR = "#2e7d32"  # Material Design Green 700
            self.LOSER_COLOR = "#9e9e9e"
            self.NEXT_MATCH_COLOR = "#e3f2fd" # Material Design Blue 50

        # --- Schriftarten ---
        try:
            tk.font.Font(family="Segoe UI", size=10)
            base_font = "Segoe UI"
        except tk.TclError:
            base_font = "Helvetica" # Fallback für Linux/macOS

        self.WINNER_FONT = (base_font, 10, "bold")
        self.NORMAL_FONT = (base_font, 10, "normal")
        self.LOSER_FONT = (base_font, 10, "italic")

    def draw_bracket(self, rounds_data: list, next_match: dict | None):
        """
        Zeichnet den kompletten Turnierbaum basierend auf den übergebenen Daten.

        Args:
            rounds_data (list): Eine Liste von Runden, wobei jede Runde eine Liste von Matches ist.
            next_match (dict | None): Das nächste zu spielende Match, um es hervorzuheben.
        """
        self.delete("all")

        if not rounds_data:
            return

        # Zeichne zuerst die Verbindungslinien, damit sie im Hintergrund sind
        self._draw_connecting_lines(rounds_data)

        # Zeichne dann die Match-Boxen und Namen
        for round_idx, current_round in enumerate(rounds_data):
            x_pos = self.PADDING + (round_idx * self.ROUND_WIDTH)
            
            # Berechne den vertikalen Abstand für diese Runde, um sie zu zentrieren
            total_height_of_round = len(current_round) * self.MATCH_HEIGHT
            y_offset = (self.winfo_height() - total_height_of_round) / 2

            for match_idx, match in enumerate(current_round):
                y_pos = y_offset + (match_idx * self.MATCH_HEIGHT)
                
                is_next = (match == next_match)
                self._draw_match_box(x_pos, y_pos, match, is_next)

    def _draw_match_box(self, x, y, match, is_next_match):
        """Zeichnet eine einzelne Spielpaarung mit verbessertem Stil."""
        p1 = match.get('player1', 'N/A')
        p2 = match.get('player2', 'N/A')
        winner = match.get('winner')

        # Hebe das nächste Match hervor
        if is_next_match:
            self.create_rectangle(
                x - 5, y - 5, x + self.BOX_WIDTH + 5, y + self.BOX_HEIGHT + 5,
                fill=self.NEXT_MATCH_COLOR, outline=""
            )

        # Spieler 1
        if winner:
            font_p1 = self.WINNER_FONT if winner == p1 else self.LOSER_FONT
            color_p1 = self.WINNER_COLOR if winner == p1 else self.LOSER_COLOR
        else:
            font_p1 = self.NORMAL_FONT
            color_p1 = self.TEXT_COLOR
        self.create_text(x, y, text=p1, anchor="nw", font=font_p1, fill=color_p1)

        # Spieler 2
        if winner:
            font_p2 = self.WINNER_FONT if winner == p2 else self.LOSER_FONT
            color_p2 = self.WINNER_COLOR if winner == p2 else self.LOSER_COLOR
        else:
            font_p2 = self.NORMAL_FONT
            color_p2 = self.TEXT_COLOR
        if p2 == "BYE": # Spezielles Styling für Freilos
            font_p2 = self.LOSER_FONT
            color_p2 = self.LOSER_COLOR
        self.create_text(x, y + 25, text=p2, anchor="nw", font=font_p2, fill=color_p2)

        # Trennlinie
        self.create_line(x, y + 20, x + self.BOX_WIDTH, y + 20, fill=self.LINE_COLOR)

    def _draw_connecting_lines(self, rounds_data):
        """Zeichnet die Linien, die die Gewinner mit der nächsten Runde verbinden."""
        for round_idx in range(len(rounds_data) - 1):
            current_round = rounds_data[round_idx]
            next_round = rounds_data[round_idx + 1]

            x_start = self.PADDING + (round_idx * self.ROUND_WIDTH) + self.BOX_WIDTH
            x_end = self.PADDING + ((round_idx + 1) * self.ROUND_WIDTH)

            total_height_current = len(current_round) * self.MATCH_HEIGHT
            y_offset_current = (self.winfo_height() - total_height_current) / 2

            total_height_next = len(next_round) * self.MATCH_HEIGHT
            y_offset_next = (self.winfo_height() - total_height_next) / 2

            for match_idx, match in enumerate(current_round):
                if match.get('winner'):
                    # Finde die Position des Gewinners in der nächsten Runde
                    try:
                        next_match_idx = [i for i, m in enumerate(next_round) if match['winner'] in (m.get('player1'), m.get('player2'))][0]
                    except IndexError:
                        continue # Passiert bei Freilosen in der nächsten Runde

                    # Startpunkt (Mitte der Gewinner-Box)
                    y_start = y_offset_current + (match_idx * self.MATCH_HEIGHT) + (self.BOX_HEIGHT / 2)
                    
                    # Endpunkt (Anfang der nächsten Match-Box)
                    y_end = y_offset_next + (next_match_idx * self.MATCH_HEIGHT) + (self.BOX_HEIGHT / 2)

                    # Zeichne die L-förmige Linie
                    x_mid = (x_start + x_end) / 2
                    self.create_line(x_start, y_start, x_mid, y_start, fill=self.LINE_COLOR)
                    self.create_line(x_mid, y_start, x_mid, y_end, fill=self.LINE_COLOR)
                    self.create_line(x_mid, y_end, x_end, y_end, fill=self.LINE_COLOR)