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
from tkinter import ttk, messagebox, font
from PIL import ImageColor


class CustomColorChooserDialog(tk.Toplevel):
    """
    Ein benutzerdefinierter, modaler Dialog zur Farbauswahl. Bietet eine
    große Live-Vorschau, RGB-Slider, Hex-Code-Eingabe und vordefinierte Farben,
    die alle miteinander synchronisiert sind.
    """

    PREDEFINED_COLORS = [
        "#e53935",
        "#d81b60",
        "#8e24aa",
        "#5e35b1",
        "#3949ab",
        "#1e88e5",
        "#039be5",
        "#00acc1",
        "#00897b",
        "#43a047",
        "#7cb342",
        "#c0ca33",
        "#fdd835",
        "#ffb300",
        "#fb8c00",
        "#f4511e",
        "#6d4c41",
        "#757575",
        "#546e7a",
        "#ffffff",
        "#000000",
    ]

    def __init__(self, parent, initial_color="#ff0000"):
        super().__init__(parent)
        self.transient(parent)
        self.title("Dart-Farbe auswählen")
        self.result_color = None
        self._is_internal_update = False  # Flag zur Vermeidung von Update-Schleifen

        # --- Tkinter-Variablen für die Zwei-Wege-Synchronisation ---
        self.hex_color_var = tk.StringVar(value=initial_color)
        self.r_var = tk.IntVar()
        self.g_var = tk.IntVar()
        self.b_var = tk.IntVar()

        # --- UI-Setup ---
        self._setup_widgets()
        self._setup_traces()

        # Initialen Zustand setzen (dies löst die Trace-Callbacks aus)
        self.hex_color_var.set(initial_color)

        self.update_idletasks()
        self.grab_set()
        self.wait_window(self)

    def _setup_traces(self):
        """Verbindet die Tkinter-Variablen mit den Update-Methoden."""
        self.hex_color_var.trace_add("write", self._update_from_hex)
        self.r_var.trace_add("write", self._update_from_sliders)
        self.g_var.trace_add("write", self._update_from_sliders)
        self.b_var.trace_add("write", self._update_from_sliders)

    def _setup_widgets(self):
        """Erstellt und arrangiert alle UI-Elemente mit einem Grid-Layout."""
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=3)

        # --- Linke Spalte: Große Vorschau und vordefinierte Farben ---
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        self.preview_label = tk.Label(left_frame, text="", relief="solid", borderwidth=1, height=5)
        self.preview_label.pack(fill=tk.X, expand=True)

        swatch_frame = ttk.LabelFrame(left_frame, text="Farbfelder", padding=10)
        swatch_frame.pack(fill=tk.X, pady=(15, 0))
        for i, color in enumerate(self.PREDEFINED_COLORS):
            row, col = divmod(i, 7)
            swatch = tk.Label(
                swatch_frame,
                bg=color,
                width=4,
                height=2,
                relief="raised",
                borderwidth=1,
            )
            swatch.grid(row=row, column=col, padx=3, pady=3)
            swatch.bind("<Button-1>", lambda e, c=color: self._on_swatch_click(c))

        # --- Rechte Spalte: RGB-Slider und Hex-Eingabe ---
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        self._create_slider(right_frame, "R", self.r_var, "red")
        self._create_slider(right_frame, "G", self.g_var, "green")
        self._create_slider(right_frame, "B", self.b_var, "blue")

        hex_frame = ttk.Frame(right_frame)
        hex_frame.pack(fill=tk.X, pady=(20, 0))
        ttk.Label(hex_frame, text="Hex:").pack(side=tk.LEFT)
        self.hex_entry = ttk.Entry(
            hex_frame, textvariable=self.hex_color_var, width=10, font=("Monospace", 10)
        )
        self.hex_entry.pack(side=tk.LEFT, padx=5)

        # --- Untere Reihe: Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky="e", pady=(20, 0))
        ok_button = ttk.Button(button_frame, text="OK", command=self._on_ok, style="Accent.TButton")
        ok_button.pack(side=tk.LEFT, padx=5)
        ok_button.bind("<Return>", lambda e: self._on_ok())
        ok_button.focus_set()
        ttk.Button(button_frame, text="Abbrechen", command=self.destroy).pack(side=tk.LEFT)

    def _create_slider(self, parent, label_text, variable, color):
        """Hilfsmethode zur Erstellung eines RGB-Sliders."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, expand=True, pady=2)
        # Verwende ein Label mit fester Breite für eine saubere Ausrichtung
        label_font = font.Font(family="Monospace", size=10, weight="bold")
        ttk.Label(frame, text=label_text, foreground=color, font=label_font, width=2).pack(
            side=tk.LEFT
        )
        scale = ttk.Scale(frame, from_=0, to=255, orient=tk.HORIZONTAL, variable=variable)
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        # Ein Label, das den numerischen Wert des Sliders anzeigt
        value_label = ttk.Label(frame, textvariable=variable, width=3)
        value_label.pack(side=tk.LEFT)

    def _update_from_sliders(self, *args):
        """Wird aufgerufen, wenn ein Slider bewegt wird. Aktualisiert den Hex-Code."""
        if self._is_internal_update:
            return

        r, g, b = self.r_var.get(), self.g_var.get(), self.b_var.get()
        new_hex = f"#{r:02x}{g:02x}{b:02x}"

        self._is_internal_update = True
        self.hex_color_var.set(new_hex)
        self._is_internal_update = False

        self._update_preview(new_hex)

    def _update_from_hex(self, *args):
        """Wird aufgerufen, wenn der Hex-Code geändert wird. Aktualisiert die Slider."""
        if self._is_internal_update:
            return

        hex_str = self.hex_color_var.get()
        if self._is_valid_hex_color(hex_str):
            r, g, b = ImageColor.getrgb(hex_str)
            self._is_internal_update = True
            self.r_var.set(r)
            self.g_var.set(g)
            self.b_var.set(b)
            self._is_internal_update = False
            self._update_preview(hex_str)
            self.hex_entry.config(foreground="black")  # Gültige Farbe
        else:
            self._update_preview(self.cget("bg"))  # Fallback-Farbe
            self.hex_entry.config(foreground="red")  # Ungültige Farbe

    def _on_swatch_click(self, color):
        """Wird aufgerufen, wenn ein Farbfeld angeklickt wird."""
        self.hex_color_var.set(color)

    def _is_valid_hex_color(self, hex_string):
        """Prüft, ob ein String ein gültiger 6-stelliger Hex-Farbcode ist."""
        if not hex_string.startswith("#") or len(hex_string) != 7:
            return False
        try:
            ImageColor.getrgb(hex_string)
            return True
        except (ValueError, TypeError):
            return False

    def _update_preview(self, hex_color):
        """Aktualisiert die Hintergrundfarbe des großen Vorschau-Labels."""
        self.preview_label.config(bg=hex_color)

    def _on_ok(self):
        """Validiert die Eingabe und schließt den Dialog."""
        final_color = self.hex_color_var.get()
        if self._is_valid_hex_color(final_color):
            self.result_color = final_color
            self.destroy()
        else:
            messagebox.showerror(
                "Ungültige Farbe",
                f"'{final_color}' ist kein gültiger 6-stelliger Hex-Farbcode (z.B. #ff0000).",
                parent=self,
            )
