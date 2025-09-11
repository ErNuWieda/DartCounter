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

    def __init__(self, parent, profile_manager, player_stats_manager=None):
        super().__init__(parent)
        self.transient(parent)
        self.profile_manager = profile_manager
        self.player_stats_manager = player_stats_manager
        self.color_images = []  # Wichtig: Referenzen auf die Bilder halten

        self.title("Spielerprofile verwalten")
        self.resizable(False, False)

        self._setup_widgets()
        self._populate_profile_list()

        # UI aktualisieren, damit Tkinter die benötigte Breite berechnen kann
        self.update_idletasks()
        # Die berechnete Breite verwenden und eine feste Höhe beibehalten
        self.geometry(f"{self.winfo_reqwidth()}x425")
        self.grab_set()

    def _setup_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Button Frame (ganz unten) ---
        # Dieser Frame wird zuerst gepackt, damit er seinen Platz am unteren Rand reserviert,
        # bevor der List-Frame den restlichen Platz einnimmt.
        button_frame = ttk.Frame(main_frame, padding=(0, 10))
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        # --- List Frame (füllt den restlichen Platz) ---
        list_frame = ttk.LabelFrame(main_frame, text="Gespeicherte Profile")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Die erste Spalte (#0) wird für das Farbsymbol, die weiteren für Daten verwendet.
        self.tree = ttk.Treeview(
            list_frame,
            columns=("Name", "Spielertyp", "Schwierigkeit"),
            show="tree headings",
        )
        # Konfiguriere die Symbolspalte für das Farbfeld
        self.tree.column("#0", width=40, stretch=tk.NO, anchor="center")
        # Konfiguriere die Namensspalte
        self.tree.heading("Name", text="Name")
        self.tree.column("Name", width=200)
        # Konfiguriere die weiteren Spalten
        self.tree.heading("Spielertyp", text="Spielertyp")
        self.tree.column("Spielertyp", width=100, anchor="center")
        self.tree.heading("Schwierigkeit", text="Schwierigkeit")
        self.tree.column("Schwierigkeit", width=120, anchor="center")

        self.tree.bind("<Double-1>", lambda e: self._edit_selected_profile())
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.config(yscrollcommand=scrollbar.set)

        # --- Buttons im Button Frame ---
        ttk.Button(button_frame, text="Neues Profil", command=self._add_new_profile).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            button_frame, text="Profil bearbeiten", command=self._edit_selected_profile
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Profil löschen", command=self._delete_selected_profile).pack(
            side=tk.LEFT, padx=5
        )

        recalc_button = ttk.Button(
            button_frame,
            text="Genauigkeitsmodell neu berechnen",
            command=self._recalculate_accuracy,
        )
        recalc_button.pack(side=tk.LEFT, padx=5)
        if not self.player_stats_manager:
            recalc_button.config(state="disabled")

        ttk.Button(button_frame, text="Schließen", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def _populate_profile_list(self):
        # Bestehende Einträge und Bildreferenzen löschen
        self.tree.delete(*self.tree.get_children())
        self.color_images.clear()

        # 1. Profile abrufen und in Gruppen aufteilen
        all_profiles = self.profile_manager.get_profiles()
        ai_profiles = [p for p in all_profiles if p.is_ai]
        human_profiles = [p for p in all_profiles if not p.is_ai]

        # 2. Gruppen sortieren
        # KI-Spieler nach Schwierigkeit sortieren
        difficulty_order = [
            "Anfänger",
            "Fortgeschritten",
            "Amateur",
            "Profi",
            "Champion",
        ]
        ai_profiles.sort(
            key=lambda p: (
                difficulty_order.index(p.difficulty) if p.difficulty in difficulty_order else 99
            )
        )
        # Menschliche Spieler alphabetisch sortieren
        human_profiles.sort(key=lambda p: p.name)

        # 3. Kombinierte und sortierte Liste erstellen (Menschen zuerst)
        sorted_profiles = human_profiles + ai_profiles

        # 4. Sortierte Profile in den Treeview einfügen
        for profile in sorted_profiles:
            self._insert_profile_item("", profile)

    def _insert_profile_item(self, parent_id: str, profile: PlayerProfile):
        """
        Fügt ein einzelnes Profil-Item in den Treeview unter einem bestimmten Parent ein.
        Diese Hilfsmethode vermeidet Code-Duplizierung.
        """
        # Erstelle ein kleines, farbiges Bild für die Vorschau
        img = Image.new("RGB", (16, 16), profile.dart_color)
        photo_img = ImageTk.PhotoImage(img)
        self.color_images.append(photo_img)  # Referenz speichern!

        player_type = "KI" if profile.is_ai else "Mensch"
        difficulty = profile.difficulty if profile.is_ai else "-"
        self.tree.insert(
            parent_id,
            "end",
            image=photo_img,
            values=(profile.name, player_type, difficulty),
        )

    def _add_new_profile(self):
        dialog = EditProfileDialog(self, self.profile_manager)
        self.wait_window(dialog)
        self._populate_profile_list()

    def _edit_selected_profile(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(
                "Keine Auswahl",
                "Bitte wählen Sie zuerst ein Profil aus der Liste aus.",
                parent=self,
            )
            return

        # Verhindere Bearbeitung von Gruppen-Headern (obwohl keine mehr da sind, ist das gute Praxis)
        item_data = self.tree.item(selected_item)
        if not item_data.get("values"):
            return

        profile_name = self.tree.item(selected_item)["values"][0]
        profile_to_edit = self.profile_manager.get_profile_by_name(profile_name)
        if profile_to_edit:
            dialog = EditProfileDialog(self, self.profile_manager, profile_to_edit=profile_to_edit)
            self.wait_window(dialog)
            self._populate_profile_list()

    def _delete_selected_profile(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(
                "Keine Auswahl",
                "Bitte wählen Sie zuerst ein Profil aus der Liste aus.",
                parent=self,
            )
            return

        # Verhindere Löschen von Gruppen-Headern
        item_data = self.tree.item(selected_item)
        if not item_data.get("values"):
            return

        profile_name = self.tree.item(selected_item)["values"][0]
        if messagebox.askyesno(
            "Profil löschen",
            f"Möchten Sie das Profil '{profile_name}' wirklich löschen?",
            parent=self,  # type: ignore
        ):
            if self.profile_manager.delete_profile(profile_name):
                self._populate_profile_list()

    def _recalculate_accuracy(self):
        """Löst die Neuberechnung des Genauigkeitsmodells für das ausgewählte Profil aus."""
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(
                "Keine Auswahl",
                "Bitte wählen Sie zuerst ein Profil aus der Liste aus.",
                parent=self,
            )
            return

        item_data = self.tree.item(selected_item)
        if not item_data.get("values"):
            return  # Gruppen-Header wurde geklickt

        profile_name = self.tree.item(selected_item)["values"][0]
        player_type = self.tree.item(selected_item)["values"][1]

        if player_type == "KI":
            title = "Falscher Spielertyp"
            message = (
                "Ein Genauigkeitsmodell kann nur für menschliche Spieler aus "
                "deren Spieldaten berechnet werden."
            )
            messagebox.showwarning(title, message, parent=self)
            return

        if not self.player_stats_manager:
            messagebox.showerror(
                "Fehler", "Der Statistik-Manager ist nicht verfügbar.", parent=self
            )
            return

        confirm_title = "Bestätigung"
        confirm_message = (
            f"Möchten Sie das Genauigkeitsmodell für '{profile_name}' jetzt neu berechnen?\n\n"
            "Dieser Vorgang analysiert alle gespeicherten Würfe und kann einen Moment dauern."
        )
        if messagebox.askyesno(confirm_title, confirm_message, parent=self):
            success = self.player_stats_manager.update_accuracy_model(
                profile_name, parent_window=self
            )
            if success:
                # Erzwinge, dass der Manager seine interne Liste aus der DB neu lädt
                self.profile_manager.reload_profiles()
                # Aktualisiere die Treeview-Anzeige in diesem Dialog
                self._populate_profile_list()
