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
    Ein Toplevel-Fenster zur Anzeige des Turnierverlaufs.
    Zeigt das Winners- und Losers-Bracket (falls zutreffend) sowie
    das Grand Final an.
    """

    def __init__(self, parent, manager, start_match_callback):
        super().__init__(parent)
        self.manager = manager
        self.start_match_callback = start_match_callback

        self.title(f"Turnier-Übersicht: {self.manager.system}")

        if self.manager.system == "Doppel-K.o.":
            self.geometry("1200x800")
        else:  # Einfaches K.o.-System
            self.geometry("1200x500")

        self._setup_widgets()
        # update_idletasks() erzwingt, dass Tkinter alle anstehenden Geometrie-
        # Berechnungen durchführt. Ohne diesen Aufruf hätten die Canvas-Widgets
        # beim ersten Zeichnen eine Höhe/Breite von 1px, was zu einer
        # fehlerhaften Darstellung des Turnierbaums führen würde.
        self.update_idletasks()
        self.update_bracket_tree()

        self.protocol("WM_DELETE_WINDOW", self.withdraw)  # Nicht zerstören, nur verbergen

    def _setup_double_elim_layout(self, main_frame, finals_frame):
        """Konfiguriert das Layout spezifisch für das Doppel-K.o.-System."""
        # Dynamische Gewichtung basierend auf der Anzahl der Matches in der ersten Runde
        wb_rounds = self.manager.bracket.get("winners", [])
        lb_rounds = self.manager.bracket.get("losers", [])
        wb_weight = len(wb_rounds[0]) if wb_rounds and wb_rounds[0] else 1
        lb_weight = len(lb_rounds[0]) if lb_rounds and lb_rounds[0] else 1

        main_frame.rowconfigure(0, weight=max(1, wb_weight))
        main_frame.rowconfigure(1, weight=max(1, lb_weight))

        self.wb_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        self.lb_frame.grid(row=1, column=0, sticky="nsew", pady=5)

        # Widgets für die finalen Spiele
        self.wb_final_label = ttk.Label(
            finals_frame,
            text="",
            font=("Segoe UI", 12, "bold"),
            anchor="center",
        )
        self.wb_final_label.pack(pady=(5, 0))

        self.second_place_label = ttk.Label(
            finals_frame, text="", font=("Segoe UI", 11), anchor="center"
        )
        self.second_place_label.pack(pady=(5, 10))

    def _setup_single_elim_layout(self, main_frame, finals_frame):
        """Konfiguriert das Layout spezifisch für das einfache K.o.-System."""
        main_frame.rowconfigure(0, weight=1)  # Nur eine Zeile für den Turnierbaum
        self.wb_frame.grid(row=0, column=0, sticky="nsew")
        self.lb_frame.grid_remove()  # Sicherstellen, dass der LB-Frame nicht angezeigt wird

        # Widget für das Spiel um Platz 3
        self.third_place_label = ttk.Label(
            finals_frame, text="", font=("Segoe UI", 11), anchor="center"
        )
        self.third_place_label.grid(row=0, column=0, pady=(0, 10))

    def _setup_widgets(self):
        """Erstellt die UI-Elemente für die Brackets und Steuerelemente."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=0)  # Feste Höhe für die unteren Frames
        main_frame.rowconfigure(3, weight=0)

        # --- Winners Bracket ---
        bracket_title = "Winners Bracket" if self.manager.system == "Doppel-K.o." else "Turnierbaum"
        self.wb_frame = ttk.LabelFrame(main_frame, text=bracket_title, padding=10)
        self.winners_canvas = BracketCanvas(self.wb_frame)
        self.winners_canvas.pack(fill=tk.BOTH, expand=True)

        # --- Losers Bracket ---
        self.lb_frame = ttk.LabelFrame(main_frame, text="Losers Bracket", padding=10)
        self.losers_canvas = BracketCanvas(self.lb_frame)
        self.losers_canvas.pack(fill=tk.BOTH, expand=True)

        # --- Podium für die Siegerehrung (initial versteckt) ---
        self.podium_frame = ttk.Frame(main_frame)
        self.podium_frame.grid(
            row=0, column=0, rowspan=3, sticky="nsew"
        )  # Span over brackets and finals
        self.podium_frame.columnconfigure((0, 1, 2), weight=1)
        self.podium_frame.rowconfigure((0, 1, 2, 3), weight=1)

        # Labels for podium
        self.podium_labels = {}
        # 2nd Place
        self.podium_labels["second_cup"] = ttk.Label(
            self.podium_frame, text="🥈", font=("Segoe UI", 48)
        )
        self.podium_labels["second_cup"].grid(row=1, column=0, sticky="s")
        self.podium_labels["second_name"] = ttk.Label(
            self.podium_frame,
            text="",
            font=("Segoe UI", 18, "bold"),
            foreground="#c0c0c0",
        )
        self.podium_labels["second_name"].grid(row=2, column=0, sticky="n", pady=5)
        # 1st Place
        self.podium_labels["first_cup"] = ttk.Label(
            self.podium_frame, text="🥇", font=("Segoe UI", 64)
        )
        self.podium_labels["first_cup"].grid(row=0, column=1, sticky="s")
        self.podium_labels["first_name"] = ttk.Label(
            self.podium_frame,
            text="",
            font=("Segoe UI", 22, "bold"),
            foreground="#ffd700",
        )
        self.podium_labels["first_name"].grid(row=1, column=1, sticky="n", pady=5)
        # 3rd Place
        self.podium_labels["third_cup"] = ttk.Label(
            self.podium_frame, text="🥉", font=("Segoe UI", 40)
        )
        self.podium_labels["third_cup"].grid(row=2, column=2, sticky="s")
        self.podium_labels["third_name"] = ttk.Label(
            self.podium_frame,
            text="",
            font=("Segoe UI", 16, "bold"),
            foreground="#cd7f32",
        )
        self.podium_labels["third_name"].grid(row=3, column=2, sticky="n", pady=5)
        self.podium_frame.grid_remove()

        # --- Finale(s) und Steuerung ---
        self.finals_frame = ttk.Frame(main_frame)
        self.finals_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.finals_frame.columnconfigure(0, weight=1)

        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, sticky="ew", pady=(5, 0))
        control_frame.columnconfigure(0, weight=1)

        self.next_match_button = ttk.Button(
            control_frame,
            text="Nächstes Match starten",
            style="Accent.TButton",
            command=self.start_match_callback,
        )
        self.next_match_button.grid(row=0, column=0, pady=5)
        self.next_match_button.bind("<Return>", lambda e: self.start_match_callback())
        self.next_match_button.focus_set()

        # Systemspezifisches Layout aufrufen
        if self.manager.system == "Doppel-K.o.":
            self._setup_double_elim_layout(main_frame, self.finals_frame)
        else:
            self._setup_single_elim_layout(main_frame, self.finals_frame)

    def _update_final_matches_display(self):
        """Aktualisiert die Anzeige für das WB-Finale und das Spiel um Platz 2."""
        # WB-Finale
        wb_final_match = self.manager.bracket["winners"][-1][0]
        p1, p2 = wb_final_match.get("player1"), wb_final_match.get("player2")
        winner = wb_final_match.get("winner")

        final_text = "Finale: "
        if p1 and p2:
            final_text += f"{p1} vs {p2}"
            if winner:
                final_text += f"  |  Sieger: {winner}"
        else:
            final_text += "..."
        self.wb_final_label.config(text=final_text)

        # Spiel um Platz 2
        second_place_match_list = self.manager.bracket.get("second_place_match", [])
        if second_place_match_list and second_place_match_list[0].get("player1"):
            match = second_place_match_list[0]
            p1_2nd, p2_2nd = match["player1"], match["player2"]
            winner_2nd = match.get("winner")

            text = f"Spiel um Platz 2: {p1_2nd} vs {p2_2nd}"
            if winner_2nd:
                text += f"  |  Sieger: {winner_2nd}"
            self.second_place_label.config(text=text)
        else:
            self.second_place_label.config(text="Spiel um Platz 2: ...")

    def _update_double_elim_view(self, next_match, wb_bracket_winner):
        """Aktualisiert die UI-Elemente, die nur im Doppel-K.o.-System relevant sind."""
        losers_rounds = self.manager.bracket.get("losers", [])
        lb_bracket_winner = self._get_bracket_winner(losers_rounds)
        self.losers_canvas.draw_bracket(
            losers_rounds, next_match, lb_bracket_winner, bracket_type="losers"
        )
        self._update_final_matches_display()

    def _update_single_elim_view(self):
        """Aktualisiert die UI-Elemente, die nur im einfachen K.o.-System relevant sind."""
        third_place_match_list = self.manager.bracket.get("third_place_match", [])
        if third_place_match_list and third_place_match_list[0].get("player1"):
            match = third_place_match_list[0]
            p1, p2 = match["player1"], match["player2"]
            winner = match.get("winner")

            text = f"Spiel um Platz 3: {p1} vs {p2}"
            if winner:
                text += f"  |  Sieger: {winner}"
            self.third_place_label.config(text=text)
        else:
            self.third_place_label.config(text="")

    def _show_podium(self):
        """Blends the bracket view out and the podium view in."""
        podium_data = self.manager.get_podium()
        if not podium_data:
            return

        # Hide bracket views
        self.wb_frame.grid_remove()
        self.lb_frame.grid_remove()
        self.finals_frame.grid_remove()

        # Show podium
        self.podium_frame.grid()

        # Update labels
        self.podium_labels["first_name"].config(text=podium_data.get("first", ""))
        self.podium_labels["second_name"].config(text=podium_data.get("second", ""))
        self.podium_labels["third_name"].config(text=podium_data.get("third", ""))

    def update_bracket_tree(self):
        """Aktualisiert die Anzeige aller Brackets und Steuerelemente."""
        tournament_winner = self.manager.winner

        if tournament_winner:
            self._show_podium()
            self.title(f"Turnier beendet! Sieger: {tournament_winner}")
            self.next_match_button.config(state="disabled")
            return

        # --- Wenn das Turnier noch läuft, Brackets anzeigen ---
        self.wb_frame.grid()
        self.finals_frame.grid()
        self.podium_frame.grid_remove()

        next_match = self.manager.get_next_match()
        winners_rounds = self.manager.bracket.get("winners", [])
        wb_bracket_winner = self._get_bracket_winner(winners_rounds)
        self.winners_canvas.draw_bracket(
            winners_rounds,
            next_match,
            wb_bracket_winner,
            bracket_type="winners",
        )

        if self.manager.system == "Doppel-K.o.":
            self.lb_frame.grid()
            self._update_double_elim_view(next_match, wb_bracket_winner)
        else:
            self.lb_frame.grid_remove()
            self._update_single_elim_view()

        self.next_match_button.config(state="normal" if next_match else "disabled")

    def _get_bracket_winner(self, bracket_rounds: list) -> str | None:
        """Prüft, ob ein Bracket (WB oder LB) abgeschlossen ist."""
        if bracket_rounds and bracket_rounds[-1] and len(bracket_rounds[-1]) == 1:
            return bracket_rounds[-1][0].get("winner")
        return None

    def _on_close(self):
        # Standardmäßig wird das Fenster nur verborgen, nicht zerstört,
        # da die App den Lebenszyklus verwaltet.
        self.withdraw()
