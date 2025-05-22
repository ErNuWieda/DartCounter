import tkinter as tk
from tkinter import ttk
from core.dartboard import DartBoard
from core.game import Game
from core.player import Player

# Klasse für Spielauswahl und Eingabe Playernamen hin
class GameManager:
    def __init__(self, tk_instance):
        self.root = tk_instance
        self.game = "301"
        self.opt_in = "Single"
        self.opt_out = "Single"
        self.opt_atc = "Single"
        self.anzahl_spieler = "1"
        self.max_players = 4
        self.players = []
        self.game_select, self.opt_in_select, self.opt_out_select, self.opt_atc_select, self.player_select, self.player_name, self.settings_dlg = self.game_settings_dlg()
        

    def run(self):
        self.anzahl_spieler = int(self.player_select.get())
        for i in range(self.max_players):
            if i < self.anzahl_spieler:
                self.players.append(self.player_name[i].get())

        self.start_game()


    def start_game(self):
        self.settings_dlg.destroy()
        game_options = (self.game, self.opt_in, self.opt_out, self.opt_atc)
        spiel_instanz = Game(self.root, game_options, self.players)
        db_instanz = DartBoard(spiel_instanz) # Übergibt die Game-Instanz an DartBoard
        spiel_instanz.db = db_instanz         # Macht die DartBoard-Instanz der Game-Instanz bekannt

    def set_game(self):
        self.game = self.game_select.get()
        if self.game not in ["301", "501", "701"]:
            self.opt_in_select.config(state="disabled")
            self.opt_out_select.config(state="disabled")
        else:
            self.opt_in_select.config(state="readonly")
            self.opt_out_select.config(state="readonly")
            self.opt_atc_select.config(state="disabled")
        if self.game == "Around the Clock":
           self.opt_atc_select.config(state="readonly")
        else:
            self.opt_atc_select.config(state="disabled")

    def set_opt_in(self):
        self.opt_in = self.opt_in_select.get()

    def set_opt_out(self):
        self.opt_out = self.opt_out_select.get()
    
    def set_opt_atc(self):
        self.opt_atc = self.opt_atc_select.get()

    def set_anzahl_spieler(self):
        self.anzahl_spieler = int(self.player_select.get())
        for i in range(self.max_players):
            if i < self.anzahl_spieler:
                self.player_name[i].config(state="normal")
            else:
                self.player_name[i].config(state="disabled")

    def goback(self):
        self.root.deiconify()
        self.settings_dlg.destroy()

    def game_settings_dlg(self):
        # Spiel auswählen
        dialog = tk.Toplevel()
        dialog.title("Dartcounter - Spieleinstellungen")
        dialog.geometry("320x600")
        dialog.resizable(False, False)
        dialog.protocol("WM_DELETE_WINDOW", lambda: self.goback())
        dialog.bind("<Escape>", lambda e: self.goback())
        dialog.bind("<Alt-x>", lambda e: self.goback())
        dialog.bind("<Alt-q>", lambda e: self.goback())
        
        tk.Label(dialog, text="Spiel", font=("Arial", 14), fg="blue").pack()
        game_select = ttk.Combobox(dialog, values=['301', '501', '701', 'Around the Clock', 'Cricket', 'Cut Throat', 'Shanghai'], state="readonly")
        game_select.pack()
        game_select.bind("<<ComboboxSelected>>", lambda event: self.set_game())
        game_select.current(0)
        
        # In-/Out-Optionen für x01-Spiele
        values = ["Single", "Double", "Masters"]
        tk.Label(dialog, text="Opt In ", font=("Arial", 14), fg="blue").pack(pady=5)
        opt_in_select = ttk.Combobox(dialog, values=values, state="readonly")
        opt_in_select.pack()
        opt_in_select.bind("<<ComboboxSelected>>", lambda event: self.set_opt_in())
        opt_in_select.current(0)
        
        tk.Label(dialog, text="Opt Out", font=("Arial", 14), fg="blue").pack(pady=5)
        opt_out_select = ttk.Combobox(dialog, values=values, state="readonly")
        opt_out_select.pack()
        opt_out_select.bind("<<ComboboxSelected>>", lambda event: self.set_opt_out())
        opt_out_select.current(0)
        
        # Around the Clock Varianten
        atc_values = ["Single", "Double", "Triple"]
        tk.Label(dialog, text="Around The Clock", font=("Arial", 14), fg="blue").pack(pady=5)
        opt_atc_select = ttk.Combobox(dialog, values=atc_values, state="disabled")
        opt_atc_select.pack()
        opt_atc_select.bind("<<ComboboxSelected>>", lambda event: self.set_opt_atc())
        opt_atc_select.current(0)
        
        # Spieleranzahl und -namen
        tk.Label(dialog, text="Spieleranzahl", font=("Arial", 14), fg="blue").pack(pady=5)
        plr_values = []
        for i in range(1, self.max_players+1):
            plr_values.append(str(i))
        player_select = ttk.Combobox(dialog, values=plr_values, state="readonly")
        player_select.pack()
        player_select.bind("<<ComboboxSelected>>", lambda event: self.set_anzahl_spieler())
        player_select.current(0)

        tk.Label(dialog, text="Spielernamen", font=("Arial", 14), fg="blue").pack(pady=5)
        spieler = int(player_select.get())
        player_name = [None] * self.max_players
        for i in range(self.max_players):
            tk.Label(dialog, text=f"Spieler {i+1}", font=("Arial", 13), fg="green").pack()
            player_name[i] = ttk.Entry(dialog, font=("Arial", 12))
            player_name[i].pack()
            if i >= spieler:
                player_name[i].config(state="disabled")
        

        # Start-Button
        btn = tk.Button(dialog, text="Spiel starten", font=("Arial", 14), fg="red", command=self.run)
        btn.pack(pady=20)   

        return game_select, opt_in_select, opt_out_select, opt_atc_select, player_select, player_name, dialog