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

import math


class DartboardGeometry:
    """
    Eine UI-unabhängige Utility-Klasse, die die Geometrie des Dartboards kapselt.
    Sie enthält Konstanten und Methoden zur Umrechnung zwischen Segmentnamen und Koordinaten.
    Alle Koordinaten beziehen sich auf ein theoretisches Originalbild von 2200x2200 Pixel.
    """

    ORIGINAL_SIZE = 2200
    CENTER = ORIGINAL_SIZE // 2
    RADIEN = {
        "bullseye": 35,       # Neu vermessen 2024-05-23 (Zentrum korrigiert)
        "bull": 79,           # Neu vermessen 2024-05-23 (Zentrum korrigiert)
        "triple_inner": 464,  # Neu vermessen 2024-05-23 (Zentrum korrigiert)
        "triple_outer": 516,  # Neu vermessen 2024-05-23 (Zentrum korrigiert)
        "double_inner": 771,  # Neu vermessen 2024-05-23 (Zentrum korrigiert)
        "double_outer": 820,  # Neu vermessen 2024-05-23 (Zentrum korrigiert)
        "outer_edge": 1068,   # Neu vermessen 2024-05-23 (Zentrum korrigiert)
    }
    # Standard-Dartboard-Layout, im Uhrzeigersinn, beginnend bei der 3-Uhr-Position.
    # Dies ist die korrekte, standardisierte Reihenfolge.
    SEGMENTS = [6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5, 20, 1, 18, 4, 13]

    @staticmethod
    def get_segment_from_coords(x: float, y: float, size: int = 2200) -> str:
        """
        Ermittelt das getroffene Segment (z.B. "20", "Bullseye", "Miss") basierend auf
        Koordinaten, die auf eine Referenzgröße skaliert sind.

        Args:
            x (float): Die x-Koordinate.
            y (float): Die y-Koordinate.
            size (int): Die Referenzgröße des Boards, auf das sich x und y beziehen.

        Returns:
            str: Der Name des getroffenen Segments.
        """
        scale = DartboardGeometry.ORIGINAL_SIZE / size
        center = size / 2
        dist = math.sqrt((x - center) ** 2 + (y - center) ** 2) * scale

        if dist > DartboardGeometry.RADIEN["double_outer"]:
            return "Miss"
        if dist <= DartboardGeometry.RADIEN["bullseye"]:
            return "Bullseye"
        # FIX: Add check for Bull, which was previously missed.
        if dist <= DartboardGeometry.RADIEN["bull"]:
            return "Bull"

        # atan2 gibt Winkel gegen den Uhrzeigersinn (CCW) zurück.
        # Da unsere SEGMENTS-Liste im Uhrzeigersinn (CW) bei 3 Uhr (0°) startet,
        # müssen wir den Winkel invertieren, um den korrekten Index zu finden.
        angle_ccw = (math.degrees(math.atan2(center - y, x - center)) + 360) % 360
        idx = int((360 - angle_ccw + 9) // 18) % 20
        return str(DartboardGeometry.SEGMENTS[idx])

    @staticmethod
    def get_target_coords(target_name: str) -> tuple[int, int] | None:
        """
        Berechnet die Mittelpunkt-Koordinaten für ein gegebenes Ziel (z.B. "T20", "D18", "BE").
        Diese Methode ist nun datengesteuert, um die Lesbarkeit und Wartbarkeit zu verbessern.

        Args:
            target_name (str): Der Name des Ziels.

        Returns:
            tuple[int, int] or None: Die (x, y)-Koordinaten des Ziels oder None bei ungültigem Ziel.
        """
        target_name = target_name.upper().strip()

        # For both Bull and Bullseye, the geometric aiming point is the center of the board.
        if target_name in ("BE", "B"):
            return (DartboardGeometry.CENTER, DartboardGeometry.CENTER)

        try:
            ring_char = target_name[0]
            segment = int(target_name[1:])
            segment_index = DartboardGeometry.SEGMENTS.index(segment)
        except (ValueError, IndexError):
            return None  # Ungültiges Format oder Segment nicht gefunden

        # Winkel zur Mitte des Segments berechnen.
        # Die SEGMENTS-Liste ist im Uhrzeigersinn definiert. Mathematische Winkel
        # (und atan2) verlaufen jedoch gegen den Uhrzeigersinn. Um dies zu korrigieren, muss
        # der Winkel negativ sein, um im Uhrzeigersinn zu laufen.
        angle_deg = -(segment_index * 18)

        # Datengesteuerte Radienberechnung
        radius_keys_map = {
            "T": ("triple_inner", "triple_outer"),
            "D": ("double_inner", "double_outer"),
            "S": (
                "bull",
                "triple_inner",
            ),  # Für 'S' zielen wir immer auf das große innere Feld
        }
        if ring_char not in radius_keys_map:
            return None  # Ungültiger Ring

        inner_key, outer_key = radius_keys_map[ring_char]
        radius = (DartboardGeometry.RADIEN[inner_key] + DartboardGeometry.RADIEN[outer_key]) / 2

        return DartboardGeometry._polar_to_cartesian(radius, angle_deg)

    @staticmethod
    def _polar_to_cartesian(radius: float, angle_deg: float) -> tuple[int, int]:
        """
        Konvertiert Polarkoordinaten (mathematischer Standard: 0 Grad rechts,
        gegen den Uhrzeigersinn) in kartesische Tkinter-Canvas-Koordinaten.
        """
        angle_rad = math.radians(angle_deg)
        x = int(DartboardGeometry.CENTER + radius * math.cos(angle_rad))
        y = int(DartboardGeometry.CENTER - radius * math.sin(angle_rad))  # Y-Achse ist invertiert
        return (x, y)

    @staticmethod
    def get_target_coords_scaled(ring: str, segment: int, canvas, skaliert: dict) -> tuple[int, int] | None:
        """
        Ermittelt die (x, y)-Koordinaten für ein Ziel auf einem skalierten Board-Bild.
        Berechnet das Zentrum basierend auf der Canvas-Größe und den Board-Offsets.

        Args:
            ring (str): Der Zielring.
            segment (int): Das Zielsegment.
            canvas (tk.Canvas): Das Canvas-Widget (für die aktuelle Größe).
            skaliert (dict): Die bereits skalierten Radien.
        """
        if not skaliert or not canvas:
            return None

        # Bestimme die aktuelle Skalierung relativ zum Original
        scale = skaliert["outer_edge"] / DartboardGeometry.RADIEN["outer_edge"]

        # Berechne das Zentrum (muss exakt mit DartBoard.BOARD_CENTER_OFFSET übereinstimmen)
        # Offsets: X=-8, Y=-7
        center_x = (canvas.winfo_width() // 2) + int(-8 * scale)
        center_y = (canvas.winfo_height() // 2) + int(-7 * scale)

        # Sonderfall Bullseye/Bull (beide zielen auf die absolute Mitte)
        if ring in ("Bullseye", "Bull"):
            return int(center_x), int(center_y)

        try:
            seg_val = int(segment)
            segment_index = DartboardGeometry.SEGMENTS.index(seg_val)
        except (ValueError, IndexError, TypeError):
            return None

        # Winkel berechnen (0 Grad ist rechts bei der 6)
        angle_deg = -(segment_index * 18)

        # Radien-Mapping für die skalierten Werte
        radius_keys_map = {
            "Triple": ("triple_inner", "triple_outer"),
            "Double": ("double_inner", "double_outer"),
            "Single": ("bull", "triple_inner"),
        }

        if ring not in radius_keys_map:
            return None

        inner_key, outer_key = radius_keys_map[ring]
        radius = (skaliert[inner_key] + skaliert[outer_key]) / 2

        # Umrechnung in kartesische Koordinaten mit dem skalierten Zentrum
        angle_rad = math.radians(angle_deg)
        x = int(center_x + radius * math.cos(angle_rad))
        y = int(center_y - radius * math.sin(angle_rad))
        return x, y
