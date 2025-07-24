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
        self.geometry("320x180")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_sound_settings(self)
        self._create_theme_settings(self)
        ttk.Button(self, text="Schließen", command=self.destroy).pack(side="bottom", pady=15)

    def _create_sound_settings(self, parent):
        sound_enabled_var = tk.BooleanVar(value=self.sound_manager.sounds_enabled)
        sound_check = ttk.Checkbutton(parent, text="Soundeffekte aktivieren", variable=sound_enabled_var, command=lambda: self.sound_manager.toggle_sounds(sound_enabled_var.get()))
        sound_check.pack(pady=10, padx=20, anchor="w")

    def _create_theme_settings(self, parent):
        theme_frame = ttk.LabelFrame(parent, text="Design")
        theme_frame.pack(fill="x", padx=15, pady=10)

        theme_select = ttk.Combobox(theme_frame, values=["Light", "Dark"], state="readonly")
        theme_select.pack(pady=10, padx=10, fill='x')
        current_theme = self.settings_manager.get('theme', 'light')
        theme_select.set(current_theme.capitalize())

        def _set_theme_and_save(event):
            selected_theme = theme_select.get().lower()
            self.settings_manager.set('theme', selected_theme)
            sv_ttk.set_theme(selected_theme)

        theme_select.bind("<<ComboboxSelected>>", _set_theme_and_save)