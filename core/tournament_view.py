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
from tkinter import ttk
from .bracket_canvas import BracketCanvas

class TournamentView(tk.Toplevel):
    """
    Ein Fenster zur Visualisierung des Turnierbaums (Bracket).
    """
    def __init__(self, parent, tournament_manager, start_match_callback):
        super().__init__(parent)
        self.tm = tournament_manager
        self.start_match_callback = start_match_callback

        self.title(f"Turnier: {self.tm.game_mode}")
        self.geometry("650x450") # Etwas breiter für die neue Ansicht

        self._setup_widgets()
        self.update_bracket_tree()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.bracket_canvas = BracketCanvas(main_frame)
        self.bracket_canvas.pack(fill=tk.BOTH, expand=True)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.start_button = ttk.Button(button_frame, text="Nächstes Spiel starten", command=self.start_match_callback)
        self.start_button.pack()

    def update_bracket_tree(self):
        """Aktualisiert die Canvas-Zeichnung und den Status der Buttons."""
        # Die update_idletasks() ist wichtig, damit das Canvas seine Größe kennt, bevor gezeichnet wird.
        self.bracket_canvas.update_idletasks()
        self.bracket_canvas.draw_bracket(self.tm.rounds, self.tm.get_next_match())
        # Button-Status aktualisieren
        if self.tm.is_finished:
            self.start_button.config(text=f"Turnier beendet! Sieger: {self.tm.get_tournament_winner()}", state=tk.DISABLED)
        elif not self.tm.get_next_match():
            self.start_button.config(text="Nächste Runde generieren", command=self._advance_round_and_refresh)
        else:
            self.start_button.config(text="Nächstes Spiel starten", state=tk.NORMAL, command=self.start_match_callback)

    def _advance_round_and_refresh(self):
        """Wrapper, um die Runde voranzutreiben und die Ansicht zu aktualisieren."""
        self.tm.advance_to_next_round()
        self.update_bracket_tree()

    def _on_close(self):
        # Standardmäßig wird das Fenster nur verborgen, nicht zerstört,
        # da die App den Lebenszyklus verwaltet.
        self.withdraw()