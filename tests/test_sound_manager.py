import pytest
from unittest.mock import MagicMock
import logging
import sys

from core.sound_manager import SoundManager


@pytest.fixture
def sound_manager_mocks(monkeypatch):
    """
    Provides a dictionary of mocks for the SoundManager dependencies.
    Also handles singleton reset.
    """
    # Reset singleton to ensure a clean instance for each test
    if hasattr(SoundManager, "_instance"):
        SoundManager._instance = None
    if hasattr(SoundManager, "_initialized"):
        del SoundManager._initialized

    # Mock the pygame module
    mock_pygame = MagicMock()
    # Wir mocken die Sound-Klasse und setzen ihren return_value.
    # Dies stellt sicher, dass Aufrufe von `pygame.mixer.Sound(path)` ein Mock-Objekt zurückgeben.
    mock_pygame.mixer.Sound.return_value = MagicMock()
    mock_pygame.error = Exception
    monkeypatch.setattr("core.sound_manager.pygame", mock_pygame)

    # Mock messagebox
    mock_messagebox = MagicMock()
    monkeypatch.setattr("core.sound_manager.messagebox", mock_messagebox)

    # Mocke Path.exists global für diese Fixture, damit die Tests nicht von echten Dateien abhängen
    monkeypatch.setattr("pathlib.Path.exists", lambda p: True)

    # Mock the SettingsManager
    mock_settings_manager = MagicMock()
    mock_settings_manager.get.return_value = True

    return {
        "settings_manager": mock_settings_manager,
        "root": MagicMock(),
        "mock_pygame": mock_pygame,
        "mock_messagebox": mock_messagebox,
    }


class TestSoundManager:
    """
    Testet die SoundManager-Klasse isoliert von Pygame und dem Dateisystem.
    """

    def test_init_pygame_not_available(self, sound_manager_mocks, monkeypatch, caplog):
        """Testet, ob Sounds deaktiviert sind, wenn pygame nicht verfügbar ist."""
        monkeypatch.setattr("core.sound_manager.PYGAME_AVAILABLE", False)
        with caplog.at_level(logging.WARNING):
            sm = SoundManager(sound_manager_mocks["settings_manager"], sound_manager_mocks["root"])
            assert not sm.sounds_enabled
            sound_manager_mocks["mock_pygame"].mixer.init.assert_not_called()
        assert "pygame ist nicht installiert" in caplog.text

    def test_init_sounds_disabled_in_settings(self, sound_manager_mocks):
        """Testet, ob der Mixer nicht initialisiert wird, wenn Sounds in den Einstellungen deaktiviert sind."""
        sound_manager_mocks["settings_manager"].get.return_value = False
        sm = SoundManager(sound_manager_mocks["settings_manager"], sound_manager_mocks["root"])
        assert not sm.sounds_enabled
        sound_manager_mocks["mock_pygame"].mixer.init.assert_not_called()

    def test_init_mixer_initialization_fails(self, sound_manager_mocks, caplog):
        """Testet das Verhalten, wenn pygame.mixer.init() einen Fehler auslöst."""
        mocks = sound_manager_mocks
        mocks["mock_pygame"].mixer.init.side_effect = mocks["mock_pygame"].error("Mixer-Fehler")
        with caplog.at_level(logging.ERROR):
            sm = SoundManager(sound_manager_mocks["settings_manager"], sound_manager_mocks["root"])
            assert not sm.sounds_enabled
            assert "Pygame mixer konnte nicht initialisiert werden" in sm.loading_errors[0]
        assert "Pygame mixer konnte nicht initialisiert werden" in caplog.text

    def test_init_sound_file_not_found(self, sound_manager_mocks, caplog, monkeypatch):
        """Testet, ob ein Fehler protokolliert wird, wenn eine Sounddatei fehlt."""
        mocks = sound_manager_mocks
        
        # Wir mocken pathlib.Path.exists NUR für diesen Test.
        # Die Funktion gibt für 'miss.wav' False zurück, sonst True.
        def mock_exists(path):
            if "miss.wav" in str(path): return False
            return True

        monkeypatch.setattr("pathlib.Path.exists", mock_exists)

        with caplog.at_level(logging.WARNING):  # Wir erwarten eine Warnung, keinen Error
            sm = SoundManager(mocks["settings_manager"], mocks["root"])
            assert sm.hit_sound is not None
            assert sm.miss_sound is None, "miss_sound sollte None sein, da die Datei fehlt."
            mocks["mock_messagebox"].showwarning.assert_called_once()
        # Prüfe, ob die korrekte WARNING-Nachricht geloggt wurde.
        assert "Pflichtdatei nicht gefunden: miss.wav" in caplog.text, "Die Log-Nachricht für eine fehlende Datei ist falsch."
        assert "Fehler beim Laden" not in caplog.text, "Es sollte kein Lade-ERROR geloggt werden."

    def test_init_sound_loading_error(self, sound_manager_mocks, caplog, monkeypatch):
        """Testet, ob ein Fehler protokolliert wird, wenn pygame eine Datei nicht laden kann."""
        mocks = sound_manager_mocks

        # Stelle sicher, dass die Dateien als vorhanden gemeldet werden
        monkeypatch.setattr("pathlib.Path.exists", lambda p: True)

        # Verwende eine Funktion für side_effect, um gezielt einen Fehler bei miss.wav zu provozieren
        def mock_sound_init(path):
            if "miss.wav" in str(path):
                raise mocks["mock_pygame"].error("Ladefehler")
            return MagicMock()

        mocks["mock_pygame"].mixer.Sound.side_effect = mock_sound_init

        with caplog.at_level(logging.ERROR):
            sm = SoundManager(mocks["settings_manager"], mocks["root"])
            assert sm.hit_sound is not None
            assert sm.miss_sound is None, "miss_sound sollte None sein, da ein Ladefehler auftrat."
            mocks["mock_messagebox"].showwarning.assert_called_once()
        assert "Fehler beim Laden von miss.wav" in caplog.text

    def test_toggle_sounds(self, sound_manager_mocks):  # noqa: E501
        """Testet das Aktivieren und Deaktivieren von Sounds."""
        mocks = sound_manager_mocks
        sm = SoundManager(mocks["settings_manager"], mocks["root"])
        assert sm.sounds_enabled

        # Deaktivieren
        sm.toggle_sounds(False)
        assert not sm.sounds_enabled
        mocks["settings_manager"].set.assert_called_with("sound_enabled", False)

        # Aktivieren
        sm.toggle_sounds(True)
        assert sm.sounds_enabled
        mocks["settings_manager"].set.assert_called_with("sound_enabled", True)

    def test_play_hit_when_enabled(self, sound_manager_mocks):
        """Testet, ob play_hit() den Sound abspielt, wenn aktiviert."""
        mocks = sound_manager_mocks
        sm = SoundManager(mocks["settings_manager"], mocks["root"])
        sm.play_hit()
        sm.hit_sound.play.assert_called_once()

    def test_play_miss_when_sound_not_loaded(self, sound_manager_mocks, monkeypatch):
        """Testet, ob play_miss() nicht abstürzt, wenn der Sound nicht geladen wurde."""
        mocks = sound_manager_mocks

        # Simuliere, dass die 'miss.wav' Datei nicht existiert.
        def mock_exists(path):
            if "miss.wav" in str(path):
                return False
            return True

        monkeypatch.setattr("pathlib.Path.exists", mock_exists)
        sm = SoundManager(mocks["settings_manager"], mocks["root"])

        # sm.miss_sound ist jetzt None
        assert sm.miss_sound is None

        # Der Aufruf sollte einfach nichts tun und keinen Fehler werfen
        try:
            sm.play_miss()
        except Exception as e:
            pytest.fail(f"play_miss() hat einen unerwarteten Fehler ausgelöst: {e}")

    def test_init_optional_sound_missing_is_silent(self, sound_manager_mocks, caplog, monkeypatch):
        """Testet, dass fehlende optionale Sounds keine Warnung oder Fehler auslösen."""
        mocks = sound_manager_mocks

        # Mocke exists: bust.wav fehlt, alle anderen existieren
        def mock_exists(path):
            if "bust.wav" in str(path):
                return False
            return True

        monkeypatch.setattr("pathlib.Path.exists", mock_exists)

        with caplog.at_level(logging.WARNING):
            sm = SoundManager(mocks["settings_manager"], mocks["root"])
            # bust_sound sollte None sein
            assert sm.bust_sound is None
            # Aber hit_sound (Pflicht) sollte geladen sein
            assert sm.hit_sound is not None

        # Es sollte KEINE Warnung für bust.wav im Log sein
        assert "bust.wav" not in caplog.text
        # Die MessageBox sollte NICHT gerufen worden sein (da nur optionale Datei fehlt)
        mocks["mock_messagebox"].showwarning.assert_not_called()
