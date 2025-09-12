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

import logging
import pathlib
from tkinter import messagebox


try:
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

logger = logging.getLogger(__name__)


class SoundManager:
    """
    Verwaltet das Laden und Abspielen aller Soundeffekte in der Anwendung.

    Diese Klasse ist als Singleton implementiert, um sicherzustellen, dass nur eine
    Instanz des Pygame-Mixers existiert. Sie ist verantwortlich für:
    - Die Initialisierung des `pygame.mixer`.
    - Das Laden von Sounddateien (z.B. für Treffer, Spielgewinn).
    - Das Abspielen von Sounds auf Anforderung.
    - Die Interaktion mit dem `SettingsManager`, um die Sound-Einstellungen
      des Benutzers zu laden und zu speichern.
    - Eine robuste Fehlerbehandlung, falls `pygame` nicht installiert ist oder
      Sounddateien fehlen, um einen Absturz der Anwendung zu verhindern.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Implementiert das Singleton-Muster.
        Stellt sicher, dass nur eine Instanz dieser Klasse erstellt wird.
        """
        if not cls._instance:
            cls._instance = super(SoundManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, settings_manager, root=None):
        """
        Initialisiert den SoundManager.

        Dieser Konstruktor wird nur beim ersten Aufruf ausgeführt. Er prüft die
        Verfügbarkeit von `pygame`, lädt die Sound-Einstellungen, initialisiert
        den Mixer und lädt alle definierten Sound-Dateien. Fehler beim Laden
        werden gesammelt und am Ende in einer einzigen `MessageBox` angezeigt.

        Args:
            settings_manager (SettingsManager): Die Instanz des SettingsManagers,
                                                um Einstellungen zu laden/speichern.
            root (tk.Tk, optional): Das Hauptfenster für Dialoge.
        """
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self.settings_manager = settings_manager
        self.root = root
        self.loading_errors = []  # To collect errors for a single messagebox
        self.loaded_sounds = []  # To store all sound objects

        if not PYGAME_AVAILABLE:
            logger.warning("pygame ist nicht installiert. Soundeffekte sind deaktiviert.")
            self.sounds_enabled = False
            return

        # Lade den initialen Zustand aus dem SettingsManager
        self.sounds_enabled = self.settings_manager.get("sound_enabled", True)
        self.volume = self.settings_manager.get("sound_volume", 0.5)

        if not self.sounds_enabled:
            return  # Don't initialize mixer or load sounds if disabled from settings

        try:
            pygame.mixer.init()
        except pygame.error as e:
            logger.error(
                f"Pygame mixer konnte nicht initialisiert werden: {e}",
                exc_info=True,
            )
            self.sounds_enabled = False
            self.loading_errors.append(f"Pygame mixer konnte nicht initialisiert werden: {e}")
            return

        self._load_all_sounds()

        # After trying to load all sounds, show a single warning if any failed.
        if self.loading_errors:
            error_string = "\n- ".join(self.loading_errors)
            messagebox.showwarning(
                title="Sound-Fehler",
                message=(
                    f"Einige Sound-Dateien konnten nicht geladen werden:\n- {error_string}\n\n"
                    "Sounds sind ggf. deaktiviert."
                ),
                parent=self.root,
            )

    def _load_all_sounds(self):
        """Lädt alle definierten Sound-Dateien."""
        # Datengesteuerter Ansatz: Definiere alle Sounds an einer Stelle.
        # Das macht das Hinzufügen neuer Sounds einfacher.
        sound_definitions = {
            "hit": "hit.wav",
            "win": "win.wav",
            "miss": "miss.wav",
            "bust": "bust.wav",
            "bull": "bull.wav",
            "bullseye": "bullseye.wav",
            "score_100": "100.wav",
            "score_140": "140.wav",
            "score_160": "160.wav",
            "score_180": "180.wav",
            "shanghai": "shanghai.wav",
        }
        assets_dir = pathlib.Path(__file__).resolve().parent.parent / "assets"
        for attr_name, filename in sound_definitions.items():
            setattr(
                self,
                f"{attr_name}_sound",
                self._load_sound(assets_dir / filename),
            )

    def _load_sound(self, path):
        """
        Lädt eine einzelne Sounddatei sicher.

        Prüft, ob die Datei existiert und fängt mögliche Fehler beim Laden durch
        `pygame.mixer.Sound` ab. Alle Fehler werden zur späteren Anzeige in
        `self.loading_errors` gespeichert.

        Args:
            path (pathlib.Path): Der vollständige Pfad zur Sounddatei.

        Returns:
            pygame.mixer.Sound or None: Das geladene Sound-Objekt oder None bei einem Fehler.
        """
        if not path.exists():
            msg = f"Datei nicht gefunden: {path.name}"
            logger.warning(msg)
            self.loading_errors.append(msg)
            return None
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(self.volume)
            self.loaded_sounds.append(sound)
            return sound
        except pygame.error as e:
            msg = f"Fehler beim Laden von {path.name}: {e}"
            logger.error(msg, exc_info=True)
            self.loading_errors.append(msg)
            return None

    def set_global_volume(self, volume: float):
        """
        Setzt die Lautstärke für alle geladenen Soundeffekte.

        Args:
            volume (float): Die Lautstärke als Wert zwischen 0.0 und 1.0.
        """
        self.volume = volume
        if not PYGAME_AVAILABLE or not self.sounds_enabled:
            return

        for sound in self.loaded_sounds:
            if sound:
                sound.set_volume(self.volume)

    def toggle_sounds(self, enabled):
        """
        Aktiviert oder deaktiviert alle Sounds global und speichert die Einstellung.

        Args:
            enabled (bool): True, um Sounds zu aktivieren, False, um sie zu deaktivieren.
        """
        if not PYGAME_AVAILABLE:
            self.sounds_enabled = False
            return
        self.sounds_enabled = bool(enabled)
        # Speichere die neue Einstellung im SettingsManager
        self.settings_manager.set("sound_enabled", self.sounds_enabled)
        if not self.sounds_enabled:
            logger.info("Soundeffekte deaktiviert.")

    def play_hit(self):
        """Spielt den Sound für einen Treffer ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.hit_sound:
            self.hit_sound.play()

    def play_win(self):
        """Spielt den Sound für einen Spielgewinn ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.win_sound:
            self.win_sound.play()

    def play_miss(self):
        """Spielt den Sound für einen Fehlwurf ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.miss_sound:
            self.miss_sound.play()

    def play_bust(self):
        """Spielt den Sound für einen Bust ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.bust_sound:
            self.bust_sound.play()

    def play_bull(self):
        """Spielt den Sound für ein Bull ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.bull_sound:
            self.bull_sound.play()

    def play_bullseye(self):
        """Spielt den Sound für ein Bullseye ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.bullseye_sound:
            self.bullseye_sound.play()

    def play_score_100(self):
        """Spielt den Sound für einen Score von 100+ ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.score_100_sound:
            self.score_100_sound.play()

    def play_score_120(self):
        """Spielt den Sound für einen Score von 100+ ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.score_100_sound:
            self.score_100_sound.play()

    def play_score_140(self):
        """Spielt den Sound für einen Score von 140 ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.score_140_sound:
            self.score_140_sound.play()

    def play_score_160(self):
        """Spielt den Sound für einen Score von 160 ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.score_160_sound:
            self.score_160_sound.play()

    def play_score_180(self):
        """Spielt den Sound für einen Score von 180 ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.score_180_sound:
            self.score_180_sound.play()

    def play_shanghai(self):
        """Spielt den Sound für ein Shanghai-Finish ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.shanghai_sound:
            self.shanghai_sound.play()
