import pytest
from unittest.mock import MagicMock

from core.player_profile_manager import PlayerProfileManager
from core.player_profile import PlayerProfile

@pytest.fixture
def mock_db_manager():
    """Fixture für einen gemockten DatabaseManager."""
    db_manager = MagicMock()
    db_manager.is_connected = True
    db_manager.get_all_profiles.return_value = []
    return db_manager

class TestPlayerProfileManager:
    """Testet den PlayerProfileManager."""
    def test_init_loads_profiles_from_db(self, mock_db_manager):
        """Testet, dass beim Initialisieren Profile aus der DB geladen werden."""
        mock_profiles_data = [
            {'id': 1, 'name': 'Alice', 'avatar_path': 'a.png', 'dart_color': '#ff0000', 'is_ai': False, 'difficulty': None},
            {'id': 2, 'name': 'Bob', 'avatar_path': None, 'dart_color': '#00ff00', 'is_ai': False, 'difficulty': None}
        ]
        mock_db_manager.get_all_profiles.return_value = mock_profiles_data
        
        manager = PlayerProfileManager(mock_db_manager)
        
        mock_db_manager.get_all_profiles.assert_called_once()
        profiles = manager.get_profiles()
        assert len(profiles) == 2
        assert isinstance(profiles[0], PlayerProfile)
        assert profiles[0].name == 'Alice'
        assert profiles[0].id == 1
        assert profiles[1].name == 'Bob'

    def test_init_no_db_connection(self, mock_db_manager):
        """Testet, dass eine leere Liste zurückgegeben wird, wenn keine DB-Verbindung besteht."""
        mock_db_manager.is_connected = False
        manager = PlayerProfileManager(mock_db_manager)
        assert manager.get_profiles() == []

    def test_add_profile_success(self, mock_db_manager):
        """Testet das erfolgreiche Hinzufügen eines Profils."""
        mock_db_manager.add_profile.return_value = True
        manager = PlayerProfileManager(mock_db_manager)
        
        result = manager.add_profile("Charlie", "c.png", "#ffffff")
        
        assert result
        mock_db_manager.add_profile.assert_called_once_with("Charlie", "c.png", "#ffffff", False, None)
        # Prüfen, ob die Profile nach dem Hinzufügen neu geladen werden
        assert mock_db_manager.get_all_profiles.call_count == 2

    def test_add_profile_fail_duplicate(self, mock_db_manager):
        """Testet, dass das Hinzufügen fehlschlägt, wenn die DB einen Fehler meldet."""
        mock_db_manager.add_profile.return_value = False
        manager = PlayerProfileManager(mock_db_manager)
        
        result = manager.add_profile("Charlie", "c.png", "#ffffff")
        
        assert not result
        mock_db_manager.add_profile.assert_called_once()
        # Profile dürfen nicht neu geladen werden, wenn das Hinzufügen fehlschlägt
        mock_db_manager.get_all_profiles.assert_called_once()

    def test_update_profile_success(self, mock_db_manager):
        """Testet das erfolgreiche Aktualisieren eines Profils."""
        mock_db_manager.get_all_profiles.return_value = [
            {'id': 1, 'name': 'Alice', 'avatar_path': 'a.png', 'dart_color': '#ff0000', 'is_ai': False, 'difficulty': None}
        ]
        mock_db_manager.update_profile.return_value = True
        manager = PlayerProfileManager(mock_db_manager)
        
        result = manager.update_profile(1, "AliceV2", "a_v2.png", "#0000ff", is_ai=False, difficulty=None)
        
        assert result
        mock_db_manager.update_profile.assert_called_once_with(1, "AliceV2", "a_v2.png", "#0000ff", False, None)
        # Prüfen, ob das lokale Profil aktualisiert wurde
        updated_profile = manager.get_profile_by_name("AliceV2")
        assert updated_profile is not None
        assert updated_profile.avatar_path == "a_v2.png"

    def test_delete_profile_success(self, mock_db_manager):
        """Testet das erfolgreiche Löschen eines Profils."""
        mock_db_manager.get_all_profiles.return_value = [
            {'id': 1, 'name': 'Alice', 'avatar_path': 'a.png', 'dart_color': '#ff0000', 'is_ai': False, 'difficulty': None}
        ]
        mock_db_manager.delete_profile.return_value = True
        manager = PlayerProfileManager(mock_db_manager)
        
        assert len(manager.get_profiles()) == 1
        result = manager.delete_profile("Alice")
        
        assert result
        mock_db_manager.delete_profile.assert_called_once_with("Alice")
        assert len(manager.get_profiles()) == 0 # Prüfen, ob das Profil aus der lokalen Liste entfernt wurde