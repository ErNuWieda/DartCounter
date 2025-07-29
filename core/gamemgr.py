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
from tkinter import ttk
from .profile_manager_dialog import ProfileManagerDialog
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
    def __init__(self, sound_manager=None, settings_manager=None, profile_manager=None):
        self.sound_manager = sound_manager
        self.settings_manager = settings_manager
        self.profile_manager = profile_manager

        # Attribute, die die finalen Spieleinstellungen speichern
        self.game = "301"
        self.count_to = "301"
        self.opt_in = "Single"
        self.opt_out = "Single"
        self.opt_atc = "Single"
        self.lifes = "3"
        self.rounds = "7"
        self.players = []
        self.result = None # Wird vom Dialog gefüllt

    def configure_game(self, parent_window):
        """
        Öffnet den Einstellungsdialog, wartet auf Benutzereingaben und
        übernimmt die Einstellungen, wenn das Spiel gestartet wird.

        Args:
            parent_window (tk.Toplevel or tk.Tk): Das übergeordnete Fenster.

        Returns:
            bool: True, wenn der Benutzer das Spiel gestartet hat, sonst False.
        """
        dialog = GameSettingsDialog(parent_window, self.settings_manager, self.profile_manager)
        parent_window.wait_window(dialog) # Blockiert, bis der Dialog geschlossen wird

        if dialog.was_started and dialog.result:
            # Aktualisiert alle Attribute des Managers mit den Werten aus dem Ergebnis-Dictionary.
            # Dies ist flexibler und wartbarer als das manuelle Zuweisen jedes Attributs.
            vars(self).update(dialog.result)
            return True
        return False

# Neue, UI-fokussierte Klasse für den Einstellungsdialog.
# Diese Klasse ist noch nicht integriert und dient als erster Schritt des Refactorings.
class GameSettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings_manager=None, profile_manager=None):
        super().__init__(parent)
        self.parent = parent
        self.settings_manager = settings_manager
        self.profile_manager = profile_manager

        # --- Zustandvariablen zur Speicherung der ausgewählten Einstellungen ---
        self.game = "301"
        self.count_to = "301"
        self.opt_in = "Single"
        self.opt_out = "Single"
        self.opt_atc = "Single"
        self.anzahl_spieler = "1"
        self.lifes = "3"
        self.rounds = "7"
        self.max_players = 4
        self.was_started = False
        self.result = None
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
        self.geometry("320x675")
        self.resizable(False, True)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())

        # UI-Elemente erstellen
        self._create_players_frame(self)
        self._create_game_selection_frame(self)
        self._create_start_button_frame(self)

        # Initialen Zustand der Optionen setzen
        self._update_available_profiles()
        self.set_game()

    def _on_start(self):
        """Entspricht der alten 'run'-Methode."""
        num_players = int(self.player_select.get())
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

        # Sammle alle Einstellungen in einem Dictionary
        self.result = {
            "game": self.game, "count_to": self.count_to, "opt_in": self.opt_in,
            "opt_out": self.opt_out, "opt_atc": self.opt_atc, "lifes": self.lifes,
            "rounds": self.rounds, "players": player_names
        }

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
                elif option == "rounds": self.rounds_select.set(value); self.rounds = value

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
    def set_rounds(self, event=None): self.rounds = self.rounds_select.get()

    def set_anzahl_spieler(self, event=None):
        self.anzahl_spieler = int(self.player_select.get())
        for i in range(self.max_players):
            if i < self.anzahl_spieler:
                self.player_name_entries[i].config(state="normal")
            else:
                self.player_name_entries[i].config(state="disabled")
                self.player_name_entries[i].delete(0, tk.END)
        self._update_available_profiles()

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

        # --- Profil- und Namens-Setup ---
        tk.Label(players_frame, text="Namen", font=("Arial", 12), fg="purple").pack(pady=5)
        self.player_name_entries = [None] * self.max_players
        
        profile_names = []
        if self.profile_manager:
            profiles = self.profile_manager.get_profiles()
            profile_names = sorted([p.name for p in profiles])

        last_names = self.settings_manager.get('last_player_names', [f"Sp{i+1}" for i in range(self.max_players)]) if self.settings_manager else [f"Sp{i+1}" for i in range(self.max_players)]

        for i in range(self.max_players):
            tk.Label(players_frame, text=f"Spieler {i+1}", font=("Arial", 11), fg="green").pack()
            combo = ttk.Combobox(players_frame, font=("Arial", 10), values=profile_names)
            combo.pack(pady=2)
            combo.insert(0, last_names[i])
            combo.bind("<<ComboboxSelected>>", self._update_available_profiles)
            combo.bind("<FocusOut>", self._update_available_profiles)
            self.player_name_entries[i] = combo
            if i >= int(self.player_select.get()):
                self.player_name_entries[i].config(state="disabled")

        # Button zur direkten Verwaltung der Profile hinzufügen
        manage_profiles_button = ttk.Button(players_frame, text="Profile verwalten...", command=self._open_profile_manager)
        manage_profiles_button.pack(pady=(10, 5))

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