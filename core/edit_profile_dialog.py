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
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from pathlib import Path
import os
from .player_profile import PlayerProfile
from .custom_colorchooser import CustomColorChooserDialog

class EditProfileDialog(tk.Toplevel):
    """
    Ein Dialog zum Erstellen oder Bearbeiten eines Spielerprofils.
    Trennt die UI-Erstellung klar von der Logik.
    """
    def __init__(self, parent, profile_manager, profile_to_edit: PlayerProfile | None = None):
        super().__init__(parent)
        self.transient(parent)
        self.profile_manager = profile_manager
        self.profile_to_edit = profile_to_edit

        # Initialwerte setzen
        self.new_avatar_path = profile_to_edit.avatar_path if profile_to_edit else None
        self.new_dart_color = profile_to_edit.dart_color if profile_to_edit else "#ff0000"
        # --- Neue Variablen für AI-Einstellungen ---
        self.is_ai_var = tk.BooleanVar()
        self.difficulty_var = tk.StringVar()

        self._configure_window()
        self._create_ui()

        self._populate_initial_data()

        # Erzwinge das Zeichnen des Fensters, bevor der Fokus "gegrabbt" wird.
        # Dies verhindert den "window not viewable" Fehler.
        self.update_idletasks()
        self.grab_set()

    def _configure_window(self):
        """Konfiguriert die grundlegenden Fenstereigenschaften."""
        is_editing = self.profile_to_edit is not None
        self.title("Profil bearbeiten" if is_editing else "Neues Profil erstellen")
        self.geometry("400x450")
        self.resizable(False, False)

    def _create_ui(self):
        """Erstellt und platziert alle UI-Widgets."""
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)

        self._create_name_widgets(main_frame)
        self._create_avatar_widgets(main_frame)
        self._create_color_widgets(main_frame)
        self._create_player_type_widgets(main_frame)
        self._create_ai_settings_widgets(main_frame)
        self._create_button_widgets(main_frame)

    def _populate_initial_data(self):
        """Füllt die UI-Widgets mit den Daten eines bestehenden Profils."""
        if self.profile_to_edit:
            self.name_entry.insert(0, self.profile_to_edit.name)
            self._load_avatar_preview(self.profile_to_edit.avatar_path)
            self.color_preview_label.config(bg=self.new_dart_color)
            self.is_ai_var.set(self.profile_to_edit.is_ai)
            self.difficulty_var.set(self.profile_to_edit.difficulty or 'Anfänger')
        else:
            # Standardwerte für ein neues Profil
            self.is_ai_var.set(False)
            self.difficulty_var.set('Anfänger')
        # Initialen Zustand der AI-Einstellungen setzen
        self._on_player_type_change()

    def _create_name_widgets(self, parent_frame):
        """Erstellt die Widgets für die Namenseingabe."""
        ttk.Label(parent_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(parent_frame)
        self.name_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=5)

    def _create_avatar_widgets(self, parent_frame):
        """Erstellt die Widgets für die Avatar-Auswahl."""
        ttk.Label(parent_frame, text="Avatar:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.avatar_preview_label = ttk.Label(parent_frame, text="Kein Avatar", relief="solid", width=15, anchor="center")
        self.avatar_preview_label.bind("<Button-1>", lambda e: self._select_avatar())
        self.avatar_preview_label.grid(row=1, column=1, pady=5, sticky="w")
        ttk.Button(parent_frame, text="Bild auswählen...", command=self._select_avatar).grid(row=1, column=2, pady=5, padx=5, sticky="w")

    def _create_color_widgets(self, parent_frame):
        """Erstellt die Widgets für die Farbauswahl."""
        ttk.Label(parent_frame, text="Dart-Farbe:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.color_preview_label = tk.Label(parent_frame, text="", bg=self.new_dart_color, width=4, relief="solid")
        self.color_preview_label.bind("<Button-1>", lambda e: self._select_dart_color())
        self.color_preview_label.grid(row=2, column=1, pady=5, sticky="w")
        ttk.Button(parent_frame, text="Farbe auswählen...", command=self._select_dart_color).grid(row=2, column=2, pady=5, padx=5, sticky="w")

    def _create_player_type_widgets(self, parent_frame):
        """Erstellt die Widgets zur Auswahl des Spielertyps (Mensch/KI)."""
        type_frame = ttk.LabelFrame(parent_frame, text="Spielertyp", padding=10)
        type_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=(15, 5))

        ttk.Radiobutton(
            type_frame, text="Mensch", variable=self.is_ai_var, value=False, command=self._on_player_type_change
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(
            type_frame, text="KI-Gegner", variable=self.is_ai_var, value=True, command=self._on_player_type_change
        ).pack(side=tk.LEFT, padx=10)

    def _create_ai_settings_widgets(self, parent_frame):
        """Erstellt die Widgets für die KI-spezifischen Einstellungen."""
        self.ai_settings_frame = ttk.Frame(parent_frame)
        # Die Platzierung erfolgt in _on_player_type_change
        self.ai_settings_frame.grid(row=4, column=0, columnspan=3, sticky=tk.EW, pady=5)
        self.ai_settings_frame.columnconfigure(1, weight=1)

        ttk.Label(self.ai_settings_frame, text="Schwierigkeit:").grid(row=0, column=0, sticky=tk.W)
        
        self.difficulty_combo = ttk.Combobox(
            self.ai_settings_frame,
            textvariable=self.difficulty_var,
            values=['Anfänger', 'Fortgeschritten', 'Amateur', 'Profi', 'Champion'],
            state="readonly"
        )
        self.difficulty_combo.grid(row=0, column=1, sticky=tk.EW, padx=5)

    def _create_button_widgets(self, parent_frame):
        """Erstellt die Speichern- und Abbrechen-Buttons."""
        button_frame = ttk.Frame(parent_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        ttk.Button(button_frame, text="Speichern", command=self._on_save, style="Accent.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Abbrechen", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _load_avatar_preview(self, path):
        """Lädt und zeigt eine Vorschau des ausgewählten Avatar-Bildes an."""
        if not path or not os.path.exists(path):
            self.avatar_preview_label.config(image=None, text="Kein Avatar")
            return
        try:
            img = Image.open(path)
            img.thumbnail((100, 100))
            self.avatar_photo = ImageTk.PhotoImage(img)
            self.avatar_preview_label.config(image=self.avatar_photo, text="")
        except (FileNotFoundError, Image.UnidentifiedImageError, IOError) as e:
            self.avatar_preview_label.config(image=None, text="Fehler")
            # print(f"Fehler beim Laden des Avatar-Vorschaubildes: {e}")

    def _select_avatar(self):
        """Öffnet einen Dateidialog zur Auswahl eines Avatar-Bildes."""
        # Finde das "Bilder"-Verzeichnis des Benutzers, um eine bessere UX zu bieten.
        try:
            initial_dir = Path.home() / "Pictures"
            if not initial_dir.is_dir():
                initial_dir = Path.home() # Fallback auf das Home-Verzeichnis
        except Exception:
            initial_dir = Path.home() # Sicherer Fallback

        filepath = filedialog.askopenfilename(
            parent=self, # Wichtig, damit der Dialog modal zum Elternelement ist
            title="Avatar-Bild auswählen",
            initialdir=str(initial_dir),
            filetypes=[("Bilddateien", "*.png *.jpg *.jpeg *.gif"), ("Alle Dateien", "*.*")]
        )
        if filepath:
            self.new_avatar_path = filepath
            self._load_avatar_preview(filepath)

    def _select_dart_color(self):
        """Öffnet den Farbauswahldialog und aktualisiert die Farbe."""
        # Ruft den neuen, benutzerdefinierten Dialog auf
        dialog = CustomColorChooserDialog(self, initial_color=self.new_dart_color)
        if dialog.result_color:
            self.new_dart_color = dialog.result_color
            self.color_preview_label.config(bg=self.new_dart_color)

    def _on_player_type_change(self):
        """Zeigt oder verbirgt die KI-Einstellungen basierend auf der Auswahl."""
        if self.is_ai_var.get():
            # Zeige die AI-Einstellungen
            self.ai_settings_frame.grid()
        else:
            # Verberge die AI-Einstellungen
            self.ai_settings_frame.grid_remove()

    def _on_save(self):
        """Validiert die Eingaben und speichert das Profil."""
        new_name = self.name_entry.get().strip()
        if not new_name:
            messagebox.showerror("Fehler", "Der Name darf nicht leer sein.", parent=self)
            return

        is_ai = self.is_ai_var.get()
        difficulty = self.difficulty_var.get() if is_ai else None

        success = False
        if self.profile_to_edit:
            # Profil bearbeiten
            success = self.profile_manager.update_profile(
                self.profile_to_edit.id, new_name, self.new_avatar_path, self.new_dart_color, is_ai=is_ai, difficulty=difficulty
            )
        else:
            # Neues Profil erstellen
            success = self.profile_manager.add_profile(
                new_name, self.new_avatar_path, self.new_dart_color, is_ai=is_ai, difficulty=difficulty
            )

        if success:
            self.destroy()
        else:
            messagebox.showerror("Fehler", f"Ein Profil mit dem Namen '{new_name}' existiert bereits.", parent=self)