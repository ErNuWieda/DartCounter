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

from PIL import Image, ImageDraw
import pathlib

class HeatmapGenerator:
    """
    Eine statische Utility-Klasse zur Erstellung von Heatmap-Bildern.
    """
    ASSETS_BASE_DIR = pathlib.Path(__file__).resolve().parent.parent / "assets"
    DARTBOARD_PATH = ASSETS_BASE_DIR / "dartboard.png"
    
    @staticmethod
    def create_heatmap(coordinates: list[tuple[float, float]], point_radius=10, point_opacity=128):
        """
        Erstellt ein Heatmap-Bild, indem Wurfkoordinaten auf ein Dartboard-Bild gezeichnet werden.

        Args:
            coordinates (list[tuple[float, float]]): Eine Liste von normalisierten (x, y)-Koordinaten.
            point_radius (int): Der Radius der gezeichneten Punkte.
            point_opacity (int): Die Deckkraft der Punkte (0-255).

        Returns:
            PIL.Image.Image or None: Das generierte Heatmap-Bild oder None bei einem Fehler.
        """
        try:
            board_img = Image.open(HeatmapGenerator.DARTBOARD_PATH).convert("RGBA")
        except FileNotFoundError:
            print(f"Fehler: Dartboard-Bild nicht gefunden unter {HeatmapGenerator.DARTBOARD_PATH}")
            return None

        width, height = board_img.size
        overlay = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        point_color = (255, 0, 0, point_opacity) # Halbtransparentes Rot
        for norm_x, norm_y in coordinates:
            abs_x, abs_y = int(norm_x * width), int(norm_y * height)
            draw.ellipse((abs_x - point_radius, abs_y - point_radius, abs_x + point_radius, abs_y + point_radius), fill=point_color)
        
        combined_img = Image.alpha_composite(board_img, overlay)
        return combined_img.convert("RGB") # Konvertiere zu RGB für Tkinter