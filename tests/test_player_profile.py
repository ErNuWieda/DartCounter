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

from core.player_profile import PlayerProfile

def test_initialization():
    """Testet die korrekte Initialisierung eines Profils."""
    profile = PlayerProfile(name="Gemini", avatar_path="assets/avatars/gemini.png")
    assert profile.name == "Gemini"
    assert profile.avatar_path == "assets/avatars/gemini.png"

def test_serialization_and_deserialization():
    """Testet, ob die Konvertierung zu und von einem Dictionary funktioniert."""
    profile = PlayerProfile(name="Martin", avatar_path="assets/avatars/martin.png")
    profile_dict = profile.to_dict()

    expected_dict = {
        'id': None,
        'name': 'Martin',
        'avatar_path': 'assets/avatars/martin.png',
        'dart_color': '#ff0000',
        'is_ai': False,
        'difficulty': None,
        'preferred_double': None, 'accuracy_model': None
    }
    assert profile_dict == expected_dict

    rehydrated_profile = PlayerProfile.from_dict(profile_dict)
    assert isinstance(rehydrated_profile, PlayerProfile)
    assert rehydrated_profile.name == "Martin"
    assert rehydrated_profile.avatar_path == "assets/avatars/martin.png"
    assert rehydrated_profile.dart_color == "#ff0000"
    assert not rehydrated_profile.is_ai
    assert rehydrated_profile.difficulty is None