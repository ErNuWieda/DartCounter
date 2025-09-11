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

import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


class BaseScoreBoard:
    """
    Eine Basisklasse für alle Scoreboards. Definiert die gemeinsame Struktur
    und das Verhalten, wie Fenstererstellung, Header und Wurf-Anzeige.
    """

    def __init__(self, root, player, pos_x=None, pos_y=None, width=300, height=None):
        self.player = player
        self.game = player.game
        self.profile = player.profile
        self.original_title = player.name
        self.player_id = player.id

        self.score_window = tk.Toplevel(root)
        self.score_window.title(self.original_title)

        final_height = height if height is not None else self.game.game.get_scoreboard_height()

        if pos_x is not None and pos_y is not None:
            self.score_window.geometry(f"{width}x{final_height}+{pos_x}+{pos_y}")
        else:
            self.score_window.geometry(f"{width}x{final_height}")

        self.score_window.resizable(False, True)

        # --- Layout-Struktur ---
        # 1. Indikator-Leiste ganz oben
        self.indicator_label = ttk.Label(
            self.score_window, text="", background=self.score_window.cget("bg")
        )
        self.indicator_label.pack(side="top", fill="x")

        # 2. Button-Frame ganz unten (wird nicht vergrößert)
        bottom_frame = ttk.Frame(self.score_window)
        bottom_frame.pack(side="bottom", fill="x", pady=5)
        leave_button = ttk.Button(bottom_frame, text="Spiel verlassen", command=self.player.leave)
        leave_button.pack()

        # 3. Haupt-Frame, der den restlichen Platz füllt
        main_frame = ttk.Frame(self.score_window, padding=(10, 5))
        main_frame.pack(expand=True, fill="both")

        # --- Widgets im Haupt-Frame erstellen ---
        self._create_header(main_frame)
        self._create_extra_widgets(main_frame)  # Hook für Unterklassen
        ttk.Label(main_frame, text="Current Throws:", font=("Arial", 10)).pack(pady=(10, 0))
        self.throws_list = tk.Listbox(main_frame, height=3, font=("Arial", 12), justify="center")
        self.throws_list.pack(fill="x")

    def _create_header(self, parent):
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x")

        avatar_label = ttk.Label(header_frame, text="?", relief="solid", width=8, anchor="center")
        avatar_label.pack(side="left", padx=(0, 10))

        if self.profile and self.profile.avatar_path and os.path.exists(self.profile.avatar_path):
            try:
                img = Image.open(self.profile.avatar_path)
                img.thumbnail((64, 64))
                self.avatar_photo = ImageTk.PhotoImage(img)
                avatar_label.config(image=self.avatar_photo, text="")
            except Exception as e:
                print(f"Fehler beim Laden des Avatars für {self.player.name}: {e}")

        name_score_frame = ttk.Frame(header_frame)
        name_score_frame.pack(side="left", fill="x", expand=True, padx=5)

        name_label = ttk.Label(
            name_score_frame,
            text=self.player.name,
            font=("Arial", 16, "bold"),
            anchor="center",
        )
        name_label.pack(fill="x")

        score_display_frame = ttk.Frame(name_score_frame)
        score_display_frame.pack(pady=(5, 0))
        score_label_text = "Leben:" if self.game.options.name == "Killer" else "Score:"
        ttk.Label(score_display_frame, text=score_label_text, font=("Arial", 12)).pack(side="left")
        self.score_var = tk.StringVar(value=str(self.player.score))
        ttk.Label(
            score_display_frame, textvariable=self.score_var, font=("Arial", 20, "bold")
        ).pack(side="left", padx=5)

        separator = ttk.Separator(parent, orient="horizontal")
        separator.pack(fill="x", pady=5)

    def _create_extra_widgets(self, parent):
        """
        Platzhalter-Methode (Hook), die von Unterklassen überschrieben wird,
        um spielspezifische Widgets an der richtigen Stelle einzufügen.
        """
        pass

    def set_active(self, is_active: bool):
        if not self.score_window.winfo_exists():
            return
        if is_active:
            self.indicator_label.config(background="green")
            self.score_window.title(f"► {self.original_title} ◄")
        else:
            self.indicator_label.config(background=self.score_window.cget("bg"))
            self.score_window.title(self.original_title)

    def set_score_value(self, score):
        self.score_var.set(str(score))

    def update_score(self, score):
        self.set_score_value(score)
        self.throws_list.delete(0, tk.END)
        for r, s, _ in self.player.throws:  # Unpack the 3-tuple, ignoring coords
            self.throws_list.insert(tk.END, f"{r} {s}" if r != "Miss" else "Miss")

    def update_display(self, hits, score):
        self.update_score(score)


class X01ScoreBoard(BaseScoreBoard):
    """Ein spezialisiertes Scoreboard für X01-Spiele mit zusätzlichen Statistik-Widgets."""

    def __init__(self, root, player, pos_x=None, pos_y=None, width=300, height=None):
        # Ruft super().__init__ auf, was die Basis-UI inklusive des Hooks _create_extra_widgets erstellt.
        super().__init__(root, player, pos_x, pos_y, width, height)
        # Nachdem alles erstellt ist, wird die Anzeige initial aktualisiert.
        self.update_score(self.player.score)

    def _create_extra_widgets(self, parent):
        """Fügt die X01-spezifischen Statistik-Widgets in den übergebenen Parent-Frame ein."""
        # --- Leg/Set-Anzeige für X01-Matches ---
        # Wird nur angezeigt, wenn es sich um ein Leg/Set-Match handelt.
        if self.game.is_leg_set_match:
            leg_set_frame = ttk.Frame(parent)
            leg_set_frame.pack(pady=(0, 5), fill="x")
            # Zentriert die beiden inneren Frames (Sätze, Legs)
            leg_set_frame.columnconfigure(0, weight=1)
            leg_set_frame.columnconfigure(1, weight=1)

            set_frame = ttk.Frame(leg_set_frame)
            set_frame.grid(row=0, column=0, sticky="e", padx=(0, 10))
            ttk.Label(set_frame, text="Sätze:", font=("Arial", 10)).pack(side="left")
            self.set_score_var = tk.StringVar(value="0")
            ttk.Label(set_frame, textvariable=self.set_score_var, font=("Arial", 14, "bold")).pack(
                side="left", padx=5
            )

            leg_frame = ttk.Frame(leg_set_frame)
            leg_frame.grid(row=0, column=1, sticky="w", padx=(10, 0))
            ttk.Label(leg_frame, text="Legs:", font=("Arial", 10)).pack(side="left")
            self.leg_score_var = tk.StringVar(value="0")
            ttk.Label(leg_frame, textvariable=self.leg_score_var, font=("Arial", 14, "bold")).pack(
                side="left", padx=5
            )

        avg_frame = ttk.Frame(parent)
        avg_frame.pack(pady=(0, 5))
        ttk.Label(avg_frame, text="3-Dart-Avg:", font=("Arial", 10)).pack()
        self.avg_var = tk.StringVar(value="0.00")
        ttk.Label(avg_frame, textvariable=self.avg_var, font=("Arial", 14)).pack()

        extra_stats_frame = ttk.Frame(parent)
        extra_stats_frame.pack(pady=5, fill="x")

        hf_frame = ttk.Frame(extra_stats_frame)
        hf_frame.pack(side="left", expand=True)
        ttk.Label(hf_frame, text="High Finish:", font=("Arial", 10)).pack()
        self.hf_var = tk.StringVar(value="0")
        ttk.Label(hf_frame, textvariable=self.hf_var, font=("Arial", 14)).pack()

        co_frame = ttk.Frame(extra_stats_frame)
        co_frame.pack(side="right", expand=True)
        ttk.Label(co_frame, text="Checkout %:", font=("Arial", 10)).pack()
        self.co_var = tk.StringVar(value="0.0%")
        ttk.Label(co_frame, textvariable=self.co_var, font=("Arial", 14)).pack()

        checkout_frame = ttk.LabelFrame(parent, text="Finish-Vorschlag")
        checkout_frame.pack(pady=10, fill="x", padx=5)
        self.checkout_suggestion_var = tk.StringVar(value="-")
        ttk.Label(
            checkout_frame,
            textvariable=self.checkout_suggestion_var,
            font=("Arial", 14),
            justify="center",
        ).pack(pady=5)

    def update_checkout_suggestion(self, suggestion):
        self.checkout_suggestion_var.set(suggestion)

    def update_leg_set_scores(self, leg_score, set_score):
        """Aktualisiert die Anzeige für Leg- und Set-Stände."""
        if hasattr(self, "leg_score_var"):
            self.leg_score_var.set(str(leg_score))
        if hasattr(self, "set_score_var"):
            self.set_score_var.set(str(set_score))

    def update_score(self, score):
        super().update_score(score)
        self.avg_var.set(f"{self.player.get_average():.2f}")
        self.hf_var.set(str(self.player.stats["highest_finish"]))
        self.co_var.set(f"{self.player.get_checkout_percentage():.1f}%")
        # Initialisiert oder aktualisiert die Leg/Set-Anzeige, falls zutreffend.
        if self.game.is_leg_set_match:
            leg_score = self.game.player_leg_scores.get(self.player_id, 0)  # noqa: E501
            set_score = self.game.player_set_scores.get(self.player_id, 0)  # noqa: E501
            self.update_leg_set_scores(leg_score, set_score)


class TargetBasedScoreBoard(BaseScoreBoard):
    """Ein spezialisiertes Scoreboard für zielbasierte Spiele (Cricket, Micky, etc.)."""

    def __init__(self, root, player, pos_x=None, pos_y=None, width=300, height=None):
        self.hit_check_vars = {}
        super().__init__(root, player, pos_x, pos_y, width, height)
        self.update_display(self.player.hits, self.player.score)

    def _create_extra_widgets(self, main_frame):
        hits_frame = ttk.LabelFrame(main_frame, text="Targets")
        hits_frame.pack(pady=10, fill="x", padx=5)  # type: ignore
        num_columns = 2
        for i in range(num_columns):
            hits_frame.columnconfigure(i, weight=1)

        for i, target in enumerate(self.player.targets):
            row, col = divmod(i, num_columns)
            target_frame = ttk.Frame(hits_frame)
            target_frame.grid(row=row, column=col, padx=5, pady=2, sticky="ew")
            ttk.Label(target_frame, text=f"{target}:", width=5).pack(side="left")

            if self.game.options.name in (
                "Cricket",
                "Cut Throat",
                "Tactics",
                "Micky Mouse",
            ):
                self.hit_check_vars[target] = []
                for _ in range(3):
                    var = tk.BooleanVar()
                    chk = ttk.Checkbutton(target_frame, variable=var, state="disabled")
                    chk.pack(side="left")
                    self.hit_check_vars[target].append(var)
            elif self.game.options.name in ("Around the Clock", "Shanghai"):
                var = tk.BooleanVar()
                chk = ttk.Checkbutton(target_frame, variable=var, state="disabled")
                chk.pack(side="left")
                self.hit_check_vars[target] = [var]

    def update_display(self, hits, score):
        super().update_score(score)
        for target, vars_list in self.hit_check_vars.items():
            num_hits = hits.get(str(target), 0)
            for i, var in enumerate(vars_list):
                if i < num_hits:
                    var.set(True)
                else:
                    var.set(False)


class ScoreBoard(BaseScoreBoard):
    """
    Die Standard-Scoreboard-Klasse für Spiele ohne spezielle UI-Elemente
    (z.B. Killer, Elimination). Erbt alle Basisfunktionen.
    """

    def __init__(self, root, player, pos_x=None, pos_y=None, width=300, height=None):
        super().__init__(root, player, pos_x, pos_y, width, height)
        self.update_score(self.player.score)


def setup_scoreboards(game_controller):
    """
    Erstellt und positioniert die Scoreboards für alle Spieler.

    Die Positionierung erfolgt dynamisch relativ zum zentrierten
    Dartboard-Fenster, um eine aufgeräumte und überlappungsfreie
    Anzeige auf verschiedenen Bildschirmgrößen zu gewährleisten.
    Diese Methode kapselt die Logik aus der ehemaligen GameUI-Klasse.

    Args:
        game_controller (Game): Die Haupt-Spielinstanz.

    Returns:
        list[ScoreBoard]: Eine Liste der erstellten Scoreboard-Instanzen.
    """
    if not game_controller.dartboard or not game_controller.dartboard.root.winfo_exists():
        return []

    game_controller.dartboard.root.update_idletasks()

    db_x = game_controller.dartboard.root.winfo_x()
    db_y = game_controller.dartboard.root.winfo_y()
    db_width = game_controller.dartboard.root.winfo_width()

    scoreboard_width = 340
    scoreboard_height = game_controller.game.get_scoreboard_height()
    gap = 10

    positions = [
        (db_x - scoreboard_width - gap, db_y),
        (db_x - scoreboard_width - gap, db_y + scoreboard_height + gap),
        (db_x + db_width + gap, db_y),
        (db_x + db_width + gap, db_y + scoreboard_height + gap),
    ]

    created_scoreboards = []
    for i, player in enumerate(game_controller.players):
        if i < len(positions):
            pos_x, pos_y = positions[i]

            # --- Factory-Logik zur Auswahl der korrekten Scoreboard-Klasse ---
            game_name = game_controller.options.name
            if game_name in ("301", "501", "701"):
                scoreboard_class = X01ScoreBoard  # type: ignore
            elif game_name in (
                "Cricket",
                "Cut Throat",
                "Tactics",
                "Micky Mouse",
                "Around the Clock",
                "Shanghai",
            ):
                scoreboard_class = TargetBasedScoreBoard
            else:
                # Fallback für Spiele ohne spezielle UI (z.B. Killer, Elimination)
                scoreboard_class = ScoreBoard

            sb = scoreboard_class(
                root=game_controller.dartboard.root,
                player=player,
                pos_x=pos_x,
                pos_y=pos_y,
                width=scoreboard_width,
                height=scoreboard_height,
            )
            created_scoreboards.append(sb)
            player.sb = sb  # Weist das Scoreboard direkt dem Spieler zu

    return created_scoreboards
