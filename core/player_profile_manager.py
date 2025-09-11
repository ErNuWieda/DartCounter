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

from .database_manager import DatabaseManager
from .player_profile import PlayerProfile


class PlayerProfileManager:
    """
    Verwaltet das Laden, Speichern und den Zugriff auf Spielerprofile.
    Interagiert jetzt mit dem DatabaseManager statt mit einer JSON-Datei.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.profiles = self._load_profiles_from_db()

    def reload_profiles(self):
        """Erzwingt ein Neuladen aller Profile aus der Datenbank."""
        self.profiles = self._load_profiles_from_db()

    def _load_profiles_from_db(self) -> list[PlayerProfile]:
        """Lädt die Profile aus der Datenbank."""
        if not self.db_manager.is_connected:
            return []

        profiles_data = self.db_manager.get_all_profiles()
        return [PlayerProfile.from_dict(p_data) for p_data in profiles_data]

    def get_profiles(self) -> list[PlayerProfile]:
        """Gibt eine Liste aller geladenen Profile zurück."""
        return self.profiles

    def get_profile_by_name(self, name: str) -> PlayerProfile | None:
        """Sucht und gibt ein Profil anhand seines Namens zurück."""
        return next((p for p in self.profiles if p.name == name), None)

    def add_profile(
        self,
        name: str,
        avatar_path: str,
        dart_color: str,
        is_ai: bool = False,
        difficulty: str = None,
        preferred_double: int = None,
        accuracy_model: dict | None = None,
    ) -> bool:
        """
        Fügt ein neues Profil hinzu, wenn der Name noch nicht existiert.

        Returns:
            bool: True bei Erfolg, False wenn der Name bereits vergeben ist.
        """
        success = self.db_manager.add_profile(
            name,
            avatar_path,
            dart_color,
            is_ai,
            difficulty,
            preferred_double,
            accuracy_model,
        )
        if success:
            self.profiles = self._load_profiles_from_db()  # Liste neu laden
        return success

    def update_profile(
        self,
        profile_id: int,
        new_name: str,
        new_avatar_path: str,
        new_dart_color: str,
        is_ai: bool = False,
        difficulty: str = None,
        preferred_double: int = None,
        accuracy_model: dict | None = None,
    ) -> bool:
        """
        Aktualisiert ein bestehendes Profil.

        Args:
            profile_id (int): Die ID des zu aktualisierenden Profils.
            new_name (str): Der (potenziell neue) Name.
            new_avatar_path (str): Der (potenziell neue) Pfad zum Avatar.
            new_dart_color (str): Die (potenziell neue) Farbe für den Dart.

        Returns:
            bool: True bei Erfolg, False wenn der neue Name bereits von einem anderen Profil verwendet wird.
        """
        success = self.db_manager.update_profile(
            profile_id,
            new_name,
            new_avatar_path,
            new_dart_color,
            is_ai,
            difficulty,
            preferred_double,
            accuracy_model,
        )
        if success:
            # Finde das Profil in der lokalen Liste und aktualisiere es, um einen Neuladevorgang zu vermeiden
            profile_to_update = next(
                (p for p in self.profiles if p.id == profile_id), None
            )
            if profile_to_update:
                profile_to_update.name = new_name
                profile_to_update.avatar_path = new_avatar_path
                profile_to_update.dart_color = new_dart_color
                profile_to_update.is_ai = is_ai
                profile_to_update.difficulty = difficulty
                profile_to_update.preferred_double = preferred_double
                profile_to_update.accuracy_model = accuracy_model

        return success

    def delete_profile(self, profile_name: str) -> bool:
        """
        Löscht ein Profil anhand seines Namens.

        Returns:
            bool: True bei Erfolg, False wenn kein Profil mit dem Namen gefunden wurde.
        """
        success = self.db_manager.delete_profile(profile_name)
        if success:
            self.profiles = [p for p in self.profiles if p.name != profile_name]
        return success
