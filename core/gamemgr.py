import tkinter as tk 
from tkinter import ttk
from core.dartboard import DartBoard
from core.game import Game
from core.player import Player

# Zentrale Konfiguration für alle Spielmodi.
# Definiert, welcher Options-Frame angezeigt wird, welche Standardwerte gelten
# und ob es spezielle Regeln wie eine Mindestspieleranzahl gibt.
GAME_CONFIG = {
    # game_name: { "frame": frame_key, "defaults": {option: value}, "min_players": N }
    "301": {"frame": "x01_options", "defaults": {"opt_in": "Single", "opt_out": "Single"}},
    "501": {"frame": "x01_options", "defaults": {"opt_in": "Single", "opt_out": "Single"}},
    "701": {"frame": "x01_options", "defaults": {"opt_in": "Single", "opt_out": "Single"}},
    "Around the Clock": {"frame": "atc_options", "defaults": {"opt_atc": "Single"}},
    "Cricket": {},
    "Cut Throat": {"min_players": 2},
    "Elimination": {"frame": "elimination_options", "defaults": {"count_to": "301", "opt_out": "Single"}, "min_players": 2},
    "Killer": {"frame": "killer_options", "defaults": {"lifes": "3"}, "min_players": 2},
    "Micky Mouse": {},
    "Shanghai": {"frame": "shanghai_options", "defaults": {"rounds": "7"}},
    "Tactics": {},
}
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
        self.el_opt_out_select = None # Eigene Combobox für Elimination Opt-Out
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
        config = GAME_CONFIG.get(self.game, {})

        # 1. Alle Options-Frames ausblenden
        for frame in self.game_option_frames.values():
            frame.pack_forget()

        # 2. Den korrekten Frame basierend auf der Konfiguration anzeigen
        if "frame" in config:
            frame_key = config["frame"]
            self.game_option_frames[frame_key].pack(fill="x", padx=10, pady=5)

        # 3. Standardwerte für Optionen aus der Konfiguration setzen
        if "defaults" in config:
            for option, value in config["defaults"].items():
                if option == "opt_in":
                    self.opt_in_select.set(value)
                    self.opt_in = value
                elif option == "opt_out":
                    # Unterscheiden, welche Combobox gesetzt werden muss
                    if self.game == "Elimination":
                        self.el_opt_out_select.set(value)
                    else: # x01
                        self.opt_out_select.set(value)
                    self.opt_out = value
                elif option == "opt_atc":
                    self.opt_atc_select.set(value)
                    self.opt_atc = value
                elif option == "count_to":
                    self.count_to_select.set(value)
                    self.count_to = value
                elif option == "lifes":
                    self.lifes_select.set(value)
                    self.lifes = value
                elif option == "rounds":
                    self.rounds_select.set(value)
                    self.shanghai_rounds = value

        # 4. Mindestspieleranzahl aus der Konfiguration setzen
        min_players = config.get("min_players", 1)
        if int(self.player_select.get()) < min_players:
            self.player_select.set(str(min_players))
            self.set_anzahl_spieler()

    def set_opt_in(self):
        self.opt_in = self.opt_in_select.get()

    def set_opt_out(self):
        self.opt_out = self.opt_out_select.get()

    def set_opt_atc(self):
        self.opt_atc = self.opt_atc_select.get()

    def set_count_to(self):
        self.count_to = self.count_to_select.get()

    def set_elimination_opt_out(self):
        self.opt_out = self.el_opt_out_select.get()

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

    def _create_players_frame(self, parent):
        """Erstellt den Frame für Spieleranzahl und -namen."""
        tk.Label(parent, text="Spieler", font=("Arial", 12), fg="blue").pack(padx=10, anchor="nw")
        players_frame = tk.Frame(parent, bd=2, relief="groove")
        players_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(players_frame, text="Anzahl", font=("Arial", 12), fg="purple").pack(pady=5)
        plr_values = [str(i) for i in range(1, self.max_players + 1)]
        self.player_select = ttk.Combobox(players_frame, values=plr_values, state="readonly")
        self.player_select.pack()
        self.player_select.bind("<<ComboboxSelected>>", lambda event: self.set_anzahl_spieler())
        self.player_select.current(0)  # Standard auf 1 Spieler

        tk.Label(players_frame, text="Namen", font=("Arial", 12), fg="purple").pack(pady=5)
        self.player_name_entries = [None] * self.max_players
        last_names = self.settings_manager.get('last_player_names', [f"Sp{i+1}" for i in range(self.max_players)]) if self.settings_manager else [f"Sp{i+1}" for i in range(self.max_players)]

        for i in range(self.max_players):
            tk.Label(players_frame, text=f"Spieler {i+1}", font=("Arial", 11), fg="green").pack()
            self.player_name_entries[i] = ttk.Entry(players_frame, font=("Arial", 10))
            self.player_name_entries[i].pack(pady=10 if i == 3 else 0)
            self.player_name_entries[i].insert(0, last_names[i])
            if i >= int(self.player_select.get()):
                self.player_name_entries[i].config(state="disabled")

    def _create_general_settings_frame(self, parent):
        """Erstellt den Frame für allgemeine Einstellungen wie Sound und Theme."""
        tk.Label(parent, text="Einstellungen", font=("Arial", 12), fg="blue").pack(padx=10, pady=(10, 0), anchor="nw")
        general_settings_frame = tk.Frame(parent, bd=2, relief="groove")
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

        tk.Label(general_settings_frame, text="Design-Theme:", font=("Arial", 11)).pack(pady=(10, 0), padx=10, anchor="w")
        self.theme_select = ttk.Combobox(general_settings_frame, values=["Light", "Dark"], state="readonly")
        self.theme_select.pack(pady=5, padx=10, anchor="w")
        self.theme_select.bind("<<ComboboxSelected>>", lambda event: self.set_theme())

        if self.settings_manager:
            current_theme = self.settings_manager.get('theme', 'light')
            self.theme_select.set(current_theme.capitalize())

    def _create_x01_options_frame(self, parent):
        """Erstellt den Frame für x01-spezifische Optionen (Opt In/Out)."""
        x01_frame = tk.Frame(parent)
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
    
    def _create_atc_options_frame(self, parent):
        """Erstellt den Frame für Around the Clock-spezifische Optionen."""
        atc_frame = tk.Frame(parent)
        self.game_option_frames["atc_options"] = atc_frame
        atc_values = ["Single", "Double", "Triple"]
        tk.Label(atc_frame, text="Around The Clock Variante", font=("Arial", 11), fg="green").pack(pady=2)
        self.opt_atc_select = ttk.Combobox(atc_frame, values=atc_values, state="readonly")
        self.opt_atc_select.pack()
        self.opt_atc_select.bind("<<ComboboxSelected>>", lambda event: self.set_opt_atc())
        self.opt_atc_select.current(0)
    
    def _create_elimination_options_frame(self, parent):
        """Erstellt den Frame für Elimination-spezifische Optionen."""
        elimination_frame = tk.Frame(parent)
        self.game_option_frames["elimination_options"] = elimination_frame
        count_to_values = ["301", "501"]
        tk.Label(elimination_frame, text="Count To", font=("Arial", 11), fg="green").pack(pady=2)
        self.count_to_select = ttk.Combobox(elimination_frame, values=count_to_values, state="readonly")
        self.count_to_select.bind("<<ComboboxSelected>>", lambda event: self.set_count_to())
        self.count_to_select.pack()
        el_out_values = ["Single", "Double"]
        tk.Label(elimination_frame, text="Opt Out", font=("Arial", 11), fg="green").pack(pady=2)
        self.el_opt_out_select = ttk.Combobox(elimination_frame, values=el_out_values, state="readonly")
        self.el_opt_out_select.pack()
        self.el_opt_out_select.bind("<<ComboboxSelected>>", lambda event: self.set_elimination_opt_out())
        self.el_opt_out_select.current(0)
    
    def _create_killer_options_frame(self, parent):
        """Erstellt den Frame für Killer-spezifische Optionen."""
        killer_frame = tk.Frame(parent)
        self.game_option_frames["killer_options"] = killer_frame
        life_values = ["3", "5", "7"]
        tk.Label(killer_frame, text="Anzahl Leben", font=("Arial", 11), fg="green").pack(pady=2)
        self.lifes_select = ttk.Combobox(killer_frame, values=life_values, state="readonly")
        self.lifes_select.pack()
        self.lifes_select.bind("<<ComboboxSelected>>", lambda event: self.set_lifes())
        self.lifes_select.current(0)
    
    def _create_shanghai_options_frame(self, parent):
        """Erstellt den Frame für Shanghai-spezifische Optionen."""
        shanghai_frame = tk.Frame(parent)
        self.game_option_frames["shanghai_options"] = shanghai_frame
        rounds_values = ["7", "10", "20"]
        tk.Label(shanghai_frame, text="Anzahl Runden", font=("Arial", 11), fg="green").pack(pady=2)
        self.rounds_select = ttk.Combobox(shanghai_frame, values=rounds_values, state="readonly")
        self.rounds_select.pack()
        self.rounds_select.bind("<<ComboboxSelected>>", lambda event: self.set_rounds())
        self.rounds_select.current(0)

    def _create_dynamic_option_frames(self, parent):
        """Erstellt die (zunächst unsichtbaren) Frames für spielspezifische Optionen."""
        self._create_x01_options_frame(parent)
        self._create_atc_options_frame(parent)
        self._create_elimination_options_frame(parent)
        self._create_killer_options_frame(parent)
        self._create_shanghai_options_frame(parent)

    def _create_game_selection_frame(self, parent):
        """Erstellt den Frame für die Spielauswahl und die dynamischen Options-Frames."""
        tk.Label(parent, text="Varianten", font=("Arial", 12), fg="blue").pack(padx=10, pady=(10, 0), anchor="nw")
        game_selection_frame = tk.Frame(parent, bd=2, relief="groove")
        game_selection_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(game_selection_frame, text="Spiel", font=("Arial", 12), fg="purple").pack()
        self.game_select = ttk.Combobox(game_selection_frame, values=['301', '501', '701', 'Around the Clock', 'Cricket', 'Cut Throat', "Elimination", 'Killer', 'Micky Mouse', 'Shanghai', 'Tactics'], state="readonly")
        self.game_select.pack()
        self.game_select.bind("<<ComboboxSelected>>", lambda event: self.set_game())
        self.game_select.current(0)

        # Die dynamischen Frames werden innerhalb des game_selection_frame erstellt
        self._create_dynamic_option_frames(game_selection_frame)

    def _create_start_button_frame(self, parent):
        """Erstellt den unteren Frame mit dem Start-Button."""
        start_button_frame = tk.Frame(parent)
        start_button_frame.pack(side="bottom", fill="x", pady=10)

        btn = tk.Button(start_button_frame, text="Spiel starten", font=("Arial", 13), fg="red", command=self.run)
        btn.pack()
        btn.bind("<Return>", lambda event: self.run())
        btn.focus_set()

    def game_settings_dlg(self):
        self.settings_dlg = tk.Toplevel()
        self.settings_dlg.title("Spieleinstellungen")
        # Höhe für neue Optionen angepasst
        self.settings_dlg.geometry("320x800")
        self.settings_dlg.resizable(False, True)
        self.settings_dlg.protocol("WM_DELETE_WINDOW", self.goback)
        self.settings_dlg.bind("<Escape>", lambda e: self.goback())
        self.settings_dlg.bind("<Alt-x>", lambda e: self.goback())
        self.settings_dlg.bind("<Alt-q>", lambda e: self.goback())

        # UI-Elemente erstellen
        self._create_players_frame(self.settings_dlg)
        self._create_game_selection_frame(self.settings_dlg)
        self._create_general_settings_frame(self.settings_dlg)
        self._create_start_button_frame(self.settings_dlg)

        # Initialen Zustand der Optionen setzen (zeigt den Frame für "301" an)
        self.set_game()