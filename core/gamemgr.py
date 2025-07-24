import tkinter as tk 
from tkinter import ttk
import json
import pathlib

def _load_game_config():
    """Lädt die Spielkonfigurationen aus der JSON-Datei."""
    try:
        base_path = pathlib.Path(__file__).resolve().parent
        json_path = base_path / "game_config.json"
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Fehler beim Laden der Spielkonfiguration: {e}")
        return {}

# Die Spielkonfiguration wird nur einmal beim Import des Moduls geladen.
GAME_CONFIG = _load_game_config()

class GameManager:
    """
    Ein Controller, der die Spielkonfiguration verwaltet, ohne UI-Logik zu enthalten.
    Er delegiert die UI-Darstellung an den GameSettingsDialog.
    """
    def __init__(self, sound_manager=None, settings_manager=None):
        self.sound_manager = sound_manager
        self.settings_manager = settings_manager

        # Attribute, die die finalen Spieleinstellungen speichern
        self.game = "301"
        self.count_to = "301"
        self.opt_in = "Single"
        self.opt_out = "Single"
        self.opt_atc = "Single"
        self.lifes = "3"
        self.shanghai_rounds = "7"
        self.players = []

    def configure_game(self, parent_window):
        """
        Öffnet den Einstellungsdialog, wartet auf Benutzereingaben und
        übernimmt die Einstellungen, wenn das Spiel gestartet wird.

        Args:
            parent_window (tk.Toplevel or tk.Tk): Das übergeordnete Fenster.

        Returns:
            bool: True, wenn der Benutzer das Spiel gestartet hat, sonst False.
        """
        dialog = GameSettingsDialog(parent_window, self.settings_manager)
        parent_window.wait_window(dialog) # Blockiert, bis der Dialog geschlossen wird

        if dialog.was_started:
            self.game = dialog.game
            self.count_to = dialog.count_to
            self.opt_in = dialog.opt_in
            self.opt_out = dialog.opt_out
            self.opt_atc = dialog.opt_atc
            self.lifes = dialog.lifes
            self.shanghai_rounds = dialog.shanghai_rounds
            self.players = dialog.players
            return True
        return False

# Neue, UI-fokussierte Klasse für den Einstellungsdialog.
# Diese Klasse ist noch nicht integriert und dient als erster Schritt des Refactorings.
class GameSettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings_manager=None):
        super().__init__(parent)
        self.parent = parent
        self.settings_manager = settings_manager

        # --- Zustandvariablen zur Speicherung der ausgewählten Einstellungen ---
        self.game = "301"
        self.count_to = "301"
        self.opt_in = "Single"
        self.opt_out = "Single"
        self.opt_atc = "Single"
        self.anzahl_spieler = "1"
        self.lifes = "3"
        self.shanghai_rounds = "7"
        self.max_players = 4
        self.was_started = False
        self.players = []

        # --- UI Widgets ---
        self.game_select = None
        self.opt_in_select = None
        self.opt_out_select = None
        self.opt_atc_select = None
        self.el_opt_out_select = None
        self.count_to_select = None
        self.lifes_select = None
        self.rounds_select = None
        self.player_select = None
        self.player_name_entries = []
        self.game_option_frames = {}

        # --- Dialog aufbauen ---
        self.title("Spieleinstellungen")
        self.geometry("320x650")
        self.resizable(False, True)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())

        # UI-Elemente erstellen
        self._create_players_frame(self)
        self._create_game_selection_frame(self)
        self._create_start_button_frame(self)

        # Initialen Zustand der Optionen setzen
        self.set_game()

    def _on_start(self):
        """Entspricht der alten 'run'-Methode."""
        self.anzahl_spieler = int(self.player_select.get())
        self.players = []
        for i in range(self.max_players):
            if i < self.anzahl_spieler:
                self.players.append(self.player_name_entries[i].get())

        if self.settings_manager:
            current_names = [entry.get() for entry in self.player_name_entries]
            self.settings_manager.set('last_player_names', current_names)

        self.was_started = True
        self.destroy()

    def _on_cancel(self):
        """Entspricht der alten 'goback'-Methode."""
        self.was_started = False
        self.destroy()

    def set_game(self, event=None):
        self.game = self.game_select.get()
        config = GAME_CONFIG.get(self.game, {})

        for frame in self.game_option_frames.values():
            frame.pack_forget()

        if "frame" in config:
            frame_key = config["frame"]
            self.game_option_frames[frame_key].pack(fill="x", padx=10, pady=5)

        if "defaults" in config:
            for option, value in config["defaults"].items():
                if option == "opt_in": self.opt_in_select.set(value); self.opt_in = value
                elif option == "opt_out":
                    if self.game == "Elimination": self.el_opt_out_select.set(value)
                    else: self.opt_out_select.set(value)
                    self.opt_out = value
                elif option == "opt_atc": self.opt_atc_select.set(value); self.opt_atc = value
                elif option == "count_to": self.count_to_select.set(value); self.count_to = value
                elif option == "lifes": self.lifes_select.set(value); self.lifes = value
                elif option == "rounds": self.rounds_select.set(value); self.shanghai_rounds = value

        min_players = config.get("min_players", 1)
        if int(self.player_select.get()) < min_players:
            self.player_select.set(str(min_players))
            self.set_anzahl_spieler()

    def set_opt_in(self, event=None): self.opt_in = self.opt_in_select.get()
    def set_opt_out(self, event=None): self.opt_out = self.opt_out_select.get()
    def set_opt_atc(self, event=None): self.opt_atc = self.opt_atc_select.get()
    def set_count_to(self, event=None): self.count_to = self.count_to_select.get()
    def set_elimination_opt_out(self, event=None): self.opt_out = self.el_opt_out_select.get()
    def set_lifes(self, event=None): self.lifes = self.lifes_select.get()
    def set_rounds(self, event=None): self.shanghai_rounds = self.rounds_select.get()

    def set_anzahl_spieler(self, event=None):
        self.anzahl_spieler = int(self.player_select.get())
        for i in range(self.max_players):
            if i < self.anzahl_spieler:
                self.player_name_entries[i].config(state="normal")
            else:
                self.player_name_entries[i].config(state="disabled")
                self.player_name_entries[i].delete(0, tk.END)
                self.player_name_entries[i].insert(0, f"Sp{i+1}")

    def _create_players_frame(self, parent):
        tk.Label(parent, text="Spieler", font=("Arial", 12), fg="blue").pack(padx=10, anchor="nw")
        players_frame = tk.Frame(parent, bd=2, relief="groove")
        players_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(players_frame, text="Anzahl", font=("Arial", 12), fg="purple").pack(pady=5)
        plr_values = [str(i) for i in range(1, self.max_players + 1)]
        self.player_select = ttk.Combobox(players_frame, values=plr_values, state="readonly")
        self.player_select.pack()
        self.player_select.bind("<<ComboboxSelected>>", self.set_anzahl_spieler)
        self.player_select.current(0)

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

    def _create_option_widget(self, parent, label_text, values, callback, default_index=0):
        """Hilfsmethode zur Erstellung eines Labels und einer Combobox für eine Spieloption."""
        tk.Label(parent, text=label_text, font=("Arial", 11), fg="green").pack(pady=2)
        widget = ttk.Combobox(parent, values=values, state="readonly")
        widget.pack()
        widget.bind("<<ComboboxSelected>>", callback)
        widget.current(default_index)
        return widget

    def _create_x01_options_frame(self, parent):
        x01_frame = tk.Frame(parent)
        self.game_option_frames["x01_options"] = x01_frame
        values = ["Single", "Double", "Masters"]
        self.opt_in_select = self._create_option_widget(x01_frame, "Opt In", values, self.set_opt_in)
        self.opt_out_select = self._create_option_widget(x01_frame, "Opt Out", values, self.set_opt_out)

    def _create_atc_options_frame(self, parent):
        atc_frame = tk.Frame(parent)
        self.game_option_frames["atc_options"] = atc_frame
        atc_values = ["Single", "Double", "Triple"]
        self.opt_atc_select = self._create_option_widget(atc_frame, "Around The Clock Variante", atc_values, self.set_opt_atc)

    def _create_elimination_options_frame(self, parent):
        elimination_frame = tk.Frame(parent)
        self.game_option_frames["elimination_options"] = elimination_frame
        count_to_values = ["301", "501"]
        self.count_to_select = self._create_option_widget(elimination_frame, "Count To", count_to_values, self.set_count_to)
        el_out_values = ["Single", "Double"]
        self.el_opt_out_select = self._create_option_widget(elimination_frame, "Opt Out", el_out_values, self.set_elimination_opt_out)

    def _create_killer_options_frame(self, parent):
        killer_frame = tk.Frame(parent)
        self.game_option_frames["killer_options"] = killer_frame
        life_values = ["3", "5", "7"]
        self.lifes_select = self._create_option_widget(killer_frame, "Anzahl Leben", life_values, self.set_lifes)

    def _create_shanghai_options_frame(self, parent):
        shanghai_frame = tk.Frame(parent)
        self.game_option_frames["shanghai_options"] = shanghai_frame
        rounds_values = ["7", "10", "20"]
        self.rounds_select = self._create_option_widget(shanghai_frame, "Anzahl Runden", rounds_values, self.set_rounds)

    def _create_dynamic_option_frames(self, parent):
        self._create_x01_options_frame(parent)
        self._create_atc_options_frame(parent)
        self._create_elimination_options_frame(parent)
        self._create_killer_options_frame(parent)
        self._create_shanghai_options_frame(parent)

    def _create_game_selection_frame(self, parent):
        tk.Label(parent, text="Varianten", font=("Arial", 12), fg = "blue").pack(padx=10, pady=(10, 0), anchor="nw")
        game_selection_frame = tk.Frame(parent, bd=2, relief="groove")
        game_selection_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(game_selection_frame, text="Spiel", font=("Arial", 12), fg="purple").pack()
        self.game_select = ttk.Combobox(game_selection_frame, values=list(GAME_CONFIG.keys()), state="readonly")
        self.game_select.pack()
        self.game_select.bind("<<ComboboxSelected>>", self.set_game)
        self.game_select.current(0)
        self._create_dynamic_option_frames(game_selection_frame)

    def _create_start_button_frame(self, parent):
        start_button_frame = tk.Frame(parent)
        start_button_frame.pack(side="bottom", fill="x", pady=10)
        btn = ttk.Button(start_button_frame, text="Spiel starten", style="Accent.TButton", command=self._on_start)
        btn.pack()
        btn.bind("<Return>", lambda event: self._on_start())
        btn.focus_set()