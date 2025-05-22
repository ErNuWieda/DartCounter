import tkinter as tk
from tkinter import ttk, messagebox

class ScoreBoard:
    def __init__(self, root, player, game):
        self.player = player
        self.game = game
        self.round = game.round
        if len(game.name) == 3:
            self.score = int (game.name)
            self.score_window_x01(root)
        else:
            self.score = 0
            self.score_window_other(root)


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
    def score_window_x01(self, root):
        x = int(root.winfo_screenheight() * 0.9)+60
        x += ((self.player.id-1) % 2) * 350
        y = (self.player.id // 3) * 450
        self.score_window = tk.Toplevel(root)
        self.score_window.title(f"{self.player.name} - {self.game.name}")
        self.score_window.geometry("%dx%d+%d+%d" % (350, 380, x, y))
        self.score_window.resizable(False, False)
        self.score_window.protocol("WM_DELETE_WINDOW", self.leave)
        self.score_label = tk.Label(self.score_window, text=f"Score: {self.score}", font=("Arial", 14), fg="blue")
        self.score_label.pack()


        self.throws_label = tk.Label(self.score_window, text="Würfe:", font=("Arial", 14), fg="blue")
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
        self.text_widget.bind("<Control-z>", lambda event: self.undo())
        self.text_widget.bind("<Control-y>", lambda event: self.redo())
        self.text_widget.pack(fill="both", expand=True)

        # Scrollbar konfigurieren
        # command=text_widget.yview weist die Scrollbar an, das Textfeld zu scrollen
    def score_window_other(self, root):
        x = int(root.winfo_screenheight() * 0.9)+60
        x += ((self.player.id-1) % 2) * 350
        y = (self.player.id // 3) * 450
        self.score_window = tk.Toplevel(root)
        self.score_window.title(f"{self.player.name} - {self.game.name}")
        self.score_window.geometry("%dx%d+%d+%d" % (350, 380, x, y))
        self.score_window.resizable(False, False)
        self.score_window.protocol("WM_DELETE_WINDOW", self.leave)
        self.score_label = tk.Label(self.score_window, text=f"Score: {self.score}", font=("Arial", 14), fg="blue")
        self.score_label.pack()

        if self.game.name in ("Cricket", "Cut Throat"):
            self.cricket_target_vars = {} # Speichert IntVars für Checkbuttons
            self.cb_frame = tk.Frame(self.score_window)
            self.cb_frame.pack(pady=5)

            # player.cricket_targets = ["20", "19", "18", "17", "16", "15", "Bull"]
            for i, target_label_str in enumerate(self.player.cricket_targets):
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
                self.cricket_target_vars[target_label_str] = vars_for_target
    
        # Andere Spieltypen könnten hier eine ähnliche Logik für ihre spezifische Anzeige benötigen
        elif self.game.name == "Around the Clock":
            self.atc_target_vars = {} # Speichert IntVars für Checkbuttons
            self.cb_frame = tk.Frame(self.score_window)
            self.cb_frame.pack(pady=5)

            # player.atc_targets = ["1",..., "20", "Bull"]
            col = 0
            row = 0
            for i, target_label_str in enumerate(self.player.atc_targets):

                if i == 7 or i == 14:
                    col += 2
                    row = 0
                row +=1
                
                # Label für das Ziel (z.B. "20", "19", ..., "Bull")                      
                tk.Label(self.cb_frame, text=target_label_str, width=4, anchor="w").grid(row=row, column=col, sticky="w", padx=(10,5))
                       
                var = tk.IntVar(value=0) # Initialisiert als nicht angehakt (0)
                # Erstelle Checkbutton, verbinde mit var. state="disabled" macht sie nicht-interaktiv.
                cb = tk.Checkbutton(self.cb_frame, variable=var, state="disabled") 
                cb.grid(row=row, column=col + 1, padx=1) # Spalten 1, 2, 3 für Checkbuttons
                # checkbuttons_for_target.append(cb)
                self.atc_target_vars[target_label_str] = var
        

        self.throws_label = tk.Label(self.score_window, text="Würfe:", font=("Arial", 14), fg="blue")
        self.throws_label.pack(padx=5,pady=5)
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
        self.text_widget.pack(fill="x", expand=True)

        # Scrollbar konfigurieren
        # command=text_widget.yview weist die Scrollbar an, das Textfeld zu scrollen
        self.scrollbar.config(command=self.text_widget.yview)

    def update_score(self, score):
        self.score_label.config(text=f"Score: {score}")
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
        
        if len(self.player.throws) <= 3:
            self.text_widget.delete(float(self.game.round), tk.END)
        if self.round != self.game.round:
            self.round = self.game.round
            
        self.add_text_line(text)
    
    def update_cricket_display(self, cricket_hits, current_score):
        self.score_label.config(text=f"Score: {current_score}")

        if self.game.name in ("Cricket", "Cut Throat"):
            if hasattr(self, 'cricket_target_vars'):
                for target_str_from_player_definition in self.player.cricket_targets:
                    hits = cricket_hits.get(target_str_from_player_definition, 0)
                    
                    if target_str_from_player_definition in self.cricket_target_vars:
                        vars_list = self.cricket_target_vars[target_str_from_player_definition]
                        # Setze den Zustand der 3 IntVars basierend auf der Anzahl der Treffer
                        vars_list[0].set(1 if hits >= 1 else 0)
                        vars_list[1].set(1 if hits >= 2 else 0)
                        vars_list[2].set(1 if hits >= 3 else 0)
        # TODO: Die Logik zur Aktualisierung des Text-Widgets mit den Würfen sollte hier
        # ebenfalls aufgerufen werden, ähnlich wie in self.update_score().
        # self._update_throws_text_widget() # (Eine refaktorisierte Methode wäre ideal)
        self.update_score(current_score) # Provisorisch, um zumindest die Würfe anzuzeigen, Score-Label wird hier nochmal gesetzt

    def update_atc_display(self, atc_hit, current_score):
        self.score_label.config(text=f"Score: {current_score}")
        if self.game.name == "Around the Clock":
            if hasattr(self, 'atc_target_vars'):
                for target_str_from_player_definition in self.player.atc_targets:
                    hit = atc_hit.get(target_str_from_player_definition, 0)
                    if target_str_from_player_definition in self.atc_target_vars:
                        var = self.atc_target_vars[target_str_from_player_definition]
                        # Setze den Zustand der IntVar auf Treffer
                        var.set(1 if hit == 1 else 0)

        self.update_score(current_score)