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
        """Initialisiert den Manager mit einer Referenz auf den DatabaseManager."""
        self.db_manager = db_manager

    def _load_profiles_from_db(self) -> list[PlayerProfile]:
        """Lädt die Profile aus der Datenbank."""
        # Die Prüfung auf `is_connected` wurde entfernt. Der DatabaseManager selbst
        # ist so konzipiert, dass er bei fehlender Verbindung sicher eine leere Liste
        # zurückgibt. Dies macht den Manager robuster gegenüber initialen Verbindungsfehlern.
        # Lade die ORM-Objekte aus der Datenbank.
        orm_profiles = self.db_manager.get_all_profiles()
        # Konvertiere jedes ORM-Objekt in eine PlayerProfile-Datenklasse.
        # Dies entkoppelt die Anwendungslogik von der Datenbankschicht.
        return [PlayerProfile.from_orm(p) for p in orm_profiles]

    def get_profiles(self) -> list[PlayerProfile]:
        """Gibt eine Liste aller geladenen Profile zurück."""
        # Lädt die Profile bei jedem Aufruf frisch aus der Datenbank.
        # Dies stellt sicher, dass die Daten immer aktuell sind und vermeidet
        # Initialisierungsprobleme.
        return self._load_profiles_from_db()

    def get_profile_by_name(self, name: str) -> PlayerProfile | None:
        """Sucht und gibt ein Profil anhand seines Namens zurück."""
        # Nutzt get_profiles(), um auf die aktuellen Daten zuzugreifen.
        profiles = self.get_profiles()
        return next((p for p in profiles if p.name == name), None)

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
            bool: True bei Erfolg, False wenn der neue Name bereits von einem anderen Profil verwendet wird. # noqa: E501
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

        return success

    def delete_profile_by_id(self, profile_id: int) -> bool:
        """
        Löscht ein Profil anhand seiner ID.

        Returns:
            bool: True bei Erfolg, False wenn kein Profil mit der ID gefunden wurde.
        """
        success = self.db_manager.delete_profile_by_id(profile_id)
        return success

    def delete_profile(self, profile_name: str) -> bool:
        """
        Löscht ein Profil anhand seines Namens.

        Returns:
            bool: True bei Erfolg, False wenn kein Profil mit dem Namen gefunden wurde.
        """
        success = self.db_manager.delete_profile(profile_name)
        return success
