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
import pytest
from tkinter import ttk
from unittest.mock import MagicMock, patch

# Die zu testende Klasse
from core.custom_colorchooser import CustomColorChooserDialog


@pytest.fixture
def color_chooser_dialog_setup(monkeypatch):
    """
    Patcht blockierende Methoden des CustomColorChooserDialog, um UI-Hänger
    und "window not viewable" Fehler zu vermeiden.
    """
    monkeypatch.setattr("core.custom_colorchooser.CustomColorChooserDialog.grab_set", lambda self: None)
    # KORREKTUR: wait_window wird mit (self, window) aufgerufen. Das Lambda muss diese
    # Signatur widerspiegeln, um einen TypeError zu vermeiden.
    monkeypatch.setattr("core.custom_colorchooser.CustomColorChooserDialog.wait_window", lambda self, window: None)
    # messagebox wird vom CustomColorChooserDialog nicht direkt verwendet, daher kein Patch nötig.
    # PIL.Image/ImageTk werden ebenfalls nicht direkt in der Kernlogik des Dialogs verwendet.


@pytest.mark.ui
class TestCustomColorChooserDialog:
    """Testet die UI-Logik des CustomColorChooserDialog."""

    def test_initial_color_is_set_correctly(self, tk_root_session, color_chooser_dialog_setup):
        """
        Testet, ob die anfängliche Farbe korrekt in den Sliders und dem Farbfeld
        gesetzt wird.
        """
        initial_color = "#aaff00" # RGB: 170, 255, 0
        dialog = CustomColorChooserDialog(tk_root_session, initial_color=initial_color)
        dialog.update()

        # Überprüfe, ob die Slider die korrekten Werte haben
        assert dialog.red_slider.get() == 170
        assert dialog.green_slider.get() == 255
        assert dialog.blue_slider.get() == 0

        # Überprüfe, ob die Farbanzeige die korrekte Farbe hat
        assert dialog.preview_label.cget("bg") == initial_color

        dialog.destroy()

    def test_ok_button_returns_selected_color(self, tk_root_session, color_chooser_dialog_setup):
        """
        Testet, ob der "OK"-Button die ausgewählte Farbe zurückgibt und den Dialog schließt.
        """
        dialog = CustomColorChooserDialog(tk_root_session)
        dialog.update()

        # Setze die Slider auf bestimmte Werte
        dialog.red_slider.set(128)
        dialog.green_slider.set(64)
        dialog.blue_slider.set(32)
        dialog.update_idletasks() # Wichtig, damit die UI-Updates verarbeitet werden

        # Simuliere einen Klick auf den "OK"-Button
        dialog.ok_button.invoke()

        # Überprüfe, ob die result_color korrekt gesetzt wurde
        assert dialog.result_color == "#804020"
        # Der Dialog sollte jetzt nicht mehr existieren
        assert not dialog.winfo_exists()

    def test_cancel_button_returns_none(self, tk_root_session, color_chooser_dialog_setup):
        """
        Testet, ob der "Abbrechen"-Button den Dialog ohne Farbauswahl zerstört.
        """
        dialog = CustomColorChooserDialog(tk_root_session)
        dialog.update()

        # Simuliere einen Klick auf den "Abbrechen"-Button
        dialog.cancel_button.invoke()

        # Überprüfe, ob result_color None ist und der Dialog zerstört wurde
        assert dialog.result_color is None
        assert not dialog.winfo_exists()

    def test_color_updates_dynamically_on_slider_move(self, tk_root_session, color_chooser_dialog_setup):
        """
        Testet, ob sich die Farbe dynamisch ändert, wenn die Slider bewegt werden.
        """
        dialog = CustomColorChooserDialog(tk_root_session)
        dialog.update()

        # Bewege den Rot-Slider
        dialog.red_slider.set(200)
        dialog.update_idletasks()
        assert dialog.preview_label.cget("bg") == "#c80000" # Nur Rot geändert

        # KORREKTUR: Verwende dialog.preview_label statt dialog.color_display
        # Bewege den Grün-Slider
        dialog.green_slider.set(50)
        dialog.update_idletasks()
        assert dialog.preview_label.cget("bg") == "#c83200" # Rot und Grün geändert

        # Bewege den Blau-Slider
        dialog.blue_slider.set(100)
        dialog.update_idletasks()
        assert dialog.preview_label.cget("bg") == "#c83264" # Alle drei geändert

        dialog.destroy()

    def test_swatch_click_updates_color(self, tk_root_session, color_chooser_dialog_setup):
        """
        Testet, ob ein Klick auf ein vordefiniertes Farbfeld (Swatch) alle
        relevanten UI-Elemente (Slider, Hex-Eingabe, Vorschau) aktualisiert.
        """
        dialog = CustomColorChooserDialog(tk_root_session)
        dialog.update()

        # Finde den Frame, der die Farbfelder enthält
        swatch_frame = next(
            w for w in dialog.winfo_children()[0].winfo_children()[0].winfo_children()
            if isinstance(w, ttk.LabelFrame)
        )

        # Wähle das 5. Farbfeld zum Testen (#3949ab)
        target_swatch = swatch_frame.winfo_children()[4]
        target_color = target_swatch.cget("bg")
        assert target_color == "#3949ab"

        # KORREKTUR: Anstatt zu versuchen, das komplexe UI-Event zu simulieren,
        # rufen wir die Callback-Methode direkt auf. Dies ist robuster und testet
        # die eigentliche Logik, ohne von der internen Event-Verarbeitung von Tkinter abzuhängen.
        dialog._on_swatch_click(target_color)
        dialog.update_idletasks()

        # Überprüfe, ob alle Werte korrekt aktualisiert wurden
        assert dialog.hex_color_var.get() == target_color
        assert dialog.r_var.get() == 57  # 0x39
        assert dialog.g_var.get() == 73  # 0x49
        assert dialog.b_var.get() == 171 # 0xab
        assert dialog.preview_label.cget("bg") == target_color

        dialog.destroy()