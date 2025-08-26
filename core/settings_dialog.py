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
import sv_ttk

class AppSettingsDialog(tk.Toplevel):
    """
    Ein eigenständiger Dialog für die globalen Anwendungseinstellungen.
    Kapselt die UI-Logik für Sound- und Theme-Einstellungen.
    """
    def __init__(self, parent, settings_manager, sound_manager):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.sound_manager = sound_manager

        self.title("Globale Einstellungen")
        self.geometry("320x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_sound_settings(self)
        self._create_theme_settings(self)
        ttk.Button(self, text="Schließen", command=self.destroy).pack(side="bottom", pady=15)

    def _create_sound_settings(self, parent):
        self.sound_enabled_var = tk.BooleanVar(value=self.sound_manager.sounds_enabled)
        self.sound_checkbutton = ttk.Checkbutton(
            parent,
            text="Soundeffekte aktivieren",
            variable=self.sound_enabled_var,
            command=self._on_sound_toggle
        )
        self.sound_checkbutton.pack(pady=10, padx=20, anchor="w")

    def _on_sound_toggle(self):
        """Callback-Methode, die aufgerufen wird, wenn der Sound-Checkbutton umgeschaltet wird."""
        self.sound_manager.toggle_sounds(self.sound_enabled_var.get())

    def _create_theme_settings(self, parent):
        theme_frame = ttk.LabelFrame(parent, text="Design")
        theme_frame.pack(fill="x", padx=15, pady=10)

        self.theme_combo = ttk.Combobox(theme_frame, values=["Light", "Dark"], state="readonly")
        self.theme_combo.pack(pady=10, padx=10, fill='x')
        current_theme = self.settings_manager.get('theme', 'light')
        self.theme_combo.set(current_theme.capitalize())

        def _set_theme_and_save(event):
            selected_theme = self.theme_combo.get().lower()
            self.settings_manager.set('theme', selected_theme)
            sv_ttk.set_theme(selected_theme)

        self.theme_combo.bind("<<ComboboxSelected>>", _set_theme_and_save)