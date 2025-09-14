import pytest
from unittest.mock import MagicMock
from core.db_models import PlayerProfileORM

from core.player_profile_manager import PlayerProfileManager
from core.player_profile import PlayerProfile


@pytest.fixture
def mock_db_manager():
    """Fixture für einen gemockten DatabaseManager."""
    db_manager = MagicMock()
    db_manager.get_all_profiles.return_value = []
    return db_manager


class TestPlayerProfileManager:
    """Testet den PlayerProfileManager."""

    def test_init_loads_profiles_from_db(self, mock_db_manager):
        """Testet, dass get_profiles() die Profile aus der DB lädt und konvertiert."""
        # Erstelle Mock ORM-Objekte, die von der DB zurückgegeben werden
        mock_orm_profile1 = PlayerProfileORM(
            id=1, name="Alice", avatar_path="a.png", dart_color="#ff0000", is_ai=False
        )
        mock_orm_profile2 = PlayerProfileORM(
            id=2, name="Bob", avatar_path=None, dart_color="#00ff00", is_ai=False
        )
        mock_db_manager.get_all_profiles.return_value = [mock_orm_profile1, mock_orm_profile2]

        manager = PlayerProfileManager(mock_db_manager)
        profiles = manager.get_profiles()

        mock_db_manager.get_all_profiles.assert_called_once()
        assert len(profiles) == 2
        assert isinstance(profiles[0], PlayerProfile)
        assert profiles[0].name == "Alice"
        assert profiles[0].profile_id == 1
        assert profiles[1].name == "Bob"

    def test_init_no_db_connection(self, mock_db_manager):
        """Testet, dass eine leere Liste zurückgegeben wird, wenn keine DB-Verbindung besteht."""
        # Simuliere, dass die DB-Methode eine leere Liste zurückgibt
        mock_db_manager.get_all_profiles.return_value = []
        manager = PlayerProfileManager(mock_db_manager)
        assert manager.get_profiles() == []

    def test_add_profile_success(self, mock_db_manager):
        """Testet das erfolgreiche Hinzufügen eines Profils."""
        mock_db_manager.add_profile.return_value = True
        manager = PlayerProfileManager(mock_db_manager)

        result = manager.add_profile("Charlie", "c.png", "#ffffff")

        assert result
        mock_db_manager.add_profile.assert_called_once_with(
            "Charlie", "c.png", "#ffffff", False, None, None, None
        )
        # In der neuen Logik wird nicht mehr gecacht, also wird get_all_profiles nicht erneut aufgerufen.
        mock_db_manager.get_all_profiles.assert_not_called()

    def test_add_profile_fail_duplicate(self, mock_db_manager):
        """Testet, dass das Hinzufügen fehlschlägt, wenn die DB einen Fehler meldet."""
        mock_db_manager.add_profile.return_value = False
        manager = PlayerProfileManager(mock_db_manager)

        result = manager.add_profile("Charlie", "c.png", "#ffffff")

        assert not result
        mock_db_manager.add_profile.assert_called_once()  # noqa

    def test_update_profile_success(self, mock_db_manager):
        """Testet das erfolgreiche Aktualisieren eines Profils."""
        # Erstelle ein Mock ORM-Objekt für den get_profile_by_name Aufruf
        mock_orm_profile = PlayerProfileORM(
            id=1, name="AliceV2", avatar_path="a_v2.png", dart_color="#0000ff", is_ai=False
        )

        # Konfiguriere die Mocks
        mock_db_manager.update_profile.return_value = True
        mock_db_manager.get_all_profiles.return_value = [
            mock_orm_profile
        ]  # Für get_profile_by_name

        manager = PlayerProfileManager(mock_db_manager)

        result = manager.update_profile(
            1,
            "AliceV2",
            "a_v2.png",
            "#0000ff",
            is_ai=False,
            difficulty=None,
            preferred_double=None,
            accuracy_model=None,
        )

        assert result
        mock_db_manager.update_profile.assert_called_once_with(
            1, "AliceV2", "a_v2.png", "#0000ff", False, None, None, None
        )
        # Prüfen, ob die neuen Daten beim nächsten Abruf korrekt sind
        updated_profile = manager.get_profile_by_name("AliceV2")
        assert updated_profile is not None
        assert updated_profile.avatar_path == "a_v2.png"

    def test_delete_profile_success(self, mock_db_manager):
        """Testet das erfolgreiche Löschen eines Profils."""
        mock_db_manager.delete_profile_by_id.return_value = True
        manager = PlayerProfileManager(mock_db_manager)

        # Simuliere, dass nach dem Löschen keine Profile mehr da sind
        def get_profiles_side_effect():
            if mock_db_manager.delete_profile_by_id.called:
                return []
            return [PlayerProfileORM(id=1, name="Alice")]

        mock_db_manager.get_all_profiles.side_effect = get_profiles_side_effect

        result = manager.delete_profile_by_id(1)
        assert result
        mock_db_manager.delete_profile_by_id.assert_called_once_with(1)
        assert len(manager.get_profiles()) == 0
