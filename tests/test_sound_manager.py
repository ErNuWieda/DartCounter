import unittest
from unittest.mock import patch, MagicMock

from core.sound_manager import SoundManager

class TestSoundManager(unittest.TestCase):
    """
    Testet die SoundManager-Klasse isoliert von Pygame und dem Dateisystem.
    """

    def setUp(self):
        """
        Setzt eine saubere Testumgebung für jeden Test auf.
        - Setzt das Singleton zurück, um eine neue Instanz zu erzwingen.
        - Patcht alle externen Abhängigkeiten (pygame, os, messagebox).
        """
        # Singleton-Reset, um eine saubere Instanz für jeden Test zu gewährleisten
        if hasattr(SoundManager, '_instance'):
            SoundManager._instance = None
        if hasattr(SoundManager, '_initialized'):
            del SoundManager._initialized

        # Mock für das pygame-Modul
        self.patcher_pygame = patch('core.sound_manager.pygame')
        self.mock_pygame = self.patcher_pygame.start()
        # Definieren, was die gemockten Pygame-Funktionen tun sollen
        self.mock_pygame.mixer.Sound.return_value = MagicMock()
        # Simuliere einen Pygame-Fehler für Testzwecke
        self.mock_pygame.error = Exception

        # Mock für pathlib.Path.exists, da der SoundManager jetzt pathlib verwendet.
        self.patcher_path_exists = patch('pathlib.Path.exists', return_value=True)
        self.mock_path_exists = self.patcher_path_exists.start()

        # Mock für messagebox
        self.patcher_messagebox = patch('core.sound_manager.messagebox')
        self.mock_messagebox = self.patcher_messagebox.start()

        # Mock für den SettingsManager
        self.mock_settings_manager = MagicMock()
        # Standardverhalten: Sounds sind in den Einstellungen aktiviert
        self.mock_settings_manager.get.return_value = True

        # Mock für das root-Fenster
        self.mock_root = MagicMock()

        # Sicherstellen, dass alle Patcher nach dem Test gestoppt werden
        self.addCleanup(self.patcher_pygame.stop)
        self.addCleanup(self.patcher_path_exists.stop)
        self.addCleanup(self.patcher_messagebox.stop)

    @patch('core.sound_manager.PYGAME_AVAILABLE', False)
    def test_init_pygame_not_available(self):
        """Testet, ob Sounds deaktiviert sind, wenn pygame nicht verfügbar ist."""
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        self.assertFalse(sm.sounds_enabled)
        self.mock_pygame.mixer.init.assert_not_called()

    def test_init_sounds_disabled_in_settings(self):
        """Testet, ob der Mixer nicht initialisiert wird, wenn Sounds in den Einstellungen deaktiviert sind."""
        self.mock_settings_manager.get.return_value = False
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        self.assertFalse(sm.sounds_enabled)
        self.mock_pygame.mixer.init.assert_not_called()

    def test_init_mixer_initialization_fails(self):
        """Testet das Verhalten, wenn pygame.mixer.init() einen Fehler auslöst."""
        self.mock_pygame.mixer.init.side_effect = self.mock_pygame.error("Mixer-Fehler")
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        self.assertFalse(sm.sounds_enabled)
        self.assertIn("Pygame mixer konnte nicht initialisiert werden", sm.loading_errors[0])

    def test_init_sound_file_not_found(self):
        """Testet, ob ein Fehler protokolliert wird, wenn eine Sounddatei fehlt."""
        # Reihenfolge: hit, win, miss, bust, bull, bullseye, 100, 180, shanghai
        # Simuliere, dass 'bust.wav' (4. Sound) fehlt.
        self.mock_path_exists.side_effect = [True, True, True, False, True, True, True, True, True]
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        self.assertIsNotNone(sm.hit_sound)
        self.assertIsNotNone(sm.win_sound)
        self.assertIsNotNone(sm.miss_sound)
        self.assertIsNone(sm.bust_sound, "bust_sound sollte None sein, da die Datei fehlt.")
        self.assertIsNotNone(sm.bull_sound)
        self.assertIsNotNone(sm.bullseye_sound)
        self.assertIsNotNone(sm.score_100_sound)
        self.assertIsNotNone(sm.score_180_sound)
        self.assertIsNotNone(sm.shanghai_sound)
        self.mock_messagebox.showwarning.assert_called_once()

    def test_init_sound_loading_error(self):
        """Testet, ob ein Fehler protokolliert wird, wenn pygame eine Datei nicht laden kann."""
        # Simuliere, dass Sound() beim Laden von 'bull.wav' (5. Sound) einen Fehler wirft.
        sound_mocks = [MagicMock() for _ in range(9)]
        sound_mocks[4] = self.mock_pygame.error("Ladefehler") # bull.wav fails
        self.mock_pygame.mixer.Sound.side_effect = sound_mocks

        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        self.assertIsNotNone(sm.hit_sound)
        self.assertIsNotNone(sm.win_sound)
        self.assertIsNotNone(sm.miss_sound)
        self.assertIsNotNone(sm.bust_sound)
        self.assertIsNone(sm.bull_sound, "bull_sound sollte None sein, da ein Ladefehler auftrat.")
        self.assertIsNotNone(sm.bullseye_sound)
        self.assertIsNotNone(sm.score_100_sound)
        self.assertIsNotNone(sm.score_180_sound)
        self.assertIsNotNone(sm.shanghai_sound)
        self.mock_messagebox.showwarning.assert_called_once()

    def test_toggle_sounds(self):
        """Testet das Aktivieren und Deaktivieren von Sounds."""
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        self.assertTrue(sm.sounds_enabled)

        # Deaktivieren
        sm.toggle_sounds(False)
        self.assertFalse(sm.sounds_enabled)
        self.mock_settings_manager.set.assert_called_with('sound_enabled', False)

        # Aktivieren
        sm.toggle_sounds(True)
        self.assertTrue(sm.sounds_enabled)
        self.mock_settings_manager.set.assert_called_with('sound_enabled', True)

    def test_play_hit_when_enabled(self):
        """Testet, ob play_hit() den Sound abspielt, wenn aktiviert."""
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        sm.play_hit()
        sm.hit_sound.play.assert_called_once()

    def test_play_win_when_disabled(self):
        """Testet, ob play_win() nichts tut, wenn deaktiviert."""
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        sm.toggle_sounds(False)
        sm.play_win()
        sm.win_sound.play.assert_not_called()

    def test_play_bust(self):
        """Testet, ob play_bust() den Sound abspielt."""
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        sm.play_bust()
        sm.bust_sound.play.assert_called_once()

    def test_play_bull(self):
        """Testet, ob play_bull() den Sound abspielt."""
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        sm.play_bull()
        sm.bull_sound.play.assert_called_once()

    def test_play_bullseye(self):
        """Testet, ob play_bullseye() den Sound abspielt."""
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        sm.play_bullseye()
        sm.bullseye_sound.play.assert_called_once()

    def test_play_score_100(self):
        """Testet, ob play_score_100() den Sound abspielt."""
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        sm.play_score_100()
        sm.score_100_sound.play.assert_called_once()

    def test_play_score_180(self):
        """Testet, ob play_score_180() den Sound abspielt."""
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        sm.play_score_180()
        sm.score_180_sound.play.assert_called_once()

    def test_play_shanghai(self):
        """Testet, ob play_shanghai() den Sound abspielt."""
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        sm.play_shanghai()
        sm.shanghai_sound.play.assert_called_once()

    def test_play_miss_when_sound_not_loaded(self):
        """Testet, ob play_miss() nicht abstürzt, wenn der Sound nicht geladen wurde."""
        # Reihenfolge: hit, win, miss, bust, bull, bullseye, 100, 180, shanghai
        # Simuliere, dass miss.wav (3. Sound) nicht gefunden wurde
        self.mock_path_exists.side_effect = [True, True, False, True, True, True, True, True, True]
        sm = SoundManager(self.mock_settings_manager, self.mock_root)
        
        # sm.miss_sound ist jetzt None
        self.assertIsNone(sm.miss_sound)
        
        # Der Aufruf sollte einfach nichts tun und keinen Fehler werfen
        try:
            sm.play_miss()
        except Exception as e:
            self.fail(f"play_miss() hat einen unerwarteten Fehler ausgelöst: {e}")

if __name__ == '__main__':
    unittest.main()