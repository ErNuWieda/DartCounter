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
import random
from typing import TYPE_CHECKING

from .save_load_manager import SaveLoadManager # Wird für quit_game benötigt
from . import ui_utils
from .dartboard_geometry import DartboardGeometry


class DartBoard:
    """
    Verwaltet das interaktive Dartboard-Fenster.

    Diese Klasse ist verantwortlich für die Darstellung des Dartboards, die
    Erkennung von Würfen durch Mausklicks und die Kommunikation dieser Würfe
    an die zentrale `Game`-Instanz. Sie berechnet anhand von polaren Koordinaten,
    welcher Ring und welches Segment getroffen wurde.

    Class Constants (Refactored):
        RING_DEFINITIONS (list[tuple]): Eine datengesteuerte Definition der Ringe.
                                        Jedes Tupel enthält:
                                        (Ring-Name, innerer Radius-Key, äußerer Radius-Key)
                                        Dies ersetzt die harte Verdrahtung von Radien in der Logik
                                        und macht die `get_ring_segment`-Methode wartbarer.
                                        Die Reihenfolge (von innen nach außen) ist wichtig für die
                                        korrekte Erkennung.

    Attributes:
        game_view_manager (GameViewManager): Eine Referenz auf den GameViewManager.
        root (tk.Toplevel): Das Fenster, in dem das Dartboard angezeigt wird.
        canvas (tk.Canvas): Das Canvas-Widget, das das Dartboard-Bild enthält.
    """

    ASSETS_BASE_DIR = pathlib.Path(__file__).resolve().parent.parent / "assets"
    DARTBOARD_PATH = ASSETS_BASE_DIR / "dartboard.png"
    DART_PATH = ASSETS_BASE_DIR / "dart_mask.png"  # Geändert auf die Maske

    # Diese Konstante korrigiert die Abweichung des visuellen Zentrums des Dartboards
    # vom geometrischen Zentrum der Bilddatei. Eine kleine Anpassung ist oft nötig,
    # um eine pixelgenaue Treffererkennung zu gewährleisten.
    # Ein positiver x-Offset bedeutet, dass das visuelle Zentrum nach RECHTS verschoben ist.
    # Ein positiver y-Offset bedeutet, dass das visuelle Zentrum nach UNTEN verschoben ist.
    BOARD_CENTER_OFFSET = (-8, -7)

    if TYPE_CHECKING:
        from .game_view_manager import GameViewManager

    def __init__(self, game_view_manager: "GameViewManager", parent_root: tk.Tk):
        """
        Initialisiert das Dartboard-Fenster.

        Erstellt ein neues Toplevel-Fenster, lädt und skaliert die Bilder,
        erstellt das Canvas und die Buttons.

        Args:
            spiel (Game): Die Instanz des laufenden Spiels.
            parent_root (tk.Tk | tk.Toplevel): Das übergeordnete Fenster.
        """
        self.game_view_manager = game_view_manager
        self.dartboard_path = DartBoard.DARTBOARD_PATH
        self.dart_path = DartBoard.DART_PATH
        self.skaliert = None
        self.center_x = None
        self.center_y = None
        self.canvas = None  # Wird in _create_board gesetzt
        self.throw_delay = self.game_view_manager.settings_manager.get("ai_throw_delay", 1000) # Für KI-Würfe
        self.root = tk.Toplevel(parent_root)
        if len(self.game_view_manager.game_options.name) == 3:  # = x01-Spiele
            title = f"{self.game_view_manager.game_options.name} - {self.game_view_manager.game_options.opt_in}-in, "
            title += f"{self.game_view_manager.game_options.opt_out}-out"
        elif self.game_view_manager.game_options.name == "Around the Clock":
            title = f"{self.game_view_manager.game_options.name} - {self.game_view_manager.game_options.opt_atc}"
        else:
            title = f"{self.game_view_manager.game_options.name}"
        self.root.title(title)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_game)
        self.root.resizable(False, False)
        self._create_board()

        self._dart_photo_image = None  # Will be filled with the colored dart image later
        self.dart_image_ids_on_canvas = []  # Stores canvas IDs of darts for the current turn
        try:
            # Die Maske wird einmal geladen und skaliert, um sie wiederverwenden zu können.
            self.original_dart_mask_pil = Image.open(self.dart_path).convert("RGBA")

            # Skaliere den Dart proportional zur Board-Größe (Basis: 220px für die Originalgröße)
            scale = self.skaliert["outer_edge"] / DartboardGeometry.RADIEN["outer_edge"]
            dart_size = max(20, int(220 * scale))
            self.resized_dart_mask_pil = self.original_dart_mask_pil.resize(
                (dart_size, dart_size), Image.Resampling.LANCZOS
            )
            self.update_dart_image("#ff0000")
        except FileNotFoundError:  # pragma: no cover
            pass  # print(f"Warnung: Dart-Bild nicht gefunden unter {self.dart_path}")
        except Exception:
            pass  # print(f"Warnung: Dart-Bild konnte nicht geladen werden: {e}")

    def update_dart_image(self, hex_color: str):
        """
        Färbt die weiße Fläche der Dart-Maske mit der angegebenen Farbe ein
        und aktualisiert das `PhotoImage`-Objekt.

        Args:
            hex_color (str): Die Farbe im Hex-Format (z.B. "#ff0000" für Rot).
        """
        if not hasattr(self, "resized_dart_mask_pil"):
            return  # Maske wurde nicht geladen

        img = self.resized_dart_mask_pil.copy()
        try:
            target_color_rgb = ImageColor.getrgb(hex_color)
        except (ValueError, TypeError):
            # Fallback auf Rot bei ungültiger Farbe
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
        """Delegiert die Anfrage zum Beenden des Spiels an den GameViewManager."""
        self.game_view_manager.quit_game()

    def display_dart_on_canvas(self, x: int, y: int):
        """
        Zeigt ein Dart-Bild auf dem Canvas an den angegebenen Koordinaten an.
        """
        if self._dart_photo_image and self.canvas:
            # Die -5 und -20 sind Offsets, um die Spitze des Darts auf die Klickposition zu setzen.
            dart_id = self.canvas.create_image(x - 5, y - 20, image=self._dart_photo_image)
            self.dart_image_ids_on_canvas.append(dart_id)

    def get_coords_for_target(self, ring: str, segment: int) -> tuple[int, int] | None:
        """Ermittelt die idealen (x, y)-Koordinaten für ein bestimmtes Ziel auf dem Board."""
        return DartboardGeometry.get_target_coords_scaled(ring, segment, self.canvas, self.skaliert)

    def polar_angle(self, x, y):
        """
        Berechnet den polaren Winkel eines Punktes relativ zum Zentrum des Boards.

        Args:
            x (int): Die x-Koordinate des Klicks.
            y (int): Die y-Koordinate des Klicks.

        Returns:
            float: Der Winkel in Grad (0-360).
        """
        # Korrekte Winkelberechnung für ein Koordinatensystem mit (0,0) oben links.
        # math.atan2 erwartet (y, x).
        angle_rad = math.atan2(y - self.center_y, x - self.center_x)
        return (math.degrees(angle_rad) + 360) % 360

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
    def get_ring_segment(self, x, y):
        """Ermittelt den getroffenen Ring und das Segment basierend auf Klickkoordinaten."""
        dist = self.distance(x, y)

        # Prüfe die Ringe von innen nach außen. Diese Logik ist klarer und weniger
        # fehleranfällig als die vorherige Kombination aus Sonderfall und Schleife.
        if dist <= self.skaliert["bullseye"]:
            return "Bullseye", 50
        if dist <= self.skaliert["bull"]:
            return "Bull", 25

        # Wenn es nicht Bull oder Bullseye ist, benötigen wir den Winkel für das Segment.
        angle = self.polar_angle(x, y)

        # Die `SEGMENTS`-Liste in DartboardGeometry ist im Uhrzeigersinn sortiert,
        # beginnend mit der 6 (auf der 0°-Linie). Wir addieren 9° (halbe
        # Segmentbreite), um die Grenzen korrekt zu behandeln, und teilen durch 18°.
        idx = int((angle + 9) // 18) % 20
        segment = DartboardGeometry.SEGMENTS[idx]

        # Korrekte, von innen nach außen gestaffelte Prüfung der Ringe.
        # Dies ist die robuste Methode, um die Ringe eindeutig zuzuordnen.
        if dist <= self.skaliert["triple_inner"]:
            return "Single", segment  # Großer Single-Bereich
        elif dist <= self.skaliert["triple_outer"]:
            return "Triple", segment
        elif dist <= self.skaliert["double_inner"]:
            return "Single", segment  # Kleiner Single-Bereich
        elif dist <= self.skaliert["double_outer"]:
            return "Double", segment
        # Alles außerhalb des Double-Rings, aber innerhalb des Board-Randes, ist ein "Miss".
        elif dist <= self.skaliert["outer_edge"]:
            return "Miss", 0
        else:
            return "Miss", 0

    def on_click(self, event):
        """Event-Handler für Mausklicks, leitet an den GameController weiter."""
        self.game_view_manager.game_controller.process_player_throw(event.x, event.y)

    def simulate_click(self, x: int, y: int):
        """
        Simuliert einen Klick auf das Dartboard an den gegebenen Koordinaten (x, y).
        Diese Methode wird von KI-Spielern verwendet, um einen Wurf auszuführen.
        """
        self.game_view_manager.game_controller.process_player_throw(x, y)

    def _process_throw_at_coords(self, x: int, y: int):
        """
        Diese Methode ist jetzt privat und wird nur noch intern vom DartBoard
        aufgerufen, um die Koordinaten zu verarbeiten und an den GameController
        weiterzuleiten.
        """
        # Zuerst das Dart-Bild auf dem Canvas anzeigen
        self.display_dart_on_canvas(x, y)

        # Dann Ring und Segment ermitteln
        # Die Logik zur Ermittlung von Ring und Segment bleibt hier, da sie direkt
        # von den Dartboard-Koordinaten abhängt.

        ring, segment = self.get_ring_segment(x, y)

        # Schritt 1.5: Normalisiere die Klick-Koordinaten für die Heatmap
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        # Verhindere Division durch Null, falls das Canvas noch nicht gezeichnet ist
        if canvas_width > 1 and canvas_height > 1:
            normalized_coords = (x / canvas_width, y / canvas_height)
        else:
            normalized_coords = None  # Fallback
        # Delegiere die gesamte Spiellogik an den GameController.
        self.game_view_manager.game_controller.throw(ring, segment, normalized_coords)

    def _create_board(self):
        """
        Erstellt und konfiguriert das Dartboard-Canvas und die zugehörigen Widgets.
        Diese private Methode skaliert das Dartboard-Bild auf die Bildschirmhöhe,
        erstellt das Canvas, platziert das Bild und bindet den Klick-Handler.
        """
        # Bildschirmgröße
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        target_height = int(screen_height * 0.90)  # type: ignore

        # Bildgröße skalieren
        SCALE = target_height / DartboardGeometry.ORIGINAL_SIZE
        # Radien skalieren
        self.skaliert = {k: int(v * SCALE) for k, v in DartboardGeometry.RADIEN.items()}
        # Bild vorbereiten
        image = Image.open(self.dartboard_path)
        # Bild skalieren
        new_size = (int(image.width * SCALE), int(image.height * SCALE))
        # Berechne den Mittelpunkt einmalig und korrigiere ihn mit dem Offset.
        # Der Offset muss proportional zur Skalierung mitwachsen.
        self.center_x = (new_size[0] // 2) + int(self.BOARD_CENTER_OFFSET[0] * SCALE)
        self.center_y = (new_size[1] // 2) + int(self.BOARD_CENTER_OFFSET[1] * SCALE)
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
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(side="bottom", fill="x", pady=5)
        self.undo_button = ttk.Button(btn_frame, text=" Zurück  ", command=self.game_view_manager.game_controller.undo)
        self.undo_button.pack(pady=5)
        self.done_button = ttk.Button(
            btn_frame,
            text=" Weiter  ",
            style="Accent.TButton",
            command=self.game_view_manager.game_controller.next_player,
        )
        self.done_button.pack(pady=5)
        quit_button = ttk.Button(btn_frame, text="Beenden", command=self.quit_game)
        quit_button.pack(pady=5)
        self.done_button.bind("<Return>", lambda event: self.game_view_manager.game_controller.next_player())
        self.canvas.create_window(new_size[0], new_size[1], window=btn_frame, anchor="se")

        # Fenster zentrieren, nachdem alle Widgets hinzugefügt wurden
        self.root.update_idletasks()
        window_width = self.root.winfo_reqwidth()
        window_height = self.root.winfo_reqheight()
        pos_x = (screen_width // 2) - (window_width // 2) # type: ignore
        pos_y = (screen_height // 2) - (window_height // 2) # type: ignore
        self.root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

    def update_button_states(self, player: "Player", game_ended: bool):
        """
        Aktualisiert den Zustand der 'Weiter'- und 'Zurück'-Buttons basierend
        auf der Anzahl der Würfe des aktuellen Spielers und dem Spielstatus.
        """ # type: ignore
        num_throws = len(player.throws)
        # 'Weiter'-Button: Aktiv, wenn 3 Würfe gemacht wurden, der Zug durch
        # einen Bust beendet ist oder das Spiel insgesamt zu Ende ist.
        if num_throws >= 3 or player.turn_is_over or game_ended:
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

    def show_big_fish_effect(self):
        """Zeigt einen speziellen visuellen Effekt für das 170er Finish (Big Fish)."""
        if not self.canvas:
            return

        tag = "big_fish_overlay"

        # Großer Fisch-Emoji in der Mitte (leicht nach oben versetzt)
        self.canvas.create_text(
            self.center_x, self.center_y - 20,
            text="🐟",
            font=("Arial", 120),
            tags=tag
        )

        # Text "THE BIG FISH!" mit Schatten-Effekt für bessere Lesbarkeit
        self.canvas.create_text(
            self.center_x + 2, self.center_y + 92,
            text="THE BIG FISH!",
            font=("Arial", 40, "bold"),
            fill="black",
            tags=tag
        )
        self.canvas.create_text(
            self.center_x, self.center_y + 90,
            text="THE BIG FISH!",
            font=("Arial", 40, "bold"),
            fill="gold",
            tags=tag
        )

        # Den Effekt nach 5 Sekunden automatisch entfernen
        self.root.after(5000, lambda: self.canvas.delete(tag) if self.canvas else None)

    def show_180_effect(self):
        """Zeigt einen flackernden Effekt für einen Score von 180."""
        if not self.canvas:
            return

        tag = "one_eighty_overlay"
        colors = ["#ff0000", "#ffff00", "#ffaa00", "#ffffff"]  # Rot, Gelb, Orange, Weiß

        # Großer "180" Text in der Mitte
        text_id = self.canvas.create_text(
            self.center_x, self.center_y,
            text="180",
            font=("Arial", 120, "bold"),
            fill="red",
            tags=tag
        )

        # Blitze drumherum positionieren
        lightning_positions = [
            (self.center_x - 140, self.center_y - 90),
            (self.center_x + 140, self.center_y - 90),
            (self.center_x - 140, self.center_y + 90),
            (self.center_x + 140, self.center_y + 90),
        ]
        lightning_ids = []
        for lx, ly in lightning_positions:
            l_id = self.canvas.create_text(lx, ly, text="⚡", font=("Arial", 70), tags=tag)
            lightning_ids.append(l_id)

        def flicker(count):
            if not self.canvas or not self.root.winfo_exists():
                return
            if count <= 0:
                try: self.canvas.delete(tag)
                except: pass
                return

            color = random.choice(colors)
            try:
                self.canvas.itemconfig(text_id, fill=color)
                for lid in lightning_ids:
                    self.canvas.itemconfig(lid, fill=color)
                self.root.after(100, lambda: flicker(count - 1))
            except: pass

        flicker(30)  # 3 Sekunden lang flackern (30 * 100ms)

    def show_no_score_effect(self, is_bust=False):
        """Zeigt einen humorvollen Effekt für einen Score von 0 oder ein Überwerfen (Bust)."""
        if not self.canvas:
            return

        tag = "no_score_overlay"
        emoji = "💥" if is_bust else "🐌"
        display_text = "BUST!" if is_bust else "NO SCORE!"
        text_color = "red" if is_bust else "gray"

        # Emoji (Schnecke für 0, Explosion für Bust)
        self.canvas.create_text(
            self.center_x, self.center_y - 20,
            text=emoji,
            font=("Arial", 100),
            tags=tag
        )

        # Text-Hinweis
        self.canvas.create_text(
            self.center_x, self.center_y + 80,
            text=display_text,
            font=("Arial", 30, "bold"),
            fill=text_color,
            tags=tag
        )

        # Nach 3 Sekunden automatisch entfernen
        self.root.after(3000, lambda: self.canvas.delete(tag) if self.canvas else None)

    def show_low_score_effect(self):
        """Zeigt einen mitleidigen Effekt für einen niedrigen Score (1-7 Punkte)."""
        if not self.canvas:
            return

        tag = "low_score_overlay"

        # Weinendes Emoji
        self.canvas.create_text(
            self.center_x, self.center_y - 20,
            text="😢",
            font=("Arial", 100),
            tags=tag
        )

        # Text "LOW SCORE!" in einem traurigen Blau
        self.canvas.create_text(
            self.center_x, self.center_y + 80,
            text="LOW SCORE!",
            font=("Arial", 30, "bold"),
            fill="dodgerblue",
            tags=tag
        )

        # Nach 3 Sekunden automatisch entfernen
        self.root.after(3000, lambda: self.canvas.delete(tag) if self.canvas else None)
