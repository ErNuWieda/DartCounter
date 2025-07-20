import tkinter as tk 
from tkinter import ttk
from core.dartboard import DartBoard
from core.game import Game
from core.player import Player

# Klasse für Spielauswahl und Eingabe Playernamen hin
class GameManager:
    def __init__(self, tk_instance, sound_manager=None, settings_manager=None):
        self.root = tk_instance
        self.game = "301"
        self.sound_manager = sound_manager
        self.settings_manager = settings_manager
        self.count_to = "301"
        self.opt_in = "Single"
        self.opt_out = "Single"
        self.opt_atc = "Single"
        self.anzahl_spieler = "1"
        self.lifes = "3"
        self.shanghai_rounds = "7"
        self.max_players = 4
        self.was_started = False # Wichtig für die Kommunikation mit main.py
        self.players = []

        # Widgets, die wir global benötigen, werden erst in game_settings_dlg erstellt
        self.game_select = None
        self.opt_in_select = None
        self.opt_out_select = None
        self.opt_atc_select = None
        self.count_to_select = None
        self.lifes_select = None
        self.rounds_select = None
        self.player_select = None
        self.player_name_entries = []
        self.sound_enabled_var = None
        self.theme_select = None
        self.settings_dlg = None

        # Dictionary zum Speichern der Frames für spielspezifische Optionen
        self.game_option_frames = {}

        # Hier rufen wir das Dialogfenster auf, das nun die Frames erstellt
        self.game_settings_dlg()

    def run(self):
        self.anzahl_spieler = int(self.player_select.get())
        self.players = [] # Vorherige Liste leeren
        for i in range(self.max_players):
            if i < self.anzahl_spieler:
                self.players.append(self.player_name_entries[i].get())

        # Speichere die zuletzt verwendeten Namen
        if self.settings_manager:
            current_names = [entry.get() for entry in self.player_name_entries]
            self.settings_manager.set('last_player_names', current_names)

        self.was_started = True
        self.settings_dlg.destroy()

    def set_game(self):
        self.game = self.game_select.get()

        # Alle Options-Frames ausblenden
        for frame in self.game_option_frames.values():
            frame.pack_forget()

        # Zeige die relevanten Options-Frames an und setze Standardwerte
        # Die Reihenfolge hier definiert nicht die Anzeige-Reihenfolge, nur welche eingeblendet werden
        if self.game in ["301", "501", "701"]:
            self.game_option_frames["x01_options"].pack(fill="x", padx=10, pady=5)
            self.opt_in_select.config(state="readonly")
            self.opt_out_select.config(state="readonly")
            self.opt_in_select.set("Single")
            self.opt_out_select.set("Single")
            self.opt_in = "Single"
            self.opt_out = "Single"

        if self.game == "Around the Clock":
            self.game_option_frames["atc_options"].pack(fill="x", padx=10, pady=5)
            self.opt_atc_select.config(state="readonly")
            self.opt_atc_select.set("Single")
            self.opt_atc = "Single"
        
        if self.game == "Elimination":
            self.game_option_frames["elimination_options"].pack(fill="x", padx=10, pady=5)
            self.count_to_select.config(state="readonly")
            self.count_to_select.set("301")
            self.count_to = "301"
            self.opt_out_select.config(state="readonly")
            self.opt_out_select.set("Single")
            self.opt_out = "Single"
    

        if self.game == "Killer":
            self.game_option_frames["killer_options"].pack(fill="x", padx=10, pady=5)
            self.lifes_select.config(state="readonly")
            self.lifes_select.set("3")
            self.lifes = "3"

        if self.game == "Shanghai":
            self.game_option_frames["shanghai_options"].pack(fill="x", padx=10, pady=5)
            self.rounds_select.config(state="readonly")
            self.rounds_select.set("7")
            self.shanghai_rounds = "7"

        # Spezielle Logik für Spieleranzahl bei Cut Throat Elimination und Killer
        if self.game in ("Cut Throat", "Elimination","Killer"):
            self.player_select.set("2")
            self.set_anzahl_spieler()
        else:
            if int(self.player_select.get()) > 1:
                 self.player_select.set("1")
                 self.set_anzahl_spieler()

    def set_opt_in(self):
        self.opt_in = self.opt_in_select.get()

    def set_opt_out(self):
        self.opt_out = self.opt_out_select.get()

    def set_opt_atc(self):
        self.opt_atc = self.opt_atc_select.get()

    def set_lifes(self):
        self.lifes = self.lifes_select.get()

    def set_rounds(self):
        self.shanghai_rounds = self.rounds_select.get()

    def set_anzahl_spieler(self):
        self.anzahl_spieler = int(self.player_select.get())
        for i in range(self.max_players):
            if i < self.anzahl_spieler:
                self.player_name_entries[i].config(state="normal")
            else:
                self.player_name_entries[i].config(state="disabled")
                self.player_name_entries[i].delete(0, tk.END)
                self.player_name_entries[i].insert(0, f"Sp{i+1}")

    def goback(self):
        self.root.deiconify()
        self.settings_dlg.destroy()

    def toggle_sound_setting(self):
        """Wird vom Checkbutton aufgerufen, um Sounds umzuschalten."""
        if self.sound_manager and self.sound_enabled_var:
            is_enabled = self.sound_enabled_var.get()
            self.sound_manager.toggle_sounds(is_enabled)

    def set_theme(self):
        """Wird vom Combobox aufgerufen, um das Theme zu ändern."""
        if self.settings_manager and self.theme_select:
            selected_theme = self.theme_select.get().lower()  # "Light" -> "light"
            try:
                import sv_ttk
                sv_ttk.set_theme(selected_theme)
                self.settings_manager.set('theme', selected_theme)
            except ImportError:
                print("sv-ttk nicht gefunden. Theme kann nicht geändert werden.")
            except Exception as e:
                print(f"Fehler beim Setzen des Themes: {e}")


    def game_settings_dlg(self):
        self.settings_dlg = tk.Toplevel()
        self.settings_dlg.title("Spieleinstellungen")
        # Höhe für neue Optionen angepasst
        self.settings_dlg.geometry("320x750")
        self.settings_dlg.resizable(False, True)
        self.settings_dlg.protocol("WM_DELETE_WINDOW", self.goback)
        self.settings_dlg.bind("<Escape>", lambda e: self.goback())
        self.settings_dlg.bind("<Alt-x>", lambda e: self.goback())
        self.settings_dlg.bind("<Alt-q>", lambda e: self.goback())

        # --- Spieleranzahl und -namen (Jetzt als ERSTES!) ---
        tk.Label(self.settings_dlg, text="Spieler", font=("Arial", 12), fg="blue").pack(padx=10, anchor="nw")
        players_frame = tk.Frame(self.settings_dlg, bd=2, relief="groove")
        players_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(players_frame, text="Anzahl", font=("Arial", 12), fg="purple").pack(pady=5)
        plr_values = [str(i) for i in range(1, self.max_players + 1)]
        self.player_select = ttk.Combobox(players_frame, values=plr_values, state="readonly")
        self.player_select.pack()
        self.player_select.bind("<<ComboboxSelected>>", lambda event: self.set_anzahl_spieler())
        self.player_select.current(0) # Standard auf 1 Spieler

        tk.Label(players_frame, text="Namen", font=("Arial", 12), fg="purple").pack(pady=5)
        self.player_name_entries = [None] * self.max_players
        last_names = self.settings_manager.get('last_player_names', [f"Sp{i+1}" for i in range(self.max_players)]) if self.settings_manager else [f"Sp{i+1}" for i in range(self.max_players)]

        for i in range(self.max_players):
            tk.Label(players_frame, text=f"Spieler {i+1}", font=("Arial", 11), fg="green").pack()
            self.player_name_entries[i] = ttk.Entry(players_frame, font=("Arial", 10))
            self.player_name_entries[i].pack(pady=10 if i==3 else 0)
            self.player_name_entries[i].insert(0, last_names[i])
            if i >= int(self.player_select.get()):
                self.player_name_entries[i].config(state="disabled")

        # --- Spielauswahl (Als Nächstes) ---
        tk.Label(self.settings_dlg, text="Einstellungen", font=("Arial", 12), fg="blue").pack(padx=10, pady=(10,0), anchor="nw")

        # Frame für allgemeine Einstellungen (z.B. Sound)
        general_settings_frame = tk.Frame(self.settings_dlg, bd=2, relief="groove")
        general_settings_frame.pack(fill="x", padx=10, pady=5)

        self.sound_enabled_var = tk.BooleanVar()
        if self.sound_manager:
            self.sound_enabled_var.set(self.sound_manager.sounds_enabled)

        sound_check = ttk.Checkbutton(
            general_settings_frame,
            text="Soundeffekte aktivieren",
            variable=self.sound_enabled_var,
            command=self.toggle_sound_setting
        )
        sound_check.pack(pady=5, padx=10, anchor="w")

        # Theme-Auswahl
        tk.Label(general_settings_frame, text="Design-Theme:", font=("Arial", 11)).pack(pady=(10, 0), padx=10, anchor="w")
        self.theme_select = ttk.Combobox(general_settings_frame, values=["Light", "Dark"], state="readonly")
        self.theme_select.pack(pady=5, padx=10, anchor="w")
        self.theme_select.bind("<<ComboboxSelected>>", lambda event: self.set_theme())

        if self.settings_manager:
            current_theme = self.settings_manager.get('theme', 'light')
            self.theme_select.set(current_theme.capitalize())  # "light" -> "Light"


        game_selection_frame = tk.Frame(self.settings_dlg, bd=2, relief="groove") # Separater Frame für die Spielauswahl
        game_selection_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(game_selection_frame, text="Spiel", font=("Arial", 12), fg="purple").pack()
        self.game_select = ttk.Combobox(game_selection_frame, values=['301', '501', '701', 'Around the Clock', 'Cricket', 'Cut Throat', "Elimination", 'Killer', 'Micky Mouse', 'Shanghai', 'Tactics'], state="readonly")
        self.game_select.pack()
        self.game_select.bind("<<ComboboxSelected>>", lambda event: self.set_game())
        self.game_select.current(0)

        # --- Dynamische Frames für spielspezifische Optionen (danach, aber noch unsichtbar) ---

        # Frame für x01-Optionen (Opt In/Out)
        x01_frame = tk.Frame(game_selection_frame)
        self.game_option_frames["x01_options"] = x01_frame
        values = ["Single", "Double", "Masters"]
        tk.Label(x01_frame, text="Opt In", font=("Arial", 11), fg="green").pack(pady=2)
        self.opt_in_select = ttk.Combobox(x01_frame, values=values, state="readonly")
        self.opt_in_select.pack()
        self.opt_in_select.bind("<<ComboboxSelected>>", lambda event: self.set_opt_in())
        self.opt_in_select.current(0)

        tk.Label(x01_frame, text="Opt Out", font=("Arial", 11), fg="green").pack(pady=2)
        self.opt_out_select = ttk.Combobox(x01_frame, values=values, state="readonly")
        self.opt_out_select.pack()
        self.opt_out_select.bind("<<ComboboxSelected>>", lambda event: self.set_opt_out())
        self.opt_out_select.current(0)

        # Frame für Around the Clock Varianten
        atc_frame = tk.Frame(game_selection_frame)
        self.game_option_frames["atc_options"] = atc_frame
        atc_values = ["Single", "Double", "Triple"]
        tk.Label(atc_frame, text="Around The Clock Variante", font=("Arial", 11), fg="green").pack(pady=2)
        self.opt_atc_select = ttk.Combobox(atc_frame, values=atc_values, state="readonly")
        self.opt_atc_select.pack()
        self.opt_atc_select.bind("<<ComboboxSelected>>", lambda event: self.set_opt_atc())
        self.opt_atc_select.current(0)

        # Frame für Elimination Varianten
        elimination_frame = tk.Frame(game_selection_frame)
        self.game_option_frames["elimination_options"] = elimination_frame
        count_to_values = ["301", "501"]
        tk.Label(elimination_frame, text="Count To", font=("Arial", 11), fg="green").pack(pady=2)
        self.count_to_select = ttk.Combobox(elimination_frame, values=count_to_values, state="readonly")
        self.count_to_select.pack()
        el_out_values = ["Single", "Double"]
        tk.Label(elimination_frame, text="Opt Out", font=("Arial", 11), fg="green").pack(pady=2)
        self.opt_out_select = ttk.Combobox(elimination_frame, values=el_out_values, state="readonly")
        self.opt_out_select.pack()
        self.opt_out_select.bind("<<ComboboxSelected>>", lambda event: self.set_opt_out())
        self.opt_out_select.current(0)

        # Frame für Killer-Optionen (Anzahl Leben)
        killer_frame = tk.Frame(game_selection_frame)
        self.game_option_frames["killer_options"] = killer_frame
        life_values = ["3", "5", "7"]
        tk.Label(killer_frame, text="Anzahl Leben", font=("Arial", 11), fg="green").pack(pady=2)
        self.lifes_select = ttk.Combobox(killer_frame, values=life_values, state="readonly")
        self.lifes_select.pack()
        self.lifes_select.bind("<<ComboboxSelected>>", lambda event: self.set_lifes())
        self.lifes_select.current(0)

        # Frame für Shanghai-Optionen (Anzahl Runden)
        shanghai_frame = tk.Frame(game_selection_frame)
        self.game_option_frames["shanghai_options"] = shanghai_frame
        rounds_values = ["7", "10", "20"]
        tk.Label(shanghai_frame, text="Anzahl Runden", font=("Arial", 11), fg="green").pack(pady=2)
        self.rounds_select = ttk.Combobox(shanghai_frame, values=rounds_values, state="readonly")
        self.rounds_select.pack()
        self.rounds_select.bind("<<ComboboxSelected>>", lambda event: self.set_rounds())
        self.rounds_select.current(0)

        # --- Start-Button in einem festen Frame (Wird ZULETZT gepackt!) ---
        start_button_frame = tk.Frame(self.settings_dlg)
        start_button_frame.pack(side="bottom", fill="x", pady=10) # side="bottom" ist hier entscheidend!

        btn = tk.Button(start_button_frame, text="Spiel starten", font=("Arial", 13), fg="red", command=self.run)
        btn.pack() # Packe den Button innerhalb dieses Frames
        btn.bind("<Return>", lambda event: self.run())
        btn.focus_set()

        # Initialen Zustand der Optionen setzen (zeigt den Frame für "301" an)
        self.set_game()