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
import pathlib
from .json_io_handler import JsonIOHandler

def _load_checkout_paths():
    """
    Lädt die Checkout-Pfade aus der JSON-Datei und konvertiert Schlüssel zu Integers.
    Ist robust gegenüber fehlerhaften Einträgen in der JSON-Datei.
    """
    base_path = pathlib.Path(__file__).resolve().parent
    json_path = base_path / "checkout_paths.json"
    
    data = JsonIOHandler.read_json(json_path)
    if not data:
        return {}
        
    checkout_map = {}
    for key, value in data.items():
        try:
            # JSON-Schlüssel sind Strings, wir brauchen Integer-Schlüssel
            score = int(key)
            # Der Wert kann ein String oder eine Liste sein, beides ist ok.
            checkout_map[score] = value
        except (ValueError, TypeError):
            # Ignoriere Einträge, bei denen der Schlüssel keine gültige Zahl ist.
            # logging.warning(f"Ungültiger Schlüssel '{key}' in checkout_paths.json wird ignoriert.")
            pass
    return checkout_map

# Die Checkout-Pfade werden nur einmal beim Import des Moduls geladen.
CHECKOUT_PATHS = _load_checkout_paths()

# Eine vorberechnete Map der bestmöglichen Single-Dart-Finishes.
# Die Reihenfolge der Erstellung ist wichtig, da sie die Priorität bestimmt
# (z.B. T20 für 60). Bullseye (BE) wird zuletzt gesetzt, um alles andere zu überschreiben.
_SINGLE_DART_FINISH_MAP = {}
# Singles (niedrigste Priorität)
for i in range(1, 21): _SINGLE_DART_FINISH_MAP[i] = f"{i}"
_SINGLE_DART_FINISH_MAP[25] = "25"
# Doubles
for i in range(1, 21): _SINGLE_DART_FINISH_MAP[i * 2] = f"D{i}"
# Triples
for i in range(1, 21): _SINGLE_DART_FINISH_MAP[i * 3] = f"T{i}"
# Bullseye (höchste Priorität)
_SINGLE_DART_FINISH_MAP[50] = "BE"
# Unmögliche Single-Dart-Finishes explizit entfernen, um die Logik zu 100% abzubilden
for score in [59, 58, 56, 55, 53, 52, 49, 47, 46, 44, 43, 41]:
    _SINGLE_DART_FINISH_MAP.pop(score, None)

# Geordnete Liste der Würfe von hoch nach niedrig, als Klassenkonstante definiert,
# um eine Neuerstellung bei jedem Aufruf von _get_two_dart_setup zu vermeiden.
_ORDERED_THROWS = (
    [(f"T{i}", i * 3) for i in range(20, 0, -1)] +
    [("BE", 50)] +
    [(f"D{i}", i * 2) for i in range(20, 0, -1)] +
    [("25", 25)] +
    [(f"{i}", i) for i in range(20, 0, -1)]
)

def _get_single_dart_throw(score: int) -> str | None:
    """
    Ermittelt den besten Wurf, um einen Score mit einem einzelnen Dart zu erzielen,
    indem eine vorberechnete Map für einen schnellen Lookup verwendet wird.
    Gibt None zurück, wenn der Score nicht mit einem einzelnen Dart machbar ist.
    """
    return _SINGLE_DART_FINISH_MAP.get(score)

def _get_two_dart_setup(score: int) -> tuple[str, str] | None:
    """
    Ermittelt den besten Zwei-Dart-Weg, um einen Setup-Score zu erzielen.
    Priorisiert hohe Würfe, um den Rest schnell zu reduzieren.
    """
    # Nutze die vordefinierte Klassenkonstante
    for first_throw_str, first_throw_score in _ORDERED_THROWS:
        if first_throw_score <= score:
            remainder = score - first_throw_score
            second_throw_str = _get_single_dart_throw(remainder)
            if second_throw_str:
                return first_throw_str, second_throw_str
    return None

class CheckoutCalculator:
    """
    Eine Utility-Klasse zur Berechnung von Finish-Wegen für X01-Spiele.
    Nutzt eine Hybrid-Strategie: Berechnet zuerst einen Weg zum bevorzugten Double,
    greift andernfalls auf eine kuratierte Liste von Standard-Finishwegen zurück.
    """
    @staticmethod
    def _calculate_path_for_preferred_double(score: int, darts_left: int, preferred_double: int) -> str | None:
        """Berechnet einen Checkout-Pfad, der auf dem bevorzugten Double endet."""
        double_value = 50 if preferred_double == 25 else preferred_double * 2
        double_str = "BE" if preferred_double == 25 else f"D{preferred_double}"

        setup_score = score - double_value

        if setup_score < 0:
            return None

        # 1-Dart-Finish (nur das Double)
        if darts_left >= 1 and setup_score == 0:
            return double_str

        # 2-Dart-Finish (1 Setup-Dart + Double)
        if darts_left >= 2:
            setup_throw = _get_single_dart_throw(setup_score)
            if setup_throw:
                return f"{setup_throw}, {double_str}"

        # 3-Dart-Finish (2 Setup-Darts + Double)
        if darts_left >= 3:
            setup_throws = _get_two_dart_setup(setup_score)
            if setup_throws:
                return f"{setup_throws[0]}, {setup_throws[1]}, {double_str}"

        return None

    @staticmethod
    def get_checkout_suggestion(score, opt_out="Double", darts_left=3, preferred_double: int | None = None):
        """
        Gibt einen Finish-Vorschlag für einen gegebenen Punktestand zurück.
        Nutzt eine Hybrid-Strategie: Berechnet zuerst einen Weg zum bevorzugten Double,
        greift andernfalls auf eine kuratierte Liste von Standard-Finishwegen zurück.

        Args:
            score (int): Der aktuelle Punktestand des Spielers.
            opt_out (str): Die "Opt-Out"-Regel des Spiels.
            darts_left (int): Die Anzahl der verbleibenden Darts (3, 2 oder 1).
            preferred_double (int, optional): Das bevorzugte Double-Out (z.B. 16, 20, 25 für Bull).

        Returns:
            str: Ein String mit dem Finish-Vorschlag oder "-".
        """
        # --- Vorab-Prüfungen auf unmögliche Finishes ---
        if score < 2:
            return "-"
        
        # Bogey-Nummern (nicht finishbar mit 3 Darts)
        if darts_left == 3 and score in (169, 168, 166, 165, 163, 162, 159):
            return "-"

        # Maximale Finish-Scores pro Dart-Anzahl
        if (darts_left == 3 and score > 170) or \
           (darts_left == 2 and score > 110): # 1-Dart-Finish wird separat geprüft
            return "-"
        if darts_left == 1 and opt_out in ("Double", "Masters") and (score > 50 or (score % 2 != 0 and score != 25)):
            return "-"

        # Für "Single Out" (einfachster Fall)
        if opt_out == "Single":
            # Prüfe von der besten (1 Dart) zur schlechtesten (3 Darts) Option
            if darts_left >= 1:
                if path := _get_single_dart_throw(score): return path
            if darts_left >= 2:
                if path_tuple := _get_two_dart_setup(score): return f"{path_tuple[0]}, {path_tuple[1]}"
            if darts_left >= 3:
                path = CHECKOUT_PATHS.get(score)
                if isinstance(path, list): path = path[0]
                if path: return path.replace(" ", ", ")
            return "-"

        # --- Logik für "Double Out" / "Masters Out" ---
        if opt_out in ("Double", "Masters"):
            # 1. Priorität: Versuche, einen Pfad für das bevorzugte Double zu BERECHNEN
            if preferred_double:
                calculated_path = CheckoutCalculator._calculate_path_for_preferred_double(score, darts_left, preferred_double)
                if calculated_path:
                    return calculated_path # Ist bereits komma-separiert

            # 2. Fallback: Suche in den Standard-Pfaden (JSON)
            possible_paths_raw = CHECKOUT_PATHS.get(score)
            if not possible_paths_raw:
                return "-"

            possible_paths = [possible_paths_raw] if isinstance(possible_paths_raw, str) else possible_paths_raw
            
            def count_darts(path_str: str) -> int:
                return len(path_str.split())

            # Suche nach einem Pfad, der zum (möglicherweise anderen) bevorzugten Double passt
            if preferred_double:
                target_double_str = "BE" if preferred_double == 25 else f"D{preferred_double}"
                for path in possible_paths:
                    if path.endswith(target_double_str) and count_darts(path) <= darts_left:
                        return path.replace(" ", ", ")

            # Nimm den Standardpfad, wenn er spielbar ist
            default_path = possible_paths[0]
            if count_darts(default_path) <= darts_left:
                return default_path.replace(" ", ", ")

        return "-"
