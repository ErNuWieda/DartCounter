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

import tkinter as tk 
from tkinter import ttk, messagebox
from .profile_manager_dialog import ProfileManagerDialog
from .settings_manager import get_app_data_dir, get_application_root_dir
from .json_io_handler import JsonIOHandler
import logging
import shutil

logger = logging.getLogger(__name__)

def _load_game_config():
    """
    Lädt die Spielkonfigurationen. Sucht zuerst im Benutzerverzeichnis.
    Wenn dort keine Konfiguration existiert, wird die Standardkonfiguration
    aus dem Anwendungsverzeichnis dorthin kopiert.
    """
    user_config_path = get_app_data_dir() / "game_config.json"
    default_config_path = get_application_root_dir() / "game_config.json"

    # Schritt 1: Sicherstellen, dass eine Konfigurationsdatei im Benutzerverzeichnis existiert.
    if not user_config_path.exists():
        if default_config_path.exists():
            try:
                # Kopiere die Standardkonfiguration in das Benutzerverzeichnis
                shutil.copy(default_config_path, user_config_path)
                logger.info(f"Keine 'game_config.json' im Benutzerverzeichnis gefunden. Standardkonfiguration wurde kopiert nach: {user_config_path}")
            except (IOError, shutil.Error) as e:
                logger.error(f"Konnte die Standard-Spielkonfiguration nicht in das Benutzerverzeichnis kopieren: {e}", exc_info=True)
                # Als Fallback versuchen wir, direkt die Standardkonfiguration zu laden
                config = JsonIOHandler.read_json(default_config_path)
                return config if config else {}
        else:
            # Weder Benutzer- noch Standardkonfiguration gefunden
            logger.warning("Keine 'game_config.json' gefunden. Spieloptionen sind nicht verfügbar.")
            return {}
    
    # Schritt 2: Lade die Konfiguration aus dem Benutzerverzeichnis.
    config = JsonIOHandler.read_json(user_config_path)
    return config if config else {}

# Die Spielkonfiguration wird nur einmal beim Import des Moduls geladen.
GAME_CONFIG = _load_game_config()

# Neue, UI-fokussierte Klasse für den Einstellungsdialog.
# Diese Klasse ist noch nicht integriert und dient als erster Schritt des Refactorings.
class GameSettingsDialog(tk.Toplevel):
    """Ein modaler Dialog zur Konfiguration und zum Start eines neuen Spiels."""
    def __init__(self, parent, settings_manager=None, profile_manager=None):
        super().__init__(parent)
        self.parent = parent
        self.settings_manager = settings_manager
        self.profile_manager = profile_manager

        # --- Zustandvariablen zur Speicherung der ausgewählten Einstellungen ---
        self.game_var = tk.StringVar(value="301")
        self.count_to_var = tk.StringVar(value="301")
        self.opt_in_var = tk.StringVar(value="Single")
        self.opt_out_var = tk.StringVar(value="Single")
        self.opt_atc_var = tk.StringVar(value="Single")
        self.lifes_var = tk.StringVar(value="3")
        self.legs_to_win_var = tk.StringVar(value="1") # Neu für Legs
        self.sets_to_win_var = tk.StringVar(value="1") # Neu für Sets
        self.rounds_var = tk.StringVar(value="7")
        self.player_count_var = tk.StringVar(value="1")

        # --- Data-Driven UI: Map von Optionsnamen zu Tkinter-Variablen ---
        # Ersetzt die if/elif-Kette in _on_game_selected.
        self.option_vars = {
            "opt_in": self.opt_in_var,
            "opt_out": self.opt_out_var,
            "opt_atc": self.opt_atc_var,
            "count_to": self.count_to_var,
            "lifes": self.lifes_var,
            "rounds": self.rounds_var,
            "legs_to_win": self.legs_to_win_var,
            "sets_to_win": self.sets_to_win_var,
        }
        # --- Konfiguration für die dynamisch erstellten Options-Frames ---
        # Zentralisiert die UI-Definition für Spieloptionen, um die Wartbarkeit zu verbessern.
        self.OPTION_FRAME_CONFIG = {
            "x01_options": [
                {"label": "Opt In", "values": ["Single", "Double", "Masters"], "variable": self.opt_in_var},
                {"label": "Opt Out", "values": ["Single", "Double", "Masters"], "variable": self.opt_out_var},
                {"label": "Legs pro Satz", "values": ["1", "3", "5"], "variable": self.legs_to_win_var},
                {"label": "Sätze pro Match", "values": ["1", "3", "5"], "variable": self.sets_to_win_var},
            ],
            "atc_options": [
                {"label": "Around The Clock Variante", "values": ["Single", "Double", "Triple"], "variable": self.opt_atc_var},
            ],
            "elimination_options": [
                {"label": "Count To", "values": ["301", "501"], "variable": self.count_to_var},
                {"label": "Opt Out", "values": ["Single", "Double"], "variable": self.opt_out_var},
            ],
            "killer_options": [
                {"label": "Anzahl Leben", "values": ["3", "5", "7"], "variable": self.lifes_var},
            ],
            "shanghai_options": [
                {"label": "Anzahl Runden", "values": ["7", "10", "20"], "variable": self.rounds_var},
            ],
        }

        self.max_players = 4
        self.result = None

        # --- UI Widgets ---
        self.game_select = None
        self.player_select = None
        self.player_name_entries = []
        self.game_option_frames = {}
        
        # --- Ergebnis-Flags ---
        self.was_started = False

        # --- Dialog aufbauen ---
        self.title("Spieleinstellungen")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())

        # --- Grid Layout Setup ---
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)

        # UI-Elemente erstellen
        self._create_players_frame(main_frame, row=0)
        self._create_game_selection_frame(main_frame, row=1)
        self._create_start_button_frame(main_frame, row=2)

        # Initialen Zustand der Optionen setzen
        self._update_available_profiles()
        self._on_game_selected()

    def _on_start(self):
        """Entspricht der alten 'run'-Methode."""
        num_players = int(self.player_count_var.get())
        player_names = [entry.get().strip() for entry in self.player_name_entries[:num_players]]

        # --- Validierung (analog zum TournamentSettingsDialog) ---
        if any(not name for name in player_names):
            messagebox.showerror("Fehler", "Alle Spielernamen müssen ausgefüllt sein.", parent=self)
            return

        if len(set(player_names)) != len(player_names):
            messagebox.showerror("Fehler", "Spielernamen müssen eindeutig sein.", parent=self)
            return

        if self.settings_manager:
            # Speichere die Namen aus allen Eingabefeldern, um die Reihenfolge für den nächsten Start beizubehalten.
            last_names_to_save = [entry.get() for entry in self.player_name_entries]
            self.settings_manager.set('last_player_names', last_names_to_save)

        # Sammle alle Einstellungen dynamisch aus den Variablen in einem Dictionary
        self.result = {
            "game": self.game_var.get(),
            "players": player_names
        }
        for key, var in self.option_vars.items():
            self.result[key] = var.get()

        self.was_started = True
        self.destroy()

    def _on_cancel(self):
        """Entspricht der alten 'goback'-Methode."""
        self.was_started = False
        self.destroy()

    def _on_game_selected(self, event=None):
        """Wird aufgerufen, wenn ein Spiel im Haupt-Combobox ausgewählt wird."""
        selected_game = self.game_var.get()
        config = GAME_CONFIG.get(selected_game, {})

        for frame in self.game_option_frames.values():
            frame.grid_remove()

        if "frame" in config:
            frame_key = config["frame"]
            if frame_key in self.game_option_frames:
                self.game_option_frames[frame_key].grid()

        if "defaults" in config:
            for option, value in config["defaults"].items():
                if var := self.option_vars.get(option):
                    var.set(value)

        min_players = config.get("min_players", 1)
        if int(self.player_count_var.get()) < min_players:
            self.player_count_var.set(str(min_players))
            self._on_player_count_changed()

    def _on_player_count_changed(self, event=None):
        num_players = int(self.player_count_var.get())
        for i in range(self.max_players):
            if i < num_players:
                self.player_name_entries[i].config(state="normal")
            else:
                self.player_name_entries[i].config(state="disabled")
                self.player_name_entries[i].delete(0, tk.END)
        self._update_available_profiles()

    def _create_players_frame(self, parent, row):
        players_frame = ttk.LabelFrame(parent, text="Spieler", padding=10)
        players_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        players_frame.columnconfigure(1, weight=1) # Make comboboxes expand

        # Row 0: Player count
        ttk.Label(players_frame, text="Anzahl:").grid(row=0, column=0, sticky="w")
        plr_values = [str(i) for i in range(1, self.max_players + 1)]
        self.player_select = ttk.Combobox(players_frame, textvariable=self.player_count_var, values=plr_values, state="readonly", width=5)
        self.player_select.grid(row=0, column=1, sticky="w")
        self.player_select.bind("<<ComboboxSelected>>", self._on_player_count_changed)
        # Der Wert wird bereits durch die Variable gesetzt, kein .current(0) nötig.

        # --- Profil- und Namens-Setup ---
        # Row 1 to 4: Player name entries
        self.player_name_entries = [None] * self.max_players
        
        profile_names = []
        if self.profile_manager:
            profiles = self.profile_manager.get_profiles()
            profile_names = sorted([p.name for p in profiles])

        last_names = self.settings_manager.get('last_player_names', [f"Sp{i+1}" for i in range(self.max_players)]) if self.settings_manager else [f"Sp{i+1}" for i in range(self.max_players)]

        for i in range(self.max_players):
            ttk.Label(players_frame, text=f"Spieler {i+1}:").grid(row=i+1, column=0, sticky="w", pady=2)
            combo = ttk.Combobox(players_frame, font=("Arial", 10), values=profile_names)
            combo.grid(row=i+1, column=1, sticky="ew", pady=2, padx=5)
            combo.insert(0, last_names[i])
            combo.bind("<<ComboboxSelected>>", self._update_available_profiles)
            combo.bind("<FocusOut>", self._update_available_profiles)
            self.player_name_entries[i] = combo # type: ignore
            if i >= int(self.player_count_var.get()):
                self.player_name_entries[i].config(state="disabled")

        # Button zur direkten Verwaltung der Profile hinzufügen
        manage_profiles_button = ttk.Button(players_frame, text="Profile verwalten...", command=self._open_profile_manager)
        manage_profiles_button.grid(row=self.max_players + 1, column=0, columnspan=2, pady=(10, 5))

    def _update_available_profiles(self, event=None):
        """
        Aktualisiert die Liste der verfügbaren Profile in allen Comboboxen,
        um bereits ausgewählte Profile für andere Spieler auszublenden.
        """
        if not self.profile_manager:
            return

        all_profile_names = sorted([p.name for p in self.profile_manager.get_profiles()])
        
        # Korrigierte Logik: Sammle ALLE ausgewählten Namen (Profile & Gäste), um Duplikate zu verhindern.
        selected_names = {
            entry.get() for entry in self.player_name_entries if entry and entry.cget('state') != 'disabled' and entry.get()
        }

        # Aktualisiere die `values` für jede aktive Combobox
        for entry in self.player_name_entries:
            if entry and entry.cget('state') != 'disabled': # Die Prüfung ist hier korrekt
                current_value = entry.get()
                available = [name for name in all_profile_names if name not in selected_names or name == current_value]
                entry['values'] = available

    def _open_profile_manager(self):
        """
        Öffnet den Dialog zur Verwaltung von Spielerprofilen und aktualisiert
        anschließend die Comboboxen in diesem Dialog.
        """
        if not self.profile_manager:
            return

        dialog = ProfileManagerDialog(self, self.profile_manager)
        self.wait_window(dialog)
        self._update_available_profiles()

    def _create_option_widget(self, parent, row, label_text, values, variable):
        """Hilfsmethode zur Erstellung eines Labels und einer Combobox für eine Spieloption."""
        ttk.Label(parent, text=f"{label_text}:").grid(row=row, column=0, sticky="w", pady=2)
        widget = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly")
        widget.grid(row=row, column=1, sticky="ew", padx=5, pady=2)

    def _create_dynamic_option_frames(self, parent, start_row):
        """
        Erstellt dynamisch alle Options-Frames basierend auf der zentralen Konfiguration.
        Dieser datengesteuerte Ansatz ersetzt mehrere repetitive Methoden.
        """
        for frame_key, widgets_config in self.OPTION_FRAME_CONFIG.items():
            # The frame itself is just a container, it will be placed by _on_game_selected
            frame = ttk.Frame(parent)
            frame.grid(row=start_row, column=0, columnspan=2, sticky="ew", pady=5)
            frame.columnconfigure(1, weight=1)
            self.game_option_frames[frame_key] = frame
            
            for i, widget_config in enumerate(widgets_config):
                self._create_option_widget(
                    parent=frame,
                    row=i, # row within this sub-frame
                    label_text=widget_config["label"],
                    values=widget_config["values"],
                    variable=widget_config["variable"]
                )
            # Hide the frame initially
            frame.grid_remove()

    def _create_game_selection_frame(self, parent, row):
        self.game_selection_frame = ttk.LabelFrame(parent, text="Varianten", padding=10)
        self.game_selection_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        self.game_selection_frame.columnconfigure(1, weight=1)

        ttk.Label(self.game_selection_frame, text="Spiel:").grid(row=0, column=0, sticky="w", pady=5)
        self.game_select = ttk.Combobox(self.game_selection_frame, textvariable=self.game_var, values=list(GAME_CONFIG.keys()), state="readonly")
        self.game_select.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        self.game_select.bind("<<ComboboxSelected>>", self._on_game_selected)
        self._create_dynamic_option_frames(self.game_selection_frame, start_row=1)

    def _create_start_button_frame(self, parent, row):
        start_button_frame = ttk.Frame(parent)
        start_button_frame.grid(row=row, column=0, pady=20)
        btn = ttk.Button(start_button_frame, text="Spiel starten", style="Accent.TButton", command=self._on_start)
        btn.pack() # Using pack inside this sub-frame is fine
        btn.bind("<Return>", lambda event: self._on_start())
        btn.focus_set()
