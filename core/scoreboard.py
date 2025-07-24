import tkinter as tk
from tkinter import ttk

class ScoreBoard:
    """
    Stellt ein separates Fenster für den Spielstand eines Spielers dar,
    inklusive aktueller Punktzahl, Würfe und Statistiken.
    """
    def __init__(self, root, player, game, pos_x, pos_y, width, height: int):
        self.player = player
        self.game = game
        self.hit_check_vars = {} # Hält die BooleanVar-Instanzen für die Checkboxen

        self.score_window = tk.Toplevel(root)
        self.score_window.title(player.name)

        # Fensterbreite für alle Inhalte ausreichend dimensioniert
        self.score_window.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        self.score_window.resizable(False, False)

        main_frame = ttk.Frame(self.score_window, padding="10")
        main_frame.pack(expand=True, fill="both")

        # Anzeige für den Punktestand
        score_frame = ttk.Frame(main_frame)
        score_frame.pack(pady=5)

        score_label_text = "Leben:" if self.game.name == "Killer" else "Score:"
        ttk.Label(score_frame, text=score_label_text, font=("Arial", 12)).pack()
        # Im Killer-Modus wird der Punktestand als Lebenszähler verwendet.
        initial_value = player.score
        self.score_var = tk.StringVar(value=str(initial_value))
        ttk.Label(score_frame, textvariable=self.score_var, font=("Arial", 20, "bold")).pack()

        # Anzeigen für X01-Statistiken
        if self.game.name in ('301', '501', '701'):
            # Rahmen für Checkout-Vorschläge
            checkout_frame = ttk.LabelFrame(main_frame, text="Finish-Vorschlag")
            checkout_frame.pack(pady=10, fill="x", padx=5)
            self.checkout_suggestion_var = tk.StringVar(value="-")
            ttk.Label(checkout_frame, textvariable=self.checkout_suggestion_var, font=("Arial", 14), justify="center").pack(pady=5)

            # Rahmen für 3-Dart-Average
            avg_frame = ttk.Frame(main_frame)
            avg_frame.pack(pady=(0, 5)) # Weniger Abstand nach oben
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

        # Anzeige für Treffer (Cricket, Micky, AtC, etc.)
        if self.game.targets:
            hits_frame = ttk.LabelFrame(main_frame, text="Targets")
            # Wichtig: fill="x", damit der Frame den Platz nutzt.
            hits_frame.pack(pady=10, fill="x", padx=5)

            num_columns = 2  # Anzahl der Spalten für die Ziel-Anzeige

            # Konfiguriere die Spalten im Grid, damit sie sich den Platz teilen
            for i in range(num_columns):
                hits_frame.columnconfigure(i, weight=1)

            for i, target in enumerate(self.player.targets):
                row, col = divmod(i, num_columns)

                target_frame = ttk.Frame(hits_frame)
                target_frame.grid(row=row, column=col, padx=5, pady=2, sticky='ew')

                ttk.Label(target_frame, text=f"{target}:", width=5).pack(side='left')

                # Spiele mit 3 Treffern pro Ziel
                if self.game.name in ("Cricket", "Cut Throat", "Tactics", "Micky Mouse"):
                    self.hit_check_vars[target] = []
                    for _ in range(3):
                        var = tk.BooleanVar()
                        chk = ttk.Checkbutton(target_frame, variable=var, state='disabled')
                        chk.pack(side='left')
                        self.hit_check_vars[target].append(var)
                # Spiele mit 1 Treffer pro Ziel
                elif self.game.name in ("Around the Clock", "Shanghai"):
                    var = tk.BooleanVar()
                    chk = ttk.Checkbutton(target_frame, variable=var, state='disabled')
                    chk.pack(side='left')
                    self.hit_check_vars[target] = [var]  # Als Liste für konsistente Behandlung

        # Anzeige für die aktuellen Würfe
        ttk.Label(main_frame, text="Current Throws:", font=("Arial", 10)).pack(pady=(10, 0))
        self.throws_list = tk.Listbox(main_frame, height=3, font=("Arial", 12), justify="center")
        self.throws_list.pack(fill="x")

        # Button zum Verlassen des Spiels
        leave_button = ttk.Button(main_frame, text="Spiel verlassen", command=self.player.leave)
        leave_button.pack(pady=5)

        self.update_score(initial_value)  # Initiales Update für Score und Würfe
        if self.game.targets:
            self.update_display(self.player.hits, initial_value) # Initiales Update für Checkboxen

    def set_score_value(self, score):
        """Aktualisiert nur den angezeigten Punktwert (oder Leben)."""
        self.score_var.set(str(score))

    def update_checkout_suggestion(self, suggestion):
        """Aktualisiert nur den Text für den Finish-Vorschlag."""
        self.checkout_suggestion_var.set(suggestion)

    def update_score(self, score):
        """Aktualisiert alle Anzeigen auf dem Scoreboard."""
        self.set_score_value(score) # 'score' kann auch Leben sein
        self.throws_list.delete(0, tk.END)
        for throw in self.player.throws:
            self.throws_list.insert(tk.END, f"{throw[0]} {throw[1]}" if throw[0] != "Miss" else "Miss")
        if self.game.name in ('301', '501', '701'):
            self.avg_var.set(f"{self.player.get_average():.2f}")
            self.hf_var.set(str(self.player.stats['highest_finish']))
            self.co_var.set(f"{self.player.get_checkout_percentage():.1f}%")

    def update_display(self, hits, score):
        """Aktualisiert die spielspezifischen Anzeigen wie Treffer-Checkboxes."""
        self.update_score(score)  # Aktualisiert die allgemeinen Teile wie Score und Würfe

        if not self.game.targets:
            return

        for target, vars_list in self.hit_check_vars.items():
            num_hits = hits.get(str(target), 0) # Sicherstellen, dass der Key ein String ist
            for i, var in enumerate(vars_list):
                if i < num_hits:
                    var.set(True)
                else:
                    var.set(False)