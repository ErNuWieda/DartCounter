import tkinter as tk
from tkinter import ttk, messagebox

class ScoreBoard:
    def __init__(self, root, player, game):
        self.root = root
        self.player = player
        self.game = game
        self.round = game.round
        if len(game.name) == 3:
            self.score = int (game.name)
            self.score_window_x01()
        else:
            self.score = 0
            self.target_vars = {} # Speichert IntVars für Checkbuttons
            self.score_window_other()


    def __del__(self):
        self.score_window.destroy()

    def leave(self):
        confirm = messagebox.askyesno("Spiel verlassen", "Willst du wirklich das Spiel verlassen?")
        if confirm:
            self.player.leave()
            self.__del__()
        else:
            return
    
    def add_text_line(self, text):
        # tk.END sorgt dafür, dass der neue Text am Ende eingefügt wird
        # "\n" fügt einen Zeilenumbruch hinzu, damit jede Zeile neu beginnt
        self.text_widget.insert(tk.END, text+"\n")
        # Optional: Automatisch zum Ende scrollen, um die neueste Zeile zu sehen
        self.text_widget.see(tk.END)

    # Scorefenster erstellen
    def create_score_window(self):
        x = int(self.root.winfo_screenheight() * 0.9)+60
        x += ((self.player.id-1) % 2) * 350
        y = (self.player.id // 3) * 450
        self.score_window = tk.Toplevel(self.root)
        self.score_window.title(f"{self.player.name} - {self.game.name}")
        self.score_window.geometry("%dx%d+%d+%d" % (350, 400, x, y))
        self.score_window.resizable(False, False)
        self.score_window.protocol("WM_DELETE_WINDOW", self.leave)

    def create_throw_history(self):
        self.throws_label = tk.Label(self.score_window, text="Wurf-Historie:", font=("Arial", 10), fg="blue")
        self.throws_label.pack(padx=5, pady=5)
        # Frame für das Textfeld und die Scrollbar erstellen
        # Dies hilft, die Scrollbar und das Textfeld zusammen zu layouten
        self.text_frame = ttk.Frame(self.score_window)
        self.text_frame.pack()

        # Scrollbar erstellen
        self.scrollbar = ttk.Scrollbar(self.text_frame)
        self.scrollbar.pack(side="right", fill="y")
        # Textfeld erstellen
        # yscrollcommand=scrollbar.set weist das Textfeld an, die Scrollbar zu aktualisieren, wenn gescrollt wird
        self.text_widget = tk.Text(self.text_frame, wrap="word", yscrollcommand=self.scrollbar.set)
        self.text_widget.pack(fill="both", expand=True)

        # Scrollbar konfigurieren
        # command=text_widget.yview weist die Scrollbar an, das Textfeld zu scrollen
        self.scrollbar.config(command=self.text_widget.yview)

    def score_window_x01(self):
        self.create_score_window()
        self.score_label = tk.Label(self.score_window, text=f"Punkte: {self.score}", font=("Arial", 14), fg="blue")
        self.score_label.pack()
        self.create_throw_history()


    def _create_target_checkbuttons(self, num_checks_per_target, layout='list'):
        """Hilfsmethode zur Erstellung der Ziel-Checkbuttons."""
        self.cb_frame = tk.Frame(self.score_window)
        self.cb_frame.pack(pady=5)

        if layout == 'list':
            row = 0
            col = 0
            lwidth = 4
            shanghai_list = False
            if self.game.name == "Shanghai":
                shanghai_list = True
                lwidth = 2
            for i, target_label_str in enumerate(self.player.targets):
                if shanghai_list:
                    if i > 0 and i % 10 == 0:  # Neue Spalte nach 10 Zielen
                        col += num_checks_per_target + 2
                        row = 0
                tk.Label(self.cb_frame, text=target_label_str, width=lwidth, anchor="w").grid(row=row, column=col, sticky="w", padx=(10, 5))
                vars_for_target = []
                for j in range(num_checks_per_target):
                    var = tk.IntVar(value=0)
                    vars_for_target.append(var)
                    cb = tk.Checkbutton(self.cb_frame, variable=var, state="disabled")
                    cb.grid(row=row, column=col +j + 1, padx=1)
                self.target_vars[target_label_str] = vars_for_target
                row += 1

        elif layout == 'grid':
            col = 0
            row = 0
            for i, target_label_str in enumerate(self.player.targets):
                if i > 0 and i % 7 == 0:  # Neue Spalte nach 7 Zielen
                    col += 2
                    row = 0
                tk.Label(self.cb_frame, text=target_label_str, width=4, anchor="w").grid(row=row, column=col, sticky="w", padx=(10, 5))
                vars_for_target = [tk.IntVar(value=0)]
                cb = tk.Checkbutton(self.cb_frame, variable=vars_for_target[0], state="disabled")
                cb.grid(row=row, column=col + 1, padx=1)
                self.target_vars[target_label_str] = vars_for_target
                row += 1

    def score_window_other(self):
        self.create_score_window()
        game_name = self.game.name

        match game_name:
            case "Cricket" | "Cut Throat" | "Tactics":
                self.score_label = tk.Label(self.score_window, text=f"Punkte: {self.score}", font=("Arial", 14), fg="blue")
                self.score_label.pack()
                self._create_target_checkbuttons(num_checks_per_target=3, layout='list')
            case "Micky Mouse":
                self.score_label = tk.Label(self.score_window, text=f"Nächstes Ziel: {self.player.next_target}", font=("Arial", 14), fg="blue")
                self.score_label.pack()
                self._create_target_checkbuttons(num_checks_per_target=3, layout='list')
            case "Around the Clock":
                opt_atc = "" if self.game.opt_atc == "Single" else self.game.opt_atc + " "
                self.score_label = tk.Label(self.score_window, text=f"Nächstes Ziel: {opt_atc}{self.player.next_target}", font=("Arial", 14), fg="blue")
                self.score_label.pack()
                self._create_target_checkbuttons(num_checks_per_target=1, layout='grid')
            case "Shanghai":
                self.score_label= tk.Label(self.score_window, text=f"Punkte: {self.score}", font=("Arial", 14), fg="blue")
                self.score_label.pack()
                self.target_label = tk.Label(self.score_window, text=f"Ziel: {self.player.next_target}", font=("Arial", 14), fg="blue")
                self.target_label.pack()
                self._create_target_checkbuttons(num_checks_per_target=3, layout='list')
            case "Killer":
                self.lifes_label = tk.Label(self.score_window, text=f"Leben: {self.player.lifes}", font=("Arial", 14), fg="blue")
                self.lifes_label.pack()
                self.life_segment_label = tk.Label(self.score_window, text=f"Lebensfeld: {self.player.life_segment}", font=("Arial", 14), fg="blue")
                self.life_segment_label.pack()

        self.create_throw_history()
        
        
    def update_score(self, score):
        if self.game.name == "Killer":
            self.lifes_label.config(text=f"Leben: {self.player.lifes}")
            self.life_segment_label.config(text=f"Lebensfeld: Double {self.player.life_segment}")
        elif self.game.name == "Around the Clock":
            if self.game.opt_atc == "Single" or self.player.next_target in ("Bull", "Bullseye"):
                opt_atc = ""
            else:
                opt_atc = self.game.opt_atc + " "
            self.score_label.config(text=f"Nächstes Ziel: {opt_atc}{self.player.next_target}")
        elif self.game.name == "Micky Mouse":
            self.score_label.config(text=f"Nächstes Ziel: {self.player.next_target}")
        elif self.game.name == "Shanghai":
            self.score_label.config(text=f"Punkte: {score}")
            self.target_label.config(text=f"Ziel: {self.player.next_target}")
        else:
            self.score_label.config(text=f"Punkte: {score}")

        throws = ""
        for i in range(len(self.player.throws)):
            ring, segment = self.player.throws[i]
            if ring == "Miss":
                throw = "X"
            elif ring == "Bullseye":
                throw = "Bullseye"
            elif ring == "Bull":
                throw = "Bull"
            else:    
                throw = ring[0] + str(segment) 
            if i < 2:
                throw += ", "
            throws += throw  
        text = f"Runde {self.game.round}: {throws}"
        if self.game.round > 1:
            text=f"\n{text}"
        if self.player.is_active:
            if len(self.player.throws) <= 3:
                self.text_widget.delete(float(self.game.round), tk.END)
            if self.round != self.game.round:
                self.round = self.game.round
            self.add_text_line(text)
    
    def update_display(self, target_hits, current_score):
        if hasattr(self, 'target_vars'):
            for target_str_from_player_definition in self.player.targets:
                hits = target_hits.get(target_str_from_player_definition, 0)
                if target_str_from_player_definition in self.target_vars:
                    vars_list = self.target_vars[target_str_from_player_definition]
                    # Setze den Zustand der IntVars basierend auf der Anzahl der Treffer
                    vars_list[0].set(1 if hits >= 1 else 0)
                    if len(vars_list) > 1:
                        vars_list[1].set(1 if hits >= 2 else 0)
                        vars_list[2].set(1 if hits >= 3 else 0)
                    
        self.update_score(current_score) # Provisorisch, um zumindest die Wurf-Historie anzuzeigen, Score-Label wird hier nochmal gesetzt
