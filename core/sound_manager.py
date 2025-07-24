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

import os
import pathlib
from tkinter import messagebox


try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

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
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.settings_manager = settings_manager
        self.root = root
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
        self.draw_sound = self._load_sound(assets_dir / "draw.wav")

        # After trying to load all sounds, show a single warning if any failed.
        if self.loading_errors:
            error_string = "\n- ".join(self.loading_errors)
            messagebox.showwarning(
                title="Sound-Fehler",
                message=f"Einige Sound-Dateien konnten nicht geladen werden:\n- {error_string}\n\nDie Soundeffekte sind für diese Sitzung teilweise oder ganz deaktiviert.",
                parent=self.root
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
        self.settings_manager.set('sound_enabled', self.sounds_enabled)
        if not self.sounds_enabled:
            print("Soundeffekte deaktiviert.")

    def play_hit(self):
        """Spielt den Sound für einen Treffer ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.hit_sound: self.hit_sound.play()

    def play_win(self):
        """Spielt den Sound für einen Spielgewinn ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.win_sound: self.win_sound.play()

    def play_draw(self):
        """Spielt den Sound für ein Unentschieden ab, falls Sounds aktiviert sind."""
        if self.sounds_enabled and self.draw_sound: self.draw_sound.play()