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
from PIL import Image, ImageTk, ImageColor
import math
import pathlib
import os
from .save_load_manager import SaveLoadManager


class DartBoard:
    """
    Verwaltet das interaktive Dartboard-Fenster.

    Diese Klasse ist verantwortlich für die Darstellung des Dartboards, die
    Erkennung von Würfen durch Mausklicks und die Kommunikation dieser Würfe
    an die zentrale `Game`-Instanz. Sie berechnet anhand von polaren Koordinaten,
    welcher Ring und welches Segment getroffen wurde.

    Class Constants:
        ASSETS_BASE_DIR (pathlib.Path): Der Basispfad zum 'assets'-Verzeichnis.
        DARTBOARD_PATH (pathlib.Path): Pfad zum Dartboard-Bild.
        DART_PATH (pathlib.Path): Pfad zum Dart-Symbolbild.
        ORIGINAL_SIZE (int): Die Kantenlänge des quadratischen Originalbildes in Pixel.
        RADIEN (dict): Ein Dictionary mit den Radien der verschiedenen Ringe
                       im Originalbild.
        SEGMENTS (list[int]): Eine Liste der Zahlenwerte der Segmente, geordnet
                              nach ihrem Winkel auf dem Board.

    Attributes:
        spiel (Game): Eine Referenz auf die übergeordnete Spielinstanz.
        root (tk.Toplevel): Das Fenster, in dem das Dartboard angezeigt wird.
        canvas (tk.Canvas): Das Canvas-Widget, das das Dartboard-Bild enthält.
    """
    ASSETS_BASE_DIR = pathlib.Path(__file__).resolve().parent.parent / "assets"    
    DARTBOARD_PATH = ASSETS_BASE_DIR / "dartboard.png"
    DART_PATH = ASSETS_BASE_DIR / "dart_mask.png" # Geändert auf die Maske
    ORIGINAL_SIZE = 2200  # Originalbildgröße in px
    RADIEN = {
        "bullseye": 30,
        "bull": 80,
        "triple_inner": 470,
        "triple_outer": 520,
        "double_inner": 785,
        "double_outer": 835,
        "außen": 836
    }
    SEGMENTS = [6, 13, 4, 18, 1,
                20, 5, 12, 9, 14,
                11, 8, 16, 7, 19,
                3, 17, 2, 15, 10][::1]

    def __init__(self, spiel):
        """
        Initialisiert das Dartboard-Fenster.

        Erstellt ein neues Toplevel-Fenster, lädt und skaliert die Bilder,
        erstellt das Canvas und die Buttons.

        Args:
            spiel (Game): Die Instanz des laufenden Spiels.
        """
        self.spiel = spiel
        self.radien = DartBoard.RADIEN
        self.segments = DartBoard.SEGMENTS
        self.original_size = DartBoard.ORIGINAL_SIZE
        self.dartboard_path = DartBoard.DARTBOARD_PATH
        self.dart_path = DartBoard.DART_PATH
        self.skaliert = None
        self.center_x = None
        self.center_y = None
        self.canvas = None # Wird in _create_board gesetzt
        self.root = tk.Toplevel()
        if len(self.spiel.name) == 3: # = x01-Spiele
            title = f"{self.spiel.name} - {self.spiel.opt_in}-in, {self.spiel.opt_out}-out"
        elif self.spiel.name == "Around the Clock":
            title = f"{self.spiel.name} - {self.spiel.opt_atc}"
        else:
            title = f"{self.spiel.name}"
        self.root.title(title)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_game)
        self.root.resizable(False, False)
        self._create_board()

        # Dart-Maske laden und für die Einfärbung vorbereiten
        self._dart_photo_image = None
        self.dart_image_ids_on_canvas = [] # Speichert IDs mehrerer Darts für den aktuellen Zug
        try:
            # Die Maske wird einmal geladen und skaliert, um sie wiederverwenden zu können.
            self.original_dart_mask_pil = Image.open(self.dart_path).convert("RGBA")
            dart_display_width = 75
            dart_display_height = dart_display_width
            self.resized_dart_mask_pil = self.original_dart_mask_pil.resize(
                (dart_display_width, dart_display_height), Image.Resampling.LANCZOS
            )
            # Initial eine Standardfarbe setzen
            self.update_dart_image("#ff0000") # Standard-Rot
        except FileNotFoundError:
            pass # print(f"Warnung: Dart-Bild nicht gefunden unter {self.dart_path}")
        except Exception as e:
            pass # print(f"Warnung: Dart-Bild konnte nicht geladen werden: {e}")

    def update_dart_image(self, hex_color: str):
        """
        Färbt die weiße Fläche der Dart-Maske mit der angegebenen Farbe ein
        und aktualisiert das `PhotoImage`-Objekt.

        Args:
            hex_color (str): Die Farbe im Hex-Format (z.B. "#ff0000" für Rot).
        """
        if not hasattr(self, 'resized_dart_mask_pil'):
            return # Maske wurde nicht geladen

        img = self.resized_dart_mask_pil.copy()
        try:
            target_color_rgb = ImageColor.getrgb(hex_color)
        except (ValueError, TypeError):
            # print(f"Warnung: Ungültige Farbe '{hex_color}'. Fallback auf Rot.")
            target_color_rgb = (255, 0, 0)

        # Lade die Pixeldaten für den direkten Zugriff
        pixels = img.load()
        width, height = img.size

        # Iteriere durch alle Pixel und ersetze nur die weißen Flächen (Flights/Shaft).
        # Andere Farben (z.B. schwarz für Barrel/Needle) bleiben unberührt.
        for x in range(width):
            for y in range(height):
                r, g, b, a = pixels[x, y]
                # Ersetze nur weiße, nicht-transparente Pixel
                if r == 255 and g == 255 and b == 255 and a > 0:
                    # Ersetze die Farbe, behalte aber die ursprüngliche Transparenz des Pixels bei
                    pixels[x, y] = target_color_rgb + (a,)

        self._dart_photo_image = ImageTk.PhotoImage(img)

    def clear_dart_images_from_canvas(self):
        """
        Entfernt alle für den aktuellen Zug angezeigten Dart-Bilder vom Canvas.
        """
        if self.canvas:
            for dart_id in self.dart_image_ids_on_canvas:
                self.canvas.delete(dart_id)
        self.dart_image_ids_on_canvas = []

    def clear_last_dart_image_from_canvas(self):
        """
        Entfernt das zuletzt hinzugefügte Dart-Bild vom Canvas.
        Wird von der Undo-Funktion verwendet.
        """
        if self.canvas and self.dart_image_ids_on_canvas:
            dart_id = self.dart_image_ids_on_canvas.pop()
            self.canvas.delete(dart_id)

    def quit_game(self):
        """
        Zeigt einen Dialog mit den Optionen Speichern, Beenden oder Abbrechen.
        """
        # Erstellt einen benutzerdefinierten Toplevel-Dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Spiel beenden")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Dialog zentrieren
        self.root.update_idletasks()
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()
        dialog_w, dialog_h = 400, 120
        dialog.geometry(f"{dialog_w}x{dialog_h}+{parent_x + (parent_w - dialog_w)//2}+{parent_y + (parent_h - dialog_h)//2}")

        def _cleanup_and_quit():
            dialog.destroy()
            self.spiel.destroy() # This already destroys self.root (the dartboard window)

        def save_and_quit():
            # Die save_game_state Methode gibt jetzt True bei Erfolg zurück.
            # Als Parent wird der Dialog selbst übergeben, damit Meldungen darüber erscheinen.
            was_saved = SaveLoadManager.save_game_state(self.spiel, dialog)
            if was_saved:
                _cleanup_and_quit()

        def quit_without_saving():
            _cleanup_and_quit()

        label = ttk.Label(dialog, text="Möchtest du den aktuellen Spielstand speichern, bevor du beendest?", wraplength=360, justify="center")
        label.pack(pady=15)

        button_frame = ttk.Frame(dialog)
        ttk.Button(button_frame, text="Speichern & Beenden", command=save_and_quit).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Beenden", command=quit_without_saving).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Abbrechen", command=dialog.destroy).pack(side="left", padx=5)
        button_frame.pack(pady=10)

    # POLARER WINKEL + DISTANZ
    def polar_angle(self, x, y):
        """
        Berechnet den polaren Winkel eines Punktes relativ zum Zentrum des Boards.

        Args:
            x (int): Die x-Koordinate des Klicks.
            y (int): Die y-Koordinate des Klicks.

        Returns:
            float: Der Winkel in Grad (0-360).
        """
        dx = x - self.center_x
        dy = self.center_y - y
        angle = math.atan2(dy, dx)
        return (math.degrees(angle) + 360) % 360

    def distance(self, x, y):
        """
        Berechnet die euklidische Distanz eines Punktes vom Zentrum des Boards.

        Args:
            x (int): Die x-Koordinate des Klicks.
            y (int): Die y-Koordinate des Klicks.

        Returns:
            float: Die Distanz in Pixeln.
        """
        return math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)

    # RING + SEGMENT ERMITTELN
    def get_ring_segment(self,x, y):
        """
        Ermittelt den getroffenen Ring und das Segment basierend auf Klickkoordinaten.

        Args:
            x (int): Die x-Koordinate des Klicks.
            y (int): Die y-Koordinate des Klicks.

        Returns:
            tuple[str, int]: Ein Tupel bestehend aus dem Namen des Rings und dem Zahlenwert des Segments.
        """
        dist = self.distance(x, y)
        angle = self.polar_angle(x, y)
        idx = int((angle+9) // 18) % 20
        segment = self.segments[idx]

        if dist <= self.skaliert["bullseye"]:
            return "Bullseye", 50
        elif dist <= self.skaliert["bull"]:
            return "Bull", 25
        elif self.skaliert["triple_inner"] < dist < self.skaliert["triple_outer"]:
            return "Triple", segment
        elif self.skaliert["double_inner"] < dist < self.skaliert["double_outer"]:
            return "Double", segment
        elif dist < self.skaliert["außen"]:
            return "Single", segment
        else:
            return "Miss", 0

    def on_click(self, event):
        """
        Event-Handler, der bei einem Mausklick auf das Canvas ausgelöst wird.
        Delegiert die Verarbeitung an die zentrale Logik-Methode.

        Args:
            event (tk.Event): Das von Tkinter generierte Event-Objekt.
        """
        self._process_throw_at_coords(event.x, event.y)

    def on_click_simulated(self, x, y):
        """
        Verarbeitet einen simulierten Klick von der KI.
        Delegiert die Verarbeitung an die zentrale Logik-Methode.

        Args:
            x (int): Die simulierte x-Koordinate.
            y (int): Die simulierte y-Koordinate.
        """
        self._process_throw_at_coords(x, y)

    def _process_throw_at_coords(self, x, y):
        """
        Zentrale Logik zur Verarbeitung eines Wurfs an bestimmten Koordinaten.
        Wird sowohl von echten als auch von simulierten Klicks aufgerufen.

        Args:
            x (int): Die x-Koordinate des Wurfs.
            y (int): Die y-Koordinate des Wurfs.
        """
        # Neues Dart-Bild auf dem Canvas platzieren, falls das Bild geladen ist
        if self._dart_photo_image and self.canvas:
            dart_id = self.canvas.create_image(x - 5, y - 20, image=self._dart_photo_image)
            self.dart_image_ids_on_canvas.append(dart_id)
        # Korrektur der x,y Koordinaten zwingend erforderlich zur korrekten Wurf-Ermittlung
        # NICHT ENTERNEN!!!
        x += 8
        y += 8
        # Schritt 1: Ermittle den Wurf
        ring, segment = self.get_ring_segment(x, y)

        # Schritt 1.5: Normalisiere die Klick-Koordinaten für die Heatmap
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        # Verhindere Division durch Null, falls das Canvas noch nicht gezeichnet ist
        if canvas_width > 1 and canvas_height > 1:
            normalized_coords = (x / canvas_width, y / canvas_height)
        else:
            normalized_coords = None # Fallback

        # Schritt 2: Delegiere die gesamte Spiellogik an den Game-Controller.
        self.spiel.throw(ring, segment, normalized_coords)

    def get_coords_for_target(self, ring: str, segment: int) -> tuple[int, int] | None:
        """
        Ermittelt die idealen (x, y)-Koordinaten für ein bestimmtes Ziel auf dem Board.
        Wird von der KI-Logik verwendet, um Ziele anzuvisieren.

        Args:
            ring (str): Der Zielring (z.B. "Triple", "Double", "Bullseye").
            segment (int): Das Zielsegment (z.B. 20 für T20).

        Returns:
            tuple[int, int] or None: Ein (x, y)-Tupel der Zielkoordinaten oder None,
                                     wenn das Ziel ungültig ist.
        """
        if ring == "Bullseye":
            return self.center_x, self.center_y
        if ring == "Bull":
            # Zielt auf die Mitte des Bull-Rings (zwischen Bullseye und äußerem Bull-Rand)
            radius = (self.skaliert["bullseye"] + self.skaliert["bull"]) / 2
            angle_rad = 0 # Winkel ist irrelevant, aber wir können 0 nehmen
        else:
            try:
                idx = self.segments.index(segment)
            except ValueError:
                return None # Ungültiges Segment

            # Berechne den mittleren Winkel für dieses Segment in Radiant.
            # Jeder Sektor ist 18 Grad breit. Die Mitte ist bei (index * 18) Grad.
            angle_deg = idx * 18
            angle_rad = math.radians(angle_deg)

            # Finde den mittleren Radius für den Zielring
            ring_map = {
                "Triple": (self.skaliert["triple_inner"] + self.skaliert["triple_outer"]) / 2,
                "Double": (self.skaliert["double_inner"] + self.skaliert["double_outer"]) / 2,
                "Single": (self.skaliert["bull"] + self.skaliert["triple_inner"]) / 2, # Großes Single-Feld
            }
            radius = ring_map.get(ring)
            if radius is None: return None # Unbekannter Ring

        x = self.center_x + radius * math.cos(angle_rad)
        y = self.center_y - radius * math.sin(angle_rad) # Y-Achse ist im Canvas invertiert
        return int(x), int(y)

    def _create_board(self):
        """
        Erstellt und konfiguriert das Dartboard-Canvas und die zugehörigen Widgets.

        Diese private Methode skaliert das Dartboard-Bild auf die Bildschirmhöhe,
        erstellt das Canvas, platziert das Bild und bindet den Klick-Handler.
        """
        # Bildschirmgröße
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        target_height = int(screen_height * 0.90)

        # Bildgröße skalieren
        SCALE = target_height / self.original_size
        # Radien skalieren
        self.skaliert = {k: int(v * SCALE) for k, v in self.radien.items()}
        # Bild vorbereiten
        image = Image.open(self.dartboard_path)
        # Bild skalieren
        new_size = (int(image.width * SCALE), int(image.height * SCALE))
        self.center_x, self.center_y = new_size[0] // 2, new_size[1] // 2
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized)
        # Canvas erstellen
        self.canvas = tk.Canvas(self.root, width=new_size[0], height=new_size[1])
        self.canvas.pack(side="top", fill="both", expand=True)
        # Bild einfügen
        self.canvas.create_image(0, 0, image=photo, anchor=tk.NW)
        self.canvas.image = photo
        self.canvas.bind("<Button-1>", self.on_click)

        # Buttons erstellen
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(side="bottom", fill="x", pady=5)
        self.undo_button = ttk.Button(btn_frame, text=" Zurück  ", command=self.spiel.undo)
        self.undo_button.pack(pady=5)
        self.done_button = ttk.Button(btn_frame, text=" Weiter  ", style="Accent.TButton", command=self.spiel.next_player)
        self.done_button.pack(pady=5)
        quit_button = ttk.Button(btn_frame, text="Beenden", command=self.quit_game)
        quit_button.pack(pady=5)
        self.done_button.bind("<Return>", lambda event: self.spiel.next_player())
        self.canvas.create_window(
            new_size[0], new_size[1],
            window=btn_frame,
            anchor="se"
        )

        # Fenster zentrieren, nachdem alle Widgets hinzugefügt wurden
        self.root.update_idletasks()
        window_width = self.root.winfo_reqwidth()
        window_height = self.root.winfo_reqheight()
        pos_x = (screen_width // 2) - (window_width // 2)
        pos_y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

    def update_button_states(self):
        """
        Aktualisiert den Zustand der 'Weiter'- und 'Zurück'-Buttons basierend
        auf der Anzahl der Würfe des aktuellen Spielers und dem Spielstatus.
        """
        if not self.spiel or not self.spiel.current_player():
            return

        player = self.spiel.current_player()
        num_throws = len(player.throws)

        # 'Weiter'-Button: Aktiv, wenn 3 Würfe gemacht wurden, der Zug durch
        # einen Bust beendet ist oder das Spiel insgesamt zu Ende ist.
        if num_throws >= 3 or player.turn_is_over or self.spiel.end:
            self.done_button.focus_set()
            self.done_button.config(state=tk.NORMAL)
        else:
            self.done_button.config(state=tk.DISABLED)

        # 'Zurück'-Button: Aktiv, wenn mindestens ein Wurf in der aktuellen Runde
        # gemacht wurde. Das Spielende ist hier irrelevant, da der Undo-Handler
        # den Spielzustand bei Bedarf selbst zurücksetzt.
        if num_throws > 0:
            self.undo_button.config(state=tk.NORMAL)
        else:
            self.undo_button.config(state=tk.DISABLED)
        
