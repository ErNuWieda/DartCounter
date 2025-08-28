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
        "bullseye": 30, "bull": 80, "triple_inner": 470, "triple_outer": 520,
        "double_inner": 785, "double_outer": 835, "outer_edge": 836
    }
    # Segmente im Uhrzeigersinn, beginnend bei der "6" oben rechts
    SEGMENTS = [6, 13, 4, 18, 1, 20, 5, 12, 9, 14, 11, 8, 16, 7, 19, 3, 17, 2, 15, 10]

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
        dist = math.sqrt((x - center)**2 + (y - center)**2) * scale

        if dist > DartboardGeometry.RADIEN["double_outer"]:
            return "Miss"
        if dist <= DartboardGeometry.RADIEN["bullseye"]:
            return "Bullseye"
        # FIX: Add check for Bull, which was previously missed.
        if dist <= DartboardGeometry.RADIEN["bull"]:
            return "Bull"

        angle = (math.degrees(math.atan2(center - y, x - center)) + 360) % 360
        idx = int((angle + 9) // 18) % 20
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
            return None # Ungültiges Format oder Segment nicht gefunden

        # Winkel zur Mitte des Segments berechnen
        # Start bei 9 Grad (Mitte der 6) und Subtraktion von 18 Grad pro Segment
        angle_deg = 9 - (segment_index * 18)

        # Datengesteuerte Radienberechnung
        radius_keys_map = {
            'T': ("triple_inner", "triple_outer"),
            'D': ("double_inner", "double_outer"),
            'S': ("bull", "triple_inner") # Für 'S' zielen wir immer auf das große innere Feld
        }
        if ring_char not in radius_keys_map:
            return None # Ungültiger Ring

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
        y = int(DartboardGeometry.CENTER - radius * math.sin(angle_rad)) # Y-Achse ist invertiert
        return (x, y)