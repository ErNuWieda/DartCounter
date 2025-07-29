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

from .checkout_calculator import CHECKOUT_PATHS, CheckoutCalculator
from .dartboard_geometry import DartboardGeometry

class AILogic:
    """
    Das "Gehirn" des KI-Spielers. Bestimmt das strategisch beste Ziel
    basierend auf dem aktuellen Spielzustand.
    """
    def __init__(self, game_logic):
        self.game_logic = game_logic
        self.geometry = DartboardGeometry()
        # Ein Set mit allen Scores, für die es einen bekannten Checkout-Pfad gibt.
        # Dies sind die idealen Restpunktzahlen, die die KI anstreben sollte.
        self.PREFERRED_LEAVES = set(CHECKOUT_PATHS.keys())
        # Füge weitere gängige und gute "Leave"-Scores hinzu
        self.PREFERRED_LEAVES.update([32, 40, 50, 60, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 34, 36, 38])

    def determine_target(self, player) -> tuple[int, int]:
        """
        Hauptmethode zur Bestimmung des Ziels. Delegiert an spielspezifische Logik.
        """
        if self.game_logic.game.name in ("301", "501", "701"):
            return self._determine_target_for_x01(player)

        # Fallback für andere Spielmodi (z.B. immer auf T20 zielen)
        return self.geometry.get_target_coords("T20")

    def _determine_setup_target(self, current_score: int) -> str:
        """
        Bestimmt das beste Setup-Ziel, wenn kein direkter Checkout möglich ist.
        Die KI versucht, einen Rest zu hinterlassen, der ein bekanntes Finish ist.
        """
        # Bevorzugte Ziele, geordnet nach Punktwert
        targets_to_try = {
            "T20": 60, "T19": 57, "T18": 54, "T17": 51, "T16": 48, "T15": 45,
            "S20": 20, "S19": 19, "S18": 18, "BE": 25
        }

        # Finde den besten Wurf, der einen bevorzugten Rest hinterlässt
        for target_name, target_score in targets_to_try.items():
            # Ein Setup-Wurf darf niemals überwerfen (muss mind. 2 Rest lassen für D1)
            if current_score - target_score >= 2:
                if (current_score - target_score) in self.PREFERRED_LEAVES:
                    return target_name

        # Fallback: Wenn kein bevorzugter Rest erreicht werden kann, ziele auf
        # die höchste Punktzahl, die nicht überwirft.
        return "T20" if current_score > 61 else "S20"

    def _determine_target_for_x01(self, player) -> tuple[int, int]:
        """Bestimmt das Ziel für ein X01-Spiel."""
        score = player.score
        darts_left = 3 - len(player.throws)

        # Versuche, einen Checkout-Pfad zu finden
        suggestion = CheckoutCalculator.get_checkout_suggestion(
            score, self.game_logic.opt_out, darts_left
        )

        if suggestion != "-":
            # Es gibt einen direkten Checkout-Pfad, folge ihm.
            first_target = suggestion.split()[0]
            if first_target.isdigit():
                target_segment_name = f"S{first_target}"
            elif first_target == "BE":
                target_segment_name = "BE" # Bullseye
            else: # T20, D18 etc.
                target_segment_name = first_target
        else:
            # Kein direkter Checkout: Finde den besten Setup-Wurf.
            target_segment_name = self._determine_setup_target(score)

        return self.geometry.get_target_coords(target_segment_name)