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

import json
import logging
import os
import platform
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

def get_application_root_dir() -> Path:
    """
    Gibt das Wurzelverzeichnis der Anwendung zurück.
    Funktioniert sowohl für Skriptausführung als auch für eine gepackte Anwendung.
    """
    if getattr(sys, 'frozen', False):
        # Gepackte Anwendung (PyInstaller, cx_freeze, etc.)
        return Path(sys.executable).parent
    else:
        # Skriptausführung
        return Path(__file__).resolve().parent.parent

def get_app_data_dir() -> Path:
    """
    Gibt das plattformspezifische Anwendungsdaten-Verzeichnis zurück.
    Fängt Fehler ab und fällt auf das Anwendungsverzeichnis zurück.
    """
    try:
        system = platform.system()
        app_name = "DartCounter"

        if system == "Windows":
            appdata = os.getenv('APPDATA')
            if not appdata:
                raise OSError("APPDATA Umgebungsvariable nicht gefunden.")
            path = Path(appdata) / app_name
        elif system == "Darwin": # macOS
            path = Path.home() / "Library" / "Application Support" / app_name
        else: # Linux
            path = Path.home() / ".config" / app_name.lower()

        path.mkdir(parents=True, exist_ok=True)
        return path
    except (OSError, TypeError) as e:
        logger.warning(f"Konnte das Benutzer-spezifische Datenverzeichnis nicht erstellen: {e}", exc_info=True)
        logger.warning("Fallback auf das Anwendungsverzeichnis für Einstellungen und Konfiguration.")
        return get_application_root_dir()


class SettingsManager:
    """
    Verwaltet das Laden, Speichern und den Zugriff auf Anwendungseinstellungen.

    Diese Klasse ist dafür verantwortlich, Benutzereinstellungen wie das
    Design-Theme, Sound-Präferenzen oder zuletzt verwendete Spielernamen
    persistent zu machen. Sie liest und schreibt diese Einstellungen in eine
    lokale `settings.json`-Datei.

    Die Klasse ist so konzipiert, dass sie robust gegenüber fehlenden oder
    fehlerhaften Einstellungsdateien ist, indem sie auf einen Satz von
    Standardwerten zurückfällt.

    Attributes:
        filepath (str): Der Pfad zur `settings.json`-Datei.
        settings (dict): Ein Dictionary, das die geladenen Einstellungen im
                         Speicher hält.
    """
    def __init__(self):
        """
        Initialisiert den SettingsManager.

        Ermittelt den Pfad zur Einstellungsdatei und löst sofort das Laden
        der Einstellungen in den Speicher aus.
        """
        # Der Pfad zum Speichern ist immer das Benutzerverzeichnis.
        self.save_filepath = get_app_data_dir() / "settings.json"
        
        # Logik zum Finden der zu ladenden Konfigurationsdatei
        root_filepath = get_application_root_dir() / "settings.json"
        filepath_to_load_from = None

        if self.save_filepath.exists():
            filepath_to_load_from = self.save_filepath
        elif root_filepath.exists():
            filepath_to_load_from = root_filepath            
            logger.info(f"Lade 'settings.json' aus dem Anwendungsverzeichnis als Fallback: {root_filepath}")

        if filepath_to_load_from:
            self.settings = self._load_settings(filepath_to_load_from)
        else:
            self.settings = self._get_defaults()

    def _get_defaults(self):
        """
        Gibt die Standardeinstellungen als Dictionary zurück.

        Diese Methode dient als zentrale Quelle für die Standardkonfiguration
        der Anwendung. Sie wird verwendet, wenn keine Einstellungsdatei
        vorhanden ist oder um sicherzustellen, dass nach einem Update neue
        Einstellungsoptionen in einer alten Konfiguration verfügbar sind.

        Returns:
            dict: Ein Dictionary mit den Standardeinstellungen.
        """
        return {
            'sound_enabled': True,
            'theme': 'light',
            'last_player_names': ["Sp1", "Sp2", "Sp3", "Sp4"],
            'last_tournament_players': []
        }

    def _load_settings(self, filepath):
        """
        Lädt Einstellungen aus der JSON-Datei.
        
        Diese Methode geht davon aus, dass die Datei existiert. Sie wird gelesen
        und mit den Standardeinstellungen abgeglichen, um sicherzustellen, dass
        alle Schlüssel vorhanden sind. Dies verhindert Fehler, wenn nach einem
        Update neue Optionen hinzukommen. Bei einem Lesefehler wird auf die
        Standardwerte zurückgefallen.

        Returns:
            dict: Das geladene und vervollständigte Einstellungs-Dictionary.
        """
        defaults = self._get_defaults()
        try:
            # Die Existenzprüfung wird hier entfernt, da sie bereits im Konstruktor stattfindet.
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                # Stellt sicher, dass alle Standardschlüssel in den geladenen
                # Einstellungen vorhanden sind, um Kompatibilität zu gewährleisten.
                for key, value in defaults.items():
                    if key not in loaded_settings:
                        loaded_settings[key] = value
                return loaded_settings
        except (json.JSONDecodeError, IOError):
            # Bei Lesefehlern oder ungültigem JSON auf Standardwerte zurückfallen.
            return defaults

    def save_settings(self):
        """
        Speichert die aktuellen In-Memory-Einstellungen in die JSON-Datei.
        Diese Methode sollte beim Beenden der Anwendung aufgerufen werden.
        """
        try:
            # Sicherstellen, dass das übergeordnete Verzeichnis existiert.
            # Dies ist wichtig für den allerersten Start der Anwendung.
            self.save_filepath.parent.mkdir(parents=True, exist_ok=True)
            # Speichert immer in das Benutzerverzeichnis
            with open(self.save_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {e}", exc_info=True)

    def get(self, key, default=None):
        """
        Ruft einen Einstellungswert sicher über seinen Schlüssel ab.

        Args:
            key (str): Der Schlüssel der gewünschten Einstellung.
            default (any, optional): Ein Standardwert, der zurückgegeben wird,
                                     falls der Schlüssel nicht existiert.

        Returns:
            any: Der Wert der Einstellung oder der `default`-Wert.
        """
        return self.settings.get(key, default)

    def set(self, key, value):
        """
        Setzt oder aktualisiert einen Einstellungswert im Speicher.

        Hinweis: Diese Änderung wird erst durch den Aufruf von `save_settings()`
        persistent gemacht.

        Args:
            key (str): Der Schlüssel der zu setzenden Einstellung.
            value (any): Der neue Wert für die Einstellung.
        """
        self.settings[key] = value