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

class TournamentSettingsDialog(tk.Toplevel):
    """
    Ein Dialogfenster zur Konfiguration der Einstellungen für ein neues Turnier.
    Ermöglicht die Auswahl von Spielern aus Profilen, analog zum GameSettingsDialog.
    """
    def __init__(self, parent, profile_manager=None, settings_manager=None):
        super().__init__(parent)
        self.transient(parent)
        self.title("Neues Turnier erstellen")
        self.profile_manager = profile_manager
        self.settings_manager = settings_manager

        # --- Zustandvariablen ---
        self.player_count_var = tk.StringVar(value="4")
        self.game_mode_var = tk.StringVar(value="501")
        self.player_name_entries = []
        self.cancelled = True
        self.player_names = []
        self.game_mode = "501" # Wird bei Erfolg gefüllt

        self._setup_widgets()
        self._load_last_players()

        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.wait_window(self)

    def _setup_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Spieler-Auswahl ---
        players_frame = ttk.LabelFrame(main_frame, text="Spieler", padding=10)
        players_frame.pack(fill="x", padx=10, pady=5)

        count_frame = ttk.Frame(players_frame)
        count_frame.pack(fill="x")
        ttk.Label(count_frame, text="Anzahl Spieler:").pack(side="left", padx=(0, 10))
        player_count_combo = ttk.Combobox(
            count_frame, textvariable=self.player_count_var,
            values=[str(i) for i in range(2, 9)], state="readonly", width=5
        )
        player_count_combo.pack(side="left")
        player_count_combo.bind("<<ComboboxSelected>>", self._update_player_entries)

        self.entries_frame = ttk.Frame(players_frame)
        self.entries_frame.pack(pady=5)
        self._create_player_entries()

        manage_profiles_button = ttk.Button(players_frame, text="Profile verwalten...", command=self._open_profile_manager)
        manage_profiles_button.pack(pady=(10, 5))

        # Spielmodus-Auswahl
        mode_frame = ttk.LabelFrame(main_frame, text="Spielmodus", padding=10)
        mode_frame.pack(fill="x", padx=10, pady=5)
        game_mode_combo = ttk.Combobox(mode_frame, textvariable=self.game_mode_var, values=["301", "501", "701"], state="readonly")
        game_mode_combo.pack()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Turnier starten", style="Accent.TButton", command=self._on_start).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Abbrechen", command=self._on_cancel).pack(side=tk.LEFT, padx=10)

    def _create_player_entries(self):
        """Erstellt die Comboboxen für die Spielerauswahl."""
        for widget in self.entries_frame.winfo_children():
            widget.destroy()
        self.player_name_entries.clear()

        count = int(self.player_count_var.get())
        for i in range(count):
            combo = ttk.Combobox(self.entries_frame, font=("Arial", 10))
            combo.pack(pady=2)
            combo.bind("<<ComboboxSelected>>", self._update_available_profiles)
            self.player_name_entries.append(combo)

    def _update_player_entries(self, event=None):
        self._create_player_entries()
        self._load_last_players()

    def _update_available_profiles(self, event=None):
        if not self.profile_manager: return

        all_profile_names = sorted([p.name for p in self.profile_manager.get_profiles()])
        selected_names = {entry.get() for entry in self.player_name_entries if entry.get()}

        for entry in self.player_name_entries:
            current_value = entry.get()
            available = [name for name in all_profile_names if name not in selected_names or name == current_value]
            entry['values'] = available

    def _load_last_players(self):
        if not self.settings_manager or not self.profile_manager: return

        last_names = self.settings_manager.get('last_tournament_players', [])

        self._update_available_profiles() # Initial verfügbare Profile setzen

        for i, entry in enumerate(self.player_name_entries):
            # Setze den Namen, egal ob es ein Profil oder ein Gast ist.
            if i < len(last_names):
                entry.set(last_names[i])
        
        self._update_available_profiles() # Auswahl aktualisieren, um Duplikate zu entfernen

    def _open_profile_manager(self):
        if not self.profile_manager: return
        dialog = ProfileManagerDialog(self, self.profile_manager)
        self.wait_window(dialog)
        self._update_available_profiles()

    def _on_start(self):
        self.player_names = [entry.get().strip() for entry in self.player_name_entries]
        if any(not name for name in self.player_names):
            messagebox.showerror("Fehler", "Alle Spielernamen müssen ausgefüllt sein.", parent=self)
            return
        if len(set(self.player_names)) != len(self.player_names):
            messagebox.showerror("Fehler", "Spielernamen müssen eindeutig sein.", parent=self)
            return

        if self.settings_manager:
            self.settings_manager.set('last_tournament_players', self.player_names)

        self.game_mode = self.game_mode_var.get()
        self.cancelled = False
        self.destroy()

    def _on_cancel(self):
        self.cancelled = True
        self.destroy()