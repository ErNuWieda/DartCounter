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
from PIL import Image, ImageTk
from .player_profile import PlayerProfile
from .edit_profile_dialog import EditProfileDialog

class ProfileManagerDialog(tk.Toplevel):
    """
    Ein Dialog zur Verwaltung von Spielerprofilen (Erstellen, Löschen).
    """
    def __init__(self, parent, profile_manager):
        super().__init__(parent)
        self.transient(parent)
        self.profile_manager = profile_manager
        self.color_images = [] # Wichtig: Referenzen auf die Bilder halten

        self.title("Spielerprofile verwalten")
        self.geometry("600x375")
        self.grab_set()

        self._setup_widgets()
        self._populate_profile_list()

    def _setup_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.LabelFrame(main_frame, text="Gespeicherte Profile")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Die erste Spalte (#0) wird für das Farbsymbol, die weiteren für Daten verwendet.
        self.tree = ttk.Treeview(list_frame, columns=("Name", "Spielertyp"), show="tree headings")
        # Konfiguriere die Symbolspalte für das Farbfeld
        self.tree.column("#0", width=40, stretch=tk.NO, anchor="center")
        # Konfiguriere die Namensspalte
        self.tree.heading("Name", text="Name")
        self.tree.column("Name", width=200)
        # Konfiguriere die Spielertyp-Spalte
        self.tree.heading("Spielertyp", text="Spielertyp")
        self.tree.column("Spielertyp", width=100, anchor="center")
        self.tree.bind("<Double-1>", lambda e: self._edit_selected_profile())
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(main_frame, padding=(0, 10))
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        ttk.Button(button_frame, text="Neues Profil", command=self._add_new_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Profil bearbeiten", command=self._edit_selected_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Profil löschen", command=self._delete_selected_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Schließen", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def _populate_profile_list(self):
        # Bestehende Einträge und Bildreferenzen löschen
        self.tree.delete(*self.tree.get_children())
        self.color_images.clear()

        profiles = sorted(self.profile_manager.get_profiles(), key=lambda p: p.name)
        for profile in profiles:
            # Erstelle ein kleines, farbiges Bild für die Vorschau
            img = Image.new('RGB', (16, 16), profile.dart_color)
            photo_img = ImageTk.PhotoImage(img)
            self.color_images.append(photo_img) # Referenz speichern!
            player_type = "KI" if profile.is_ai else "Mensch"
            self.tree.insert("", "end", image=photo_img, values=(profile.name, player_type))

    def _add_new_profile(self):
        dialog = EditProfileDialog(self, self.profile_manager)
        self.wait_window(dialog)
        self._populate_profile_list()

    def _edit_selected_profile(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie zuerst ein Profil aus der Liste aus.", parent=self)
            return
        
        profile_name = self.tree.item(selected_item)['values'][0]
        profile_to_edit = self.profile_manager.get_profile_by_name(profile_name)
        if profile_to_edit:
            dialog = EditProfileDialog(self, self.profile_manager, profile_to_edit=profile_to_edit)
            self.wait_window(dialog)
            self._populate_profile_list()

    def _delete_selected_profile(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie zuerst ein Profil aus der Liste aus.", parent=self)
            return

        profile_name = self.tree.item(selected_item)['values'][0]
        if messagebox.askyesno("Profil löschen", f"Möchten Sie das Profil '{profile_name}' wirklich löschen?", parent=self):
            if self.profile_manager.delete_profile(profile_name):
                self._populate_profile_list()