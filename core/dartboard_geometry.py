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
    def get_segment_from_coords(x: float, y: float) -> int:
        """
        Ermittelt das getroffene Segment basierend auf unskalierten Koordinaten.
        Dies ist die UI-unabhängige Kernlogik von DartBoard.get_ring_segment.

        Args:
            x (float): Die x-Koordinate auf dem Original-Board.
            y (float): Die y-Koordinate auf dem Original-Board.

        Returns:
            int: Der Zahlenwert des getroffenen Segments.
        """
        angle = (math.degrees(math.atan2(DartboardGeometry.CENTER - y, x - DartboardGeometry.CENTER)) + 360) % 360
        idx = int((angle + 9) // 18) % 20
        return DartboardGeometry.SEGMENTS[idx]
    @staticmethod
    def get_target_coords(target_name: str) -> tuple[int, int]:
        """
        Berechnet die Mittelpunkt-Koordinaten für ein gegebenes Ziel (z.B. "T20", "D18", "BE").

        Args:
            target_name (str): Der Name des Ziels.

        Returns:
            tuple[int, int]: Die (x, y)-Koordinaten des Ziels auf dem Original-Board.
        """
        if target_name == "BE": return (DartboardGeometry.CENTER, DartboardGeometry.CENTER)
        if target_name == "B":
            radius = (DartboardGeometry.RADIEN["bullseye"] + DartboardGeometry.RADIEN["bull"]) / 2
            return DartboardGeometry._polar_to_cartesian(radius, 0) # Winkel ist irrelevant

        ring_char = target_name[0]
        segment = int(target_name[1:])

        try:
            segment_index = DartboardGeometry.SEGMENTS.index(segment)
        except ValueError:
            return (DartboardGeometry.CENTER, DartboardGeometry.CENTER) # Fallback

        # Jeder Sektor ist 18 Grad breit. Der Winkel wird zur Mitte des Sektors berechnet.
        # Wir starten bei 9 Grad (Mitte der 6) und subtrahieren für jedes weitere Segment 18 Grad.
        angle_deg = 9 - (segment_index * 18)

        radius = 0
        if ring_char == 'T':
            radius = (DartboardGeometry.RADIEN["triple_inner"] + DartboardGeometry.RADIEN["triple_outer"]) / 2
        elif ring_char == 'D':
            radius = (DartboardGeometry.RADIEN["double_inner"] + DartboardGeometry.RADIEN["double_outer"]) / 2
        elif ring_char == 'S':
            # Unterscheide zwischen großem und kleinem Single-Feld
            if segment_index % 2 == 0: # Annahme: Große Felder bei geraden Indizes
                radius = (DartboardGeometry.RADIEN["bull"] + DartboardGeometry.RADIEN["triple_inner"]) / 2
            else:
                radius = (DartboardGeometry.RADIEN["triple_outer"] + DartboardGeometry.RADIEN["double_inner"]) / 2

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