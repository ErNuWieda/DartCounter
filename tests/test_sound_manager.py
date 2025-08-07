import pytest
from unittest.mock import MagicMock
import sys

from core.sound_manager import SoundManager

@pytest.fixture
def sound_manager_mocks(monkeypatch):
    """
    Provides a dictionary of mocks for the SoundManager dependencies.
    Also handles singleton reset.
    """
    # Reset singleton to ensure a clean instance for each test
    if hasattr(SoundManager, '_instance'):
        SoundManager._instance = None
    if hasattr(SoundManager, '_initialized'):
        del SoundManager._initialized

    # Mock the pygame module
    mock_pygame = MagicMock()
    mock_pygame.mixer.Sound.return_value = MagicMock()
    mock_pygame.error = Exception
    monkeypatch.setattr('core.sound_manager.pygame', mock_pygame)

    # Mock pathlib.Path.exists
    mock_path_exists = MagicMock(return_value=True)
    monkeypatch.setattr('pathlib.Path.exists', mock_path_exists)

    # Mock messagebox
    mock_messagebox = MagicMock()
    monkeypatch.setattr('core.sound_manager.messagebox', mock_messagebox)

    # Mock the SettingsManager
    mock_settings_manager = MagicMock()
    mock_settings_manager.get.return_value = True

    return {
        "settings_manager": mock_settings_manager,
        "root": MagicMock(),
        "mock_pygame": mock_pygame,
        "mock_path_exists": mock_path_exists,
        "mock_messagebox": mock_messagebox
    }

class TestSoundManager:
    """
    Testet die SoundManager-Klasse isoliert von Pygame und dem Dateisystem.
    """
    def test_init_pygame_not_available(self, sound_manager_mocks, monkeypatch):
        """Testet, ob Sounds deaktiviert sind, wenn pygame nicht verfügbar ist."""
        monkeypatch.setattr('core.sound_manager.PYGAME_AVAILABLE', False)
        sm = SoundManager(sound_manager_mocks["settings_manager"], sound_manager_mocks["root"])
        assert not sm.sounds_enabled
        sound_manager_mocks["mock_pygame"].mixer.init.assert_not_called()

    def test_init_sounds_disabled_in_settings(self, sound_manager_mocks):
        """Testet, ob der Mixer nicht initialisiert wird, wenn Sounds in den Einstellungen deaktiviert sind."""
        sound_manager_mocks["settings_manager"].get.return_value = False
        sm = SoundManager(sound_manager_mocks["settings_manager"], sound_manager_mocks["root"])
        assert not sm.sounds_enabled
        sound_manager_mocks["mock_pygame"].mixer.init.assert_not_called()

    def test_init_mixer_initialization_fails(self, sound_manager_mocks):
        """Testet das Verhalten, wenn pygame.mixer.init() einen Fehler auslöst."""
        sound_manager_mocks["mock_pygame"].mixer.init.side_effect = sound_manager_mocks["mock_pygame"].error("Mixer-Fehler")
        sm = SoundManager(sound_manager_mocks["settings_manager"], sound_manager_mocks["root"])
        assert not sm.sounds_enabled
        assert "Pygame mixer konnte nicht initialisiert werden" in sm.loading_errors[0]

    def test_init_sound_file_not_found(self, sound_manager_mocks):
        """Testet, ob ein Fehler protokolliert wird, wenn eine Sounddatei fehlt."""
        mocks = sound_manager_mocks
        # Reihenfolge: hit, win, miss, bust, bull, bullseye, 100, 180, shanghai
        # Simuliere, dass 'bust.wav' (4. Sound) fehlt.
        mocks["mock_path_exists"].side_effect = [True, True, True, False, True, True, True, True, True]
        sm = SoundManager(mocks["settings_manager"], mocks["root"])
        assert sm.hit_sound is not None
        assert sm.win_sound is not None
        assert sm.miss_sound is not None
        assert sm.bust_sound is None, "bust_sound sollte None sein, da die Datei fehlt."
        assert sm.bull_sound is not None
        assert sm.bullseye_sound is not None
        assert sm.score_100_sound is not None
        assert sm.score_180_sound is not None
        assert sm.shanghai_sound is not None
        mocks["mock_messagebox"].showwarning.assert_called_once()

    def test_init_sound_loading_error(self, sound_manager_mocks):
        """Testet, ob ein Fehler protokolliert wird, wenn pygame eine Datei nicht laden kann."""
        mocks = sound_manager_mocks
        # Simuliere, dass Sound() beim Laden von 'bull.wav' (5. Sound) einen Fehler wirft.
        sound_mocks = [MagicMock() for _ in range(9)]
        sound_mocks[4] = mocks["mock_pygame"].error("Ladefehler") # bull.wav fails
        mocks["mock_pygame"].mixer.Sound.side_effect = sound_mocks

        sm = SoundManager(mocks["settings_manager"], mocks["root"])
        assert sm.hit_sound is not None
        assert sm.win_sound is not None
        assert sm.miss_sound is not None
        assert sm.bust_sound is not None
        assert sm.bull_sound is None, "bull_sound sollte None sein, da ein Ladefehler auftrat."
        assert sm.bullseye_sound is not None
        assert sm.score_100_sound is not None
        assert sm.score_180_sound is not None
        assert sm.shanghai_sound is not None
        mocks["mock_messagebox"].showwarning.assert_called_once()

    def test_toggle_sounds(self, sound_manager_mocks):
        """Testet das Aktivieren und Deaktivieren von Sounds."""
        mocks = sound_manager_mocks
        sm = SoundManager(mocks["settings_manager"], mocks["root"])
        assert sm.sounds_enabled

        # Deaktivieren
        sm.toggle_sounds(False)
        assert not sm.sounds_enabled
        mocks["settings_manager"].set.assert_called_with('sound_enabled', False)

        # Aktivieren
        sm.toggle_sounds(True)
        assert sm.sounds_enabled
        mocks["settings_manager"].set.assert_called_with('sound_enabled', True)

    def test_play_hit_when_enabled(self, sound_manager_mocks):
        """Testet, ob play_hit() den Sound abspielt, wenn aktiviert."""
        mocks = sound_manager_mocks
        sm = SoundManager(mocks["settings_manager"], mocks["root"])
        sm.play_hit()
        sm.hit_sound.play.assert_called_once()

    def test_play_win_when_disabled(self, sound_manager_mocks):
        """Testet, ob play_win() nichts tut, wenn deaktiviert."""
        mocks = sound_manager_mocks
        sm = SoundManager(mocks["settings_manager"], mocks["root"])
        sm.toggle_sounds(False)
        sm.play_win()
        sm.win_sound.play.assert_not_called()

    def test_play_miss_when_sound_not_loaded(self, sound_manager_mocks):
        """Testet, ob play_miss() nicht abstürzt, wenn der Sound nicht geladen wurde."""
        mocks = sound_manager_mocks
        # Reihenfolge: hit, win, miss, bust, bull, bullseye, 100, 180, shanghai
        # Simuliere, dass miss.wav (3. Sound) nicht gefunden wurde
        mocks["mock_path_exists"].side_effect = [True, True, False, True, True, True, True, True, True]
        sm = SoundManager(mocks["settings_manager"], mocks["root"])
        
        # sm.miss_sound ist jetzt None
        assert sm.miss_sound is None
        
        # Der Aufruf sollte einfach nichts tun und keinen Fehler werfen
        try:
            sm.play_miss()
        except Exception as e:
            pytest.fail(f"play_miss() hat einen unerwarteten Fehler ausgelöst: {e}")