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

        # Initialisiere alle Sound-Attribute mit None, um AttributeErrors zu vermeiden,
        # falls optionale Dateien nicht vorhanden sind.
        self.hit_sound = None
        self.miss_sound = None
        self.bust_sound = None
        self.no_score_sound = None
        self.low_score_sound = None
        self.one_eighty_sound = None
        self.big_fish_sound = None

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
        # Format: "attribut_name": ("dateiname.wav", ist_pflichtfeld)
        # Hinweis: 'hit.wav' ist die ehemalige 'thump.wav'.
        sound_definitions = {
            "hit": ("hit.wav", True),   # Der dumpfe Einschlag (ehemals thump)
            "miss": ("miss.wav", True), # Das "Ouch!" bei Fehlwürfen
            "bust": ("bust.wav", False),
            "no_score": ("no_score.wav", False),
            "low_score": ("low_score.wav", False),
            "one_eighty": ("180.wav", False),
            "big_fish": ("big_fish.wav", False),
        }
        assets_dir = pathlib.Path(__file__).resolve().parent.parent / "assets"
        for attr_name, (filename, is_required) in sound_definitions.items():
            sound_obj = self._load_sound(assets_dir / filename, required=is_required)
            setattr(self, f"{attr_name}_sound", sound_obj)

    def _load_sound(self, path, required=True):
        """
        Lädt eine einzelne Sounddatei sicher.

        Prüft, ob die Datei existiert und fängt mögliche Fehler beim Laden durch
        `pygame.mixer.Sound` ab. Alle Fehler werden zur späteren Anzeige in
        `self.loading_errors` gespeichert.

        Args:
            path (pathlib.Path): Der vollständige Pfad zur Sounddatei.
            required (bool): Wenn True, wird ein Fehler geloggt/angezeigt, falls die Datei fehlt.

        Returns:
            pygame.mixer.Sound or None: Das geladene Sound-Objekt oder None bei einem Fehler.
        """
        if not path.exists():
            if required:
                msg = f"Pflichtdatei nicht gefunden: {path.name}"
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
            
    def _play(self, sound_obj, ducking_factor=0.3):
        """
        Interne Hilfsmethode zum sicheren Abspielen.
        Reduziert die Lautstärke automatisch (Ducking), wenn der Announcer spricht.
        """
        if self.sounds_enabled and sound_obj:
            # Ducking: Wenn der Announcer (music) aktiv ist, Lautstärke temporär senken
            is_speaking = pygame.mixer.music.get_busy()
            actual_volume = self.volume * ducking_factor if is_speaking else self.volume
            sound_obj.set_volume(actual_volume)
            sound_obj.play()

    def play_hit(self):
        """Spielt den Sound für einen Treffer ab, falls Sounds aktiviert sind."""
        self._play(self.hit_sound)

    def play_miss(self):
        """Spielt den Sound für einen Fehlwurf ab, falls Sounds aktiviert sind."""
        self._play(self.miss_sound)

    def play_bust(self):
        """Spielt den Sound für ein Überwerfen ab, falls Sounds aktiviert sind."""
        self._play(self.bust_sound)

    def play_no_score(self):
        """Spielt den Sound für 0 Punkte ab, falls Sounds aktiviert sind."""
        self._play(self.no_score_sound)

    def play_low_score(self):
        """Spielt den Sound für niedrige Scores ab, falls Sounds aktiviert sind."""
        self._play(self.low_score_sound)

    def play_one_eighty(self):
        """Spielt den Sound für ein Maximum ab, falls Sounds aktiviert sind."""
        self._play(self.one_eighty_sound)

    def play_big_fish(self):
        """Spielt den Sound für das Big Fish Finish ab, falls Sounds aktiviert sind."""
        self._play(self.big_fish_sound)
