import json
import os

SETTINGS_FILE = "settings.json"

class SettingsManager:
    """
    Verwaltet das Laden und Speichern von Anwendungseinstellungen.
    """
    def __init__(self):
        self.filepath = SETTINGS_FILE
        self.settings = self._load_settings()

    def _get_defaults(self):
        """Gibt die Standardeinstellungen als Dictionary zurück."""
        return {
            'sound_enabled': True,
            # Hier können zukünftig weitere Einstellungen hinzugefügt werden
            'theme': 'light',
            'last_player_names': ["Sp1", "Sp2", "Sp3", "Sp4"]
        }

    def _load_settings(self):
        """Lädt Einstellungen aus der JSON-Datei oder gibt die Standardwerte zurück."""
        defaults = self._get_defaults()
        if not os.path.exists(self.filepath):
            return defaults
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                # Stellt sicher, dass alle Standardschlüssel vorhanden sind
                for key, value in defaults.items():
                    if key not in loaded_settings:
                        loaded_settings[key] = value
                return loaded_settings
        except (json.JSONDecodeError, IOError):
            return defaults

    def save_settings(self):
        """Speichert die aktuellen Einstellungen in der JSON-Datei."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"Fehler beim Speichern der Einstellungen: {e}")

    def get(self, key, default=None):
        """Ruft einen Einstellungswert über seinen Schlüssel ab."""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Setzt einen Einstellungswert über seinen Schlüssel."""
        self.settings[key] = value