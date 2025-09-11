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
            r, g, b = (int(bg_color[i : i + 2], 16) for i in (1, 3, 5))
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            is_dark_theme = luminance < 0.5
        except (ValueError, IndexError):
            is_dark_theme = False  # Fallback auf helles Theme

        # --- Allgemeines Layout ---
        self.HEADER_HEIGHT = 30
        self.PADDING = 25
        self.ROUND_WIDTH = 160
        self.MATCH_HEIGHT = 66  # Geändert für saubere Integer-Positionierung
        self.BOX_WIDTH = 120
        self.BOX_HEIGHT = 46  # Geändert für saubere Integer-Positionierung

        # --- Theme-spezifische Einstellungen ---
        if is_dark_theme:
            self.LINE_COLOR = "#555555"
            self.TEXT_COLOR = "#cccccc"
            self.WINNER_COLOR = "#66bb6a"  # Material Design Green 300
            self.LOSER_COLOR = "#777777"
            self.NEXT_MATCH_COLOR = "#003c6b"  # Dunkleres Blau
        else:  # Helles Theme
            self.LINE_COLOR = "#cccccc"
            self.TEXT_COLOR = "#212121"
            self.WINNER_COLOR = "#2e7d32"  # Material Design Green 700
            self.LOSER_COLOR = "#9e9e9e"
            self.NEXT_MATCH_COLOR = "#e3f2fd"  # Material Design Blue 50

        # --- Schriftarten ---
        try:
            tk.font.Font(family="Segoe UI", size=10)
            base_font = "Segoe UI"
        except tk.TclError:
            base_font = "Helvetica"  # Fallback für Linux/macOS

        self.WINNER_FONT = (base_font, 10, "bold")
        self.NORMAL_FONT = (base_font, 10, "normal")
        self.LOSER_FONT = (base_font, 10, "italic")

    def draw_bracket(
        self,
        rounds_data: list,
        next_match: dict | None,
        bracket_winner: str | None,
        bracket_type: str = "winners",
    ):
        """
        Zeichnet den kompletten Turnierbaum basierend auf den übergebenen Daten.
        Verwendet einen Zwei-Phasen-Ansatz: Zuerst werden alle Positionen berechnet,
        dann wird alles gezeichnet. Dies verhindert Überschneidungen.

        Args:
            rounds_data (list): Eine Liste von Runden, wobei jede Runde eine Liste von Matches ist.
            next_match (dict | None): Das nächste zu spielende Match, um es hervorzuheben.
            bracket_winner (str | None): Der Name des Siegers dieses Brackets, falls vorhanden.
            bracket_type (str): Der Typ des Brackets ('winners' oder 'losers'), um die Zeichenlogik anzupassen.
        """
        self.delete("all")
        if not rounds_data or not rounds_data[0]:
            return

        match_positions = {}  # Speichert die Y-Mittelpunkte: {(round_idx, match_idx): y_center}

        # --- Phase 1: Positionen berechnen ---
        # Runde 1 wird vertikal zentriert
        available_height = self.winfo_height() - self.HEADER_HEIGHT
        total_height_round1 = len(rounds_data[0]) * self.MATCH_HEIGHT
        y_offset_round1 = self.HEADER_HEIGHT + (available_height - total_height_round1) // 2  # noqa
        if y_offset_round1 < self.HEADER_HEIGHT + self.PADDING:
            y_offset_round1 = self.HEADER_HEIGHT + self.PADDING

        for match_idx, _ in enumerate(rounds_data[0]):
            y_pos = y_offset_round1 + (match_idx * self.MATCH_HEIGHT)
            match_positions[(0, match_idx)] = y_pos + (self.BOX_HEIGHT // 2)

        # Folge-Runden werden relativ zur vorherigen Runde positioniert
        for round_idx in range(len(rounds_data) - 1):
            next_round_idx = round_idx + 1
            # In Losers Bracket, ungerade Runden sind "feed-in" Runden
            is_lb_feed_in_round = bracket_type == "losers" and next_round_idx % 2 != 0

            for next_match_idx, _ in enumerate(rounds_data[next_round_idx]):
                if is_lb_feed_in_round:
                    # In einer Feed-in-Runde hat jedes Match nur einen Elternteil aus der vorherigen LB-Runde.
                    # Die Position wird direkt vom Elternteil übernommen.
                    parent_y = match_positions.get((round_idx, next_match_idx))
                    y_center = parent_y if parent_y else self.winfo_height() / 2
                else:
                    # Standardlogik für WB oder interne LB-Runden # noqa
                    parent1_y = match_positions.get((round_idx, next_match_idx * 2))  # noqa
                    parent2_y = match_positions.get((round_idx, next_match_idx * 2 + 1))

                    if parent1_y and parent2_y:
                        # Der Y-Mittelpunkt des nächsten Matches ist der Durchschnitt der Eltern
                        y_center = (parent1_y + parent2_y) // 2
                    elif parent1_y:
                        # Fall für ein Freilos in der vorherigen Runde
                        y_center = parent1_y
                    else:
                        y_center = self.winfo_height() / 2  # Sollte nicht passieren
                match_positions[(next_round_idx, next_match_idx)] = y_center

        # --- Phase 2: Alles zeichnen ---
        # Zuerst die Runden-Titel
        for round_idx, _ in enumerate(rounds_data):
            x_pos = self.PADDING + (round_idx * self.ROUND_WIDTH) + (self.BOX_WIDTH / 2)
            y_pos = self.HEADER_HEIGHT / 2
            self.create_text(
                x_pos,
                y_pos,
                text=f"Runde {round_idx + 1}",
                font=self.LOSER_FONT,
                fill=self.LOSER_COLOR,
                anchor="center",
            )

        # Zuerst die Verbindungslinien
        self._draw_connecting_lines(rounds_data, match_positions, bracket_type)

        # Dann die Match-Boxen
        for (round_idx, match_idx), y_center in match_positions.items():
            x_pos = self.PADDING + (round_idx * self.ROUND_WIDTH)
            y_pos = y_center - (self.BOX_HEIGHT / 2)
            match = rounds_data[round_idx][match_idx]
            is_next = match == next_match
            self._draw_match_box(x_pos, y_pos, match, is_next)

        # --- Phase 3: Den Bracket-Sieger zeichnen ---
        if bracket_winner:
            last_round_idx = len(rounds_data) - 1
            final_match_x = self.PADDING + (last_round_idx * self.ROUND_WIDTH)
            final_match_y_center = match_positions.get((last_round_idx, 0))

            if final_match_y_center:
                winner_x = final_match_x + self.BOX_WIDTH + self.PADDING
                winner_y = final_match_y_center

                # Zeichne eine finale Linie zum Sieger
                line_start_x = final_match_x + self.BOX_WIDTH
                self.create_line(line_start_x, winner_y, winner_x, winner_y, fill=self.LINE_COLOR)

                # Zeichne den Namen des Siegers
                self.create_text(
                    winner_x + 10,
                    winner_y,
                    text=f"🏆 {bracket_winner}",
                    anchor="w",
                    font=(self.WINNER_FONT[0], 14, "bold"),
                    fill=self.WINNER_COLOR,
                )

    def _draw_connecting_lines(self, rounds_data, match_positions, bracket_type="winners"):
        """Zeichnet die Verbindungslinien zwischen den Matches."""
        for round_idx in range(len(rounds_data) - 1):
            x_start = self.PADDING + (round_idx * self.ROUND_WIDTH) + self.BOX_WIDTH
            x_end = self.PADDING + ((round_idx + 1) * self.ROUND_WIDTH)
            x_mid = (x_start + x_end) / 2

            next_round_idx = round_idx + 1
            is_lb_feed_in_round = bracket_type == "losers" and next_round_idx % 2 != 0

            for next_match_idx, _ in enumerate(rounds_data[round_idx + 1]):
                child_y = match_positions.get((next_round_idx, next_match_idx))
                if not child_y:
                    continue

                if is_lb_feed_in_round:
                    # In Feed-in-Runden gibt es nur eine Linie vom einzelnen Elternteil.
                    parent_y = match_positions.get((round_idx, next_match_idx))
                    if parent_y:
                        # Zeichne eine direkte diagonale Linie, um Überlappungen zu vermeiden.
                        self.create_line(x_start, parent_y, x_end, child_y, fill=self.LINE_COLOR)
                else:
                    # Standard-Zeichenlogik für normale Runden
                    parent1_y = match_positions.get((round_idx, next_match_idx * 2))
                    parent2_y = match_positions.get((round_idx, next_match_idx * 2 + 1))
                    if parent1_y:
                        self.create_line(x_start, parent1_y, x_mid, parent1_y, fill=self.LINE_COLOR)
                    if parent2_y:
                        self.create_line(x_start, parent2_y, x_mid, parent2_y, fill=self.LINE_COLOR)
                    if parent1_y and parent2_y:
                        self.create_line(x_mid, parent1_y, x_mid, parent2_y, fill=self.LINE_COLOR)
                    if parent1_y or parent2_y:
                        self.create_line(x_mid, child_y, x_end, child_y, fill=self.LINE_COLOR)

    def _draw_match_box(self, x, y, match, is_next_match):
        """Zeichnet eine einzelne Spielpaarung mit verbessertem Stil."""
        p1 = match.get("player1") or "???"  # Fallback für Vorschau
        p2 = match.get("player2") or "???"  # Fallback für Vorschau
        winner = match.get("winner")

        # Hebe das nächste Match hervor
        if is_next_match:
            self.create_rectangle(
                x - 5,
                y - 5,
                x + self.BOX_WIDTH + 5,
                y + self.BOX_HEIGHT + 5,
                fill=self.NEXT_MATCH_COLOR,
                outline="",
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
        if p2 == "BYE":  # Spezielles Styling für Freilos
            font_p2 = self.LOSER_FONT
            color_p2 = self.LOSER_COLOR
        self.create_text(x, y + 25, text=p2, anchor="nw", font=font_p2, fill=color_p2)

        # Trennlinie
        self.create_line(
            x,
            y + (self.BOX_HEIGHT // 2),
            x + self.BOX_WIDTH,
            y + (self.BOX_HEIGHT // 2),
            fill=self.LINE_COLOR,
        )
