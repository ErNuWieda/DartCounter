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
        self.geometry("320x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_sound_settings(self)
        self._create_theme_settings(self)
        self._create_ai_settings(self)
        ttk.Button(self, text="Schließen", command=self.destroy).pack(side="bottom", pady=15)

    def _create_sound_settings(self, parent):
        sound_frame = ttk.LabelFrame(parent, text="Sound")
        sound_frame.pack(fill="x", padx=15, pady=10)

        self.sound_enabled_var = tk.BooleanVar(value=self.sound_manager.sounds_enabled)
        self.sound_checkbutton = ttk.Checkbutton(
            sound_frame,
            text="Soundeffekte aktivieren",
            variable=self.sound_enabled_var,
            command=self._on_sound_toggle,
        )
        self.sound_checkbutton.pack(pady=5, padx=10, anchor="w")

        # --- Volume Control ---
        volume_label_frame = ttk.Frame(sound_frame)
        volume_label_frame.pack(fill="x", padx=10, pady=(5, 0))
        ttk.Label(volume_label_frame, text="Lautstärke:").pack(side="left")
        self.volume_value_label = ttk.Label(volume_label_frame, text="")
        self.volume_value_label.pack(side="right")

        self.sound_volume_var = tk.DoubleVar(value=self.settings_manager.get("sound_volume", 0.5))
        self.volume_value_label.config(text=f"{int(self.sound_volume_var.get() * 100)} %")

        volume_slider = ttk.Scale(
            sound_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.sound_volume_var,
            command=self._on_volume_change,
        )
        volume_slider.pack(fill="x", padx=10, pady=(0, 10))

    def _on_sound_toggle(self):
        """Callback-Methode, die aufgerufen wird, wenn der Sound-Checkbutton umgeschaltet wird."""
        self.sound_manager.toggle_sounds(self.sound_enabled_var.get())

    def _create_theme_settings(self, parent):
        theme_frame = ttk.LabelFrame(parent, text="Design")
        theme_frame.pack(fill="x", padx=15, pady=10)

        self.theme_combo = ttk.Combobox(theme_frame, values=["Light", "Dark"], state="readonly")
        self.theme_combo.pack(pady=10, padx=10, fill="x")
        current_theme = self.settings_manager.get("theme", "light")
        self.theme_combo.set(current_theme.capitalize())

        def _set_theme_and_save(event):
            selected_theme = self.theme_combo.get().lower()
            self.settings_manager.set("theme", selected_theme)
            sv_ttk.set_theme(selected_theme)

        self.theme_combo.bind("<<ComboboxSelected>>", _set_theme_and_save)

    def _on_volume_change(self, value):
        """Wird aufgerufen, wenn der Lautstärke-Slider bewegt wird."""
        float_value = float(value)
        self.volume_value_label.config(text=f"{int(float_value * 100)} %")
        self.settings_manager.set("sound_volume", float_value)
        if self.sound_manager:
            self.sound_manager.set_global_volume(float_value)

    def _create_ai_settings(self, parent):
        """Erstellt die UI-Elemente für die KI-Einstellungen."""
        ai_frame = ttk.LabelFrame(parent, text="KI-Einstellungen")
        ai_frame.pack(fill="x", padx=15, pady=10)

        # Label für die Anzeige des aktuellen Werts
        delay_label_frame = ttk.Frame(ai_frame)
        delay_label_frame.pack(fill="x", padx=10, pady=(5, 0))
        ttk.Label(delay_label_frame, text="Wurf-Verzögerung (ms):").pack(side="left")
        self.delay_value_label = ttk.Label(delay_label_frame, text="")
        self.delay_value_label.pack(side="right")

        # Slider zur Einstellung der Verzögerung
        self.ai_delay_var = tk.IntVar(value=self.settings_manager.get("ai_throw_delay", 1000))
        self.delay_value_label.config(text=f"{self.ai_delay_var.get()} ms")

        delay_slider = ttk.Scale(
            ai_frame,
            from_=250,
            to=2000,
            orient=tk.HORIZONTAL,
            variable=self.ai_delay_var,
            command=self._on_delay_change,
        )
        delay_slider.pack(fill="x", padx=10, pady=(0, 10))

    def _on_delay_change(self, value):
        """Wird aufgerufen, wenn der Slider bewegt wird, um den Wert zu speichern."""
        int_value = int(float(value))
        self.delay_value_label.config(text=f"{int_value} ms")
        self.settings_manager.set("ai_throw_delay", int_value)
