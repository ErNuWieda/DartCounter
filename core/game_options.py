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

from dataclasses import dataclass, asdict


@dataclass
class GameOptions:
    """Eine Datenklasse, die alle statischen Einstellungen für eine Spielsitzung enthält."""

    name: str
    opt_in: str
    opt_out: str
    opt_atc: str
    count_to: int
    lifes: int
    rounds: int
    legs_to_win: int
    sets_to_win: int
    opt_split_score_target: int = 60

    @classmethod
    def from_dict(cls, data: dict):
        """Erstellt eine GameOptions-Instanz aus einem Dictionary."""
        # Filtere das Dictionary, um nur Schlüssel zu behalten, die auch Felder der
        # Datenklasse sind. Verhindert TypeErrors bei zusätzlichen Schlüsseln.
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in field_names}

        # Konvertiere numerische Felder explizit zu Integers, da UI-Elemente
        # oder JSON-Ladevorgänge Strings liefern können.
        for field in [
            "count_to",
            "lifes",
            "rounds",
            "legs_to_win",
            "sets_to_win",
            "opt_split_score_target",
        ]:
            if field in filtered_data:
                try:
                    # Stellt sicher, dass der Wert zu einem Integer konvertiert wird,
                    # behandelt sowohl Strings ('301') als auch Integers (301).
                    filtered_data[field] = int(filtered_data[field])
                except (ValueError, TypeError):
                    # Fallback für ungültige Werte (z.B. leere Strings)
                    # Setze auf einen sicheren Standardwert, um Abstürze zu vermeiden.
                    if field == "count_to":
                        filtered_data[field] = 301
                    if field == "lifes":
                        filtered_data[field] = 3
                    if field == "rounds":
                        filtered_data[field] = 7
                    if field == "legs_to_win":
                        filtered_data[field] = 1
                    if field == "sets_to_win":
                        filtered_data[field] = 1
                    if field == "opt_split_score_target":
                        filtered_data[field] = 60
                    if field == "opt_split_score_target":
                        filtered_data[field] = 60

        return cls(**filtered_data)

    def to_dict(self) -> dict:
        """Konvertiert die GameOptions-Instanz in ein Dictionary zur Serialisierung."""
        return asdict(self)
