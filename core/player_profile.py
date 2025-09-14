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
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PlayerProfile:
    """
    Repräsentiert ein persistentes Spielerprofil mit Namen und Avatar.
    Verwendet dataclass für eine saubere und typsichere Attributdefinition.
    """

    name: str
    profile_id: Optional[int] = None
    avatar_path: Optional[str] = None
    dart_color: str = "#ff0000"
    is_ai: bool = False
    difficulty: Optional[str] = None
    preferred_double: Optional[int] = None
    accuracy_model: Optional[dict] = field(default=None, repr=False)

    # Das 'id'-Attribut wird als Property hinzugefügt, um die Abwärtskompatibilität
    # mit Teilen des Codes zu gewährleisten, die möglicherweise noch `profile.id` verwenden.
    @property
    def id(self):
        return self.profile_id

    def to_dict(self) -> dict:
        """Serialisiert das Profil in ein Dictionary."""
        return {
            "id": self.profile_id,
            "name": self.name,
            "avatar_path": self.avatar_path,
            "dart_color": self.dart_color,
            "is_ai": self.is_ai,
            "difficulty": self.difficulty,
            "preferred_double": self.preferred_double,
            "accuracy_model": self.accuracy_model,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Erstellt ein Profil aus einem Dictionary."""
        return cls(
            profile_id=data.get("id"),  # Behält 'id' für Abwärtskompatibilität beim Laden
            name=data["name"],
            avatar_path=data.get("avatar_path"),
            dart_color=data.get("dart_color", "#ff0000"),  # Fallback für alte Profile
            is_ai=data.get("is_ai", False),
            difficulty=data.get("difficulty", None),
            preferred_double=data.get("preferred_double", None),
            accuracy_model=data.get("accuracy_model", None),
        )

    @classmethod
    def from_orm(cls, orm_profile):
        """
        Erstellt eine PlayerProfile-Datenklasse aus einem SQLAlchemy ORM-Objekt.
        Dies entkoppelt die Anwendungslogik von der Datenbankschicht.

        Args:
            orm_profile: Eine Instanz des SQLAlchemy-Modells `db_models.PlayerProfileORM`.

        Returns:
            Eine Instanz der `core.player_profile.PlayerProfile`-Datenklasse.
        """
        return cls(
            profile_id=orm_profile.id,
            name=orm_profile.name,
            avatar_path=orm_profile.avatar_path,
            dart_color=orm_profile.dart_color,
            is_ai=orm_profile.is_ai,
            difficulty=orm_profile.difficulty,
            preferred_double=orm_profile.preferred_double,
            accuracy_model=orm_profile.accuracy_model,
        )
