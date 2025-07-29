import unittest
from unittest.mock import patch, MagicMock

from core.player_profile_manager import PlayerProfileManager
from core.player_profile import PlayerProfile

class TestPlayerProfileManager(unittest.TestCase):
    """Testet den PlayerProfileManager."""
    def setUp(self):
        """Patcht die DatabaseManager-Abhängigkeit."""
        self.mock_db_manager = MagicMock()
        # Standard-Setup: DB ist verbunden und gibt eine leere Profilliste zurück
        self.mock_db_manager.is_connected = True
        self.mock_db_manager.get_all_profiles.return_value = []

    def test_init_loads_profiles_from_db(self):
        """Testet, dass beim Initialisieren Profile aus der DB geladen werden."""
        mock_profiles_data = [
            {'id': 1, 'name': 'Alice', 'avatar_path': 'a.png', 'dart_color': '#ff0000'},
            {'id': 2, 'name': 'Bob', 'avatar_path': None, 'dart_color': '#00ff00'}
        ]
        self.mock_db_manager.get_all_profiles.return_value = mock_profiles_data
        
        manager = PlayerProfileManager(self.mock_db_manager)
        
        self.mock_db_manager.get_all_profiles.assert_called_once()
        profiles = manager.get_profiles()
        self.assertEqual(len(profiles), 2)
        self.assertIsInstance(profiles[0], PlayerProfile)
        self.assertEqual(profiles[0].name, 'Alice')
        self.assertEqual(profiles[0].id, 1)
        self.assertEqual(profiles[1].name, 'Bob')

    def test_init_no_db_connection(self):
        """Testet, dass eine leere Liste zurückgegeben wird, wenn keine DB-Verbindung besteht."""
        self.mock_db_manager.is_connected = False
        manager = PlayerProfileManager(self.mock_db_manager)
        self.assertEqual(manager.get_profiles(), [])

    def test_add_profile_success(self):
        """Testet das erfolgreiche Hinzufügen eines Profils."""
        self.mock_db_manager.add_profile.return_value = True
        manager = PlayerProfileManager(self.mock_db_manager)
        
        result = manager.add_profile("Charlie", "c.png", "#ffffff")
        
        self.assertTrue(result)
        self.mock_db_manager.add_profile.assert_called_once_with("Charlie", "c.png", "#ffffff", False, None)
        # Prüfen, ob die Profile nach dem Hinzufügen neu geladen werden
        self.assertEqual(self.mock_db_manager.get_all_profiles.call_count, 2)

    def test_add_profile_fail_duplicate(self):
        """Testet, dass das Hinzufügen fehlschlägt, wenn die DB einen Fehler meldet."""
        self.mock_db_manager.add_profile.return_value = False
        manager = PlayerProfileManager(self.mock_db_manager)
        
        result = manager.add_profile("Charlie", "c.png", "#ffffff")
        
        self.assertFalse(result)
        self.mock_db_manager.add_profile.assert_called_once()
        # Profile dürfen nicht neu geladen werden, wenn das Hinzufügen fehlschlägt
        self.mock_db_manager.get_all_profiles.assert_called_once()

    def test_update_profile_success(self):
        """Testet das erfolgreiche Aktualisieren eines Profils."""
        self.mock_db_manager.get_all_profiles.return_value = [
            {'id': 1, 'name': 'Alice', 'avatar_path': 'a.png', 'dart_color': '#ff0000'}
        ]
        self.mock_db_manager.update_profile.return_value = True
        manager = PlayerProfileManager(self.mock_db_manager)
        
        result = manager.update_profile(1, "AliceV2", "a_v2.png", "#0000ff")
        
        self.assertTrue(result)
        self.mock_db_manager.update_profile.assert_called_once_with(1, "AliceV2", "a_v2.png", "#0000ff", False, None)
        # Prüfen, ob das lokale Profil aktualisiert wurde
        updated_profile = manager.get_profile_by_name("AliceV2")
        self.assertIsNotNone(updated_profile)
        self.assertEqual(updated_profile.avatar_path, "a_v2.png")

    def test_delete_profile_success(self):
        """Testet das erfolgreiche Löschen eines Profils."""
        self.mock_db_manager.get_all_profiles.return_value = [
            {'id': 1, 'name': 'Alice', 'avatar_path': 'a.png', 'dart_color': '#ff0000'}
        ]
        self.mock_db_manager.delete_profile.return_value = True
        manager = PlayerProfileManager(self.mock_db_manager)
        
        self.assertEqual(len(manager.get_profiles()), 1)
        result = manager.delete_profile("Alice")
        
        self.assertTrue(result)
        self.mock_db_manager.delete_profile.assert_called_once_with("Alice")
        self.assertEqual(len(manager.get_profiles()), 0) # Prüfen, ob das Profil aus der lokalen Liste entfernt wurde