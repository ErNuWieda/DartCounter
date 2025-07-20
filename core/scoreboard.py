import tkinter as tk
from tkinter import ttk

class ScoreBoard:
    """
    Stellt ein separates Fenster für den Spielstand eines Spielers dar,
    inklusive aktueller Punktzahl, Würfe und Statistiken.
    """
    def __init__(self, root, player, game):
        self.player = player
        self.game = game
        self.score_window = tk.Toplevel(root)
        self.score_window.title(player.name)
        # Höhe für neue Statistiken und Button angepasst und Fenster positioniert
        self.score_window.geometry(f"200x380+{10 + (player.id - 1) * 210}+{10}")
        self.score_window.resizable(False, False)

        main_frame = ttk.Frame(self.score_window, padding="10")
        main_frame.pack(expand=True, fill="both")

        # Anzeige für den Punktestand
        score_frame = ttk.Frame(main_frame)
        score_frame.pack(pady=5)
        ttk.Label(score_frame, text="Score:", font=("Arial", 12)).pack()
        self.score_var = tk.StringVar(value=str(player.score))
        ttk.Label(score_frame, textvariable=self.score_var, font=("Arial", 24, "bold")).pack()

        # Anzeige für den 3-Dart-Average (nur für X01-Spiele)
        if self.game.name in ('301', '501', '701'):
            avg_frame = ttk.Frame(main_frame)
            avg_frame.pack(pady=5)
            ttk.Label(avg_frame, text="3-Dart-Avg:", font=("Arial", 10)).pack()
            self.avg_var = tk.StringVar(value="0.00")
            ttk.Label(avg_frame, textvariable=self.avg_var, font=("Arial", 14)).pack()

            # Frame für weitere Statistiken (High Finish, Checkout %)
            extra_stats_frame = ttk.Frame(main_frame)
            extra_stats_frame.pack(pady=5, fill='x')

            # High Finish (links)
            hf_frame = ttk.Frame(extra_stats_frame)
            hf_frame.pack(side='left', expand=True)
            ttk.Label(hf_frame, text="High Finish:", font=("Arial", 10)).pack()
            self.hf_var = tk.StringVar(value="0")
            ttk.Label(hf_frame, textvariable=self.hf_var, font=("Arial", 14)).pack()

            # Checkout % (rechts)
            co_frame = ttk.Frame(extra_stats_frame)
            co_frame.pack(side='right', expand=True)
            ttk.Label(co_frame, text="Checkout %:", font=("Arial", 10)).pack()
            self.co_var = tk.StringVar(value="0.0%")
            ttk.Label(co_frame, textvariable=self.co_var, font=("Arial", 14)).pack()

        # Anzeige für die aktuellen Würfe
        ttk.Label(main_frame, text="Current Throws:", font=("Arial", 10)).pack(pady=(10, 0))
        self.throws_list = tk.Listbox(main_frame, height=3, font=("Arial", 12), justify="center")
        self.throws_list.pack(fill="x")

        # Button zum Verlassen des Spiels
        leave_button = ttk.Button(main_frame, text="Spiel verlassen", command=self.player.leave)
        leave_button.pack(pady=10)

        self.update_score(player.score) # Initiales Update

    def update_score(self, score):
        """Aktualisiert alle Anzeigen auf dem Scoreboard."""
        self.score_var.set(str(score))
        self.throws_list.delete(0, tk.END)
        for throw in self.player.throws:
            self.throws_list.insert(tk.END, f"{throw[0]} {throw[1]}" if throw[0] != "Miss" else "Miss")
        if self.game.name in ('301', '501', '701'):
            self.avg_var.set(f"{self.player.get_average():.2f}")
            self.hf_var.set(str(self.player.stats['highest_finish']))
            self.co_var.set(f"{self.player.get_checkout_percentage():.1f}%")

    def __del__(self):
        """Zerstört das Scoreboard-Fenster, falls es existiert."""
        if self.score_window and self.score_window.winfo_exists():
            self.score_window.destroy()