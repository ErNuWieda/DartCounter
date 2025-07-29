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
Dieses Modul enthält die PlayerProfile-Klasse, die persistente Spielerdaten verwaltet.
"""

class PlayerProfile:
    """
    Repräsentiert ein persistentes Spielerprofil mit Namen und Avatar.
    """
    def __init__(self, name: str, avatar_path: str = None, dart_color: str = "#ff0000", is_ai: bool = False, difficulty: str = None, profile_id: int = None):
        """
        Initialisiert ein neues Spielerprofil.

        Args:
            name (str): Der eindeutige Name des Spielers.
            avatar_path (str, optional): Der Dateipfad zum Avatarbild. Defaults to None.
            dart_color (str, optional): Die Hex-Farbe für die Dart-Grafik. Defaults to "#ff0000" (rot).
            profile_id (int, optional): Die ID aus der Datenbank. Defaults to None.
        """
        self.name = name
        self.avatar_path = avatar_path
        self.dart_color = dart_color
        self.is_ai = is_ai
        self.difficulty = difficulty
        self.id = profile_id

    def to_dict(self) -> dict:
        """Serialisiert das Profil in ein Dictionary."""
        return {'id': self.id, 'name': self.name, 'avatar_path': self.avatar_path, 'dart_color': self.dart_color, 'is_ai': self.is_ai, 'difficulty': self.difficulty}

    @classmethod
    def from_dict(cls, data: dict):
        """Erstellt ein Profil aus einem Dictionary."""
        return cls(
            profile_id=data.get('id'),
            name=data['name'],
            avatar_path=data.get('avatar_path'),
            dart_color=data.get('dart_color', "#ff0000"), # Fallback für alte Profile
            is_ai=data.get('is_ai', False),
            difficulty=data.get('difficulty', None)
        )