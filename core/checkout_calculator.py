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

"""
Dieses Modul enthält die Logik zur Berechnung von Finish-Wegen für x01-Spiele.
"""
import json
import pathlib
import sys

def _load_checkout_paths():
    """Lädt die Checkout-Pfade aus der JSON-Datei."""
    try:
        # Pfad zur JSON-Datei relativ zu dieser Datei bestimmen
        base_path = pathlib.Path(__file__).resolve().parent
        json_path = base_path / "checkout_paths.json"
        with open(json_path, 'r', encoding='utf-8') as f:
            # JSON-Schlüssel sind Strings, wir brauchen Integer-Schlüssel
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Fehler beim Laden der Checkout-Pfade: {e}")
        return {}

# Die Checkout-Pfade werden nur einmal beim Import des Moduls geladen.
CHECKOUT_PATHS = _load_checkout_paths()

class CheckoutCalculator:
    """
    Eine Utility-Klasse zur Berechnung von Finish-Wegen für X01-Spiele.
    """
    @staticmethod
    def get_checkout_suggestion(score, opt_out="Double", darts_left=3):
        """
        Gibt einen Finish-Vorschlag für einen gegebenen Punktestand zurück.

        Args:
            score (int): Der aktuelle Punktestand des Spielers.
            opt_out (str): Die "Opt-Out"-Regel des Spiels.
            darts_left (int): Die Anzahl der verbleibenden Darts (3 oder 2).

        Returns:
            str: Ein String mit dem Finish-Vorschlag oder "-".
        """
        # Kein Finish möglich mit 3 Darts über 170 oder mit 2 Darts über 110
        if (darts_left == 3 and score > 170) or \
           (darts_left == 2 and score > 110) or \
           score < 2:
            return "-"

        # Kein Finish möglich, wenn der Score ungerade und kleiner als das höchste Single-Finish ist
        if darts_left == 2 and score < 41 and score % 2 != 0:
            return "-"

        # Für "Double Out" oder "Masters Out"
        if opt_out in ("Double", "Masters"):
            return CHECKOUT_PATHS.get(score, "-")

        # Für "Single Out" (einfachster Fall)
        if score <= 40 and score % 2 == 0:
            return f"D{score // 2}"
        if score <= 20:
            return f"{score}"
        if score <= 60:
            return f"T{score // 3} Rest {score % 3}" if score % 3 == 0 else f"20 D{(score - 20) // 2}"

        return CHECKOUT_PATHS.get(score, "-") # Fallback auf die Standard-Pfade
