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
        self.score_window.geometry("%dx%d+%d+%d" % (350, 380, x, y))
        self.score_window.resizable(False, False)
        self.score_window.protocol("WM_DELETE_WINDOW", self.leave)

    def create_throw_history(self):
        self.throws_label = tk.Label(self.score_window, text="Wurf-Historie:", font=("Arial", 14), fg="blue")
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


    def score_window_other(self):
        self.create_score_window()
        if self.game.name in ("Cricket", "Cut Throat", "Tactics"):
            self.score_label = tk.Label(self.score_window, text=f"Punkte: {self.score}", font=("Arial", 14), fg="blue")
            self.score_label.pack()
            self.cb_frame = tk.Frame(self.score_window)
            self.cb_frame.pack(pady=5)

            # player.cricket_targets = ["20", "19", "18", "17", "16", "15", "Bull"]
            for i, target_label_str in enumerate(self.player.targets):
                # Label für das Ziel (z.B. "20", "19", ..., "Bull")
                tk.Label(self.cb_frame, text=target_label_str, width=4, anchor="w").grid(row=i, column=0, sticky="w", padx=(10,5))
                
                vars_for_target = []
                # checkbuttons_for_target = [] # Optional: um Widgets zu speichern
                for j in range(3): # 3 Checkmarks (Treffer) pro Ziel
                    var = tk.IntVar(value=0) # Initialisiert als nicht angehakt (0)
                    vars_for_target.append(var)
                    # Erstelle Checkbutton, verbinde mit var. state="disabled" macht sie nicht-interaktiv.
                    cb = tk.Checkbutton(self.cb_frame, variable=var, state="disabled") 
                    cb.grid(row=i, column=j + 1, padx=1) # Spalten 1, 2, 3 für Checkbuttons
                    # checkbuttons_for_target.append(cb)
                self.target_vars[target_label_str] = vars_for_target
    
        # Andere Spieltypen könnten hier eine ähnliche Logik für ihre spezifische Anzeige benötigen
        elif self.game.name == "Around the Clock":
            if self.game.opt_atc == "Single":
                opt_atc = ""
            else:
                opt_atc = self.game.opt_atc + " "
            self.score_label = tk.Label(self.score_window, text=f"Nächstes Ziel: {opt_atc}{self.player.next_target}", font=("Arial", 14), fg="blue")
            self.score_label.pack()
            self.cb_frame = tk.Frame(self.score_window)
            self.cb_frame.pack(pady=5)

            # player.atc_targets = ["1",..., "20", "Bull"]
            col = 0
            row = 0
            for i, target_label_str in enumerate(self.player.targets):

                if i == 7 or i == 14:
                    col += 2
                    row = 0
                row +=1

                vars_for_target = []               
                # Label für das Ziel (z.B. "20", "19", ..., "Bull")                      
                tk.Label(self.cb_frame, text=target_label_str, width=4, anchor="w").grid(row=row, column=col, sticky="w", padx=(10,5))
                       
                var = tk.IntVar(value=0) # Initialisiert als nicht angehakt (0)
                vars_for_target.append(var)
                # Erstelle Checkbutton, verbinde mit var. state="disabled" macht sie nicht-interaktiv.
                cb = tk.Checkbutton(self.cb_frame, variable=var, state="disabled") 
                cb.grid(row=row, column=col + 1, padx=1) # Spalten 1, 2, 3 für Checkbuttons
                # checkbuttons_for_target.append(cb)
                self.target_vars[target_label_str] = vars_for_target


        elif self.game.name == "Micky Mouse":
            self.score_label = tk.Label(self.score_window, text=f"Nächstes Ziel: {self.player.next_target}", font=("Arial", 14), fg="blue")
            self.score_label.pack()
            self.cb_frame = tk.Frame(self.score_window)
            self.cb_frame.pack(pady=5)

            for i, target_label_str in enumerate(self.player.targets):
                # Label für das Ziel (z.B. "20", "19", ..., "Bull")
                tk.Label(self.cb_frame, text=target_label_str, width=4, anchor="w").grid(row=i, column=0, sticky="w", padx=(10,5))
                
                vars_for_target = []
                # checkbuttons_for_target = [] # Optional: um Widgets zu speichern
                for j in range(3): # 3 Checkmarks (Treffer) pro Ziel
                    var = tk.IntVar(value=0) # Initialisiert als nicht angehakt (0)
                    vars_for_target.append(var)
                    # Erstelle Checkbutton, verbinde mit var. state="disabled" macht sie nicht-interaktiv.
                    cb = tk.Checkbutton(self.cb_frame, variable=var, state="disabled") 
                    cb.grid(row=i, column=j + 1, padx=1) # Spalten 1, 2, 3 für Checkbuttons
                    # checkbuttons_for_target.append(cb)
                self.target_vars[target_label_str] = vars_for_target
        elif self.game.name == "Killer":
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
                    else:
                        break
        self.update_score(current_score) # Provisorisch, um zumindest die Wurf-Historie anzuzeigen, Score-Label wird hier nochmal gesetzt
