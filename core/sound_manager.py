import os
import pathlib
from tkinter import messagebox


try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

class SoundManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SoundManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, settings_manager):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.settings_manager = settings_manager
        self.loading_errors = [] # To collect errors for a single messagebox

        if not PYGAME_AVAILABLE:
            print("Warnung: pygame ist nicht installiert. Soundeffekte sind deaktiviert.")
            self.sounds_enabled = False
            return

        # Lade den initialen Zustand aus dem SettingsManager
        self.sounds_enabled = self.settings_manager.get('sound_enabled', True)

        if not self.sounds_enabled:
            return # Don't initialize mixer or load sounds if disabled from settings

        try:
            pygame.mixer.init()
        except pygame.error as e:
            print(f"Pygame mixer konnte nicht initialisiert werden: {e}")
            self.sounds_enabled = False
            self.loading_errors.append(f"Pygame mixer konnte nicht initialisiert werden: {e}")
            return

        assets_dir = pathlib.Path(__file__).resolve().parent.parent / "assets"
        self.hit_sound = self._load_sound(assets_dir / "hit.wav")
        self.win_sound = self._load_sound(assets_dir / "win.wav")

        # After trying to load all sounds, show a single warning if any failed.
        if self.loading_errors:
            error_string = "\n- ".join(self.loading_errors)
            messagebox.showwarning(
                "Sound-Fehler",
                f"Einige Sound-Dateien konnten nicht geladen werden:\n- {error_string}\n\nDie Soundeffekte sind für diese Sitzung teilweise oder ganz deaktiviert."
            )

    def _load_sound(self, path):
        if not os.path.exists(path):
            msg = f"Datei nicht gefunden: {os.path.basename(path)}"
            print(f"WARNUNG: {msg}")
            self.loading_errors.append(msg)
            return None
        try:
            return pygame.mixer.Sound(path)
        except pygame.error as e:
            msg = f"Fehler beim Laden von {os.path.basename(path)}: {e}"
            print(f"FEHLER: {msg}")
            self.loading_errors.append(msg)
            return None

    def toggle_sounds(self, enabled):
        """Aktiviert oder deaktiviert alle Sounds global."""
        if not PYGAME_AVAILABLE:
            self.sounds_enabled = False
            return
        self.sounds_enabled = bool(enabled)
        # Speichere die neue Einstellung im SettingsManager
        self.settings_manager.set('sound_enabled', self.sounds_enabled)
        if not self.sounds_enabled:
            print("Soundeffekte deaktiviert.")

    def play_hit(self):
        if self.sounds_enabled and self.hit_sound: self.hit_sound.play()

    def play_win(self):
        if self.sounds_enabled and self.win_sound: self.win_sound.play()