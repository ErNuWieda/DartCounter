import unittest

from core.player_profile import PlayerProfile

class TestPlayerProfile(unittest.TestCase):
    """Testet die PlayerProfile-Klasse."""

    def test_initialization(self):
        """Testet die korrekte Initialisierung eines Profils."""
        profile = PlayerProfile(name="Gemini", avatar_path="assets/avatars/gemini.png")
        self.assertEqual(profile.name, "Gemini")
        self.assertEqual(profile.avatar_path, "assets/avatars/gemini.png")

    def test_serialization_and_deserialization(self):
        """Testet, ob die Konvertierung zu und von einem Dictionary funktioniert."""
        profile = PlayerProfile(name="Martin", avatar_path="assets/avatars/martin.png")
        profile_dict = profile.to_dict()

        expected_dict = {
            'id': None,
            'name': 'Martin',
            'avatar_path': 'assets/avatars/martin.png',
            'dart_color': '#ff0000',
            'is_ai': False,
            'difficulty': None
        }
        self.assertEqual(profile_dict, expected_dict)

        rehydrated_profile = PlayerProfile.from_dict(profile_dict)
        self.assertIsInstance(rehydrated_profile, PlayerProfile)
        self.assertEqual(rehydrated_profile.name, "Martin")
        self.assertEqual(rehydrated_profile.avatar_path, "assets/avatars/martin.png")
        self.assertEqual(rehydrated_profile.dart_color, "#ff0000")
        self.assertFalse(rehydrated_profile.is_ai)
        self.assertIsNone(rehydrated_profile.difficulty)

if __name__ == '__main__':
    unittest.main()