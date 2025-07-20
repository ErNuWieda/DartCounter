import json
import os

SETTINGS_FILE = "settings.json"

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

        Setzt den Pfad zur Einstellungsdatei und löst sofort das Laden der
        Einstellungen in den Speicher aus.
        """
        self.filepath = SETTINGS_FILE
        self.settings = self._load_settings()

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
            'last_player_names': ["Sp1", "Sp2", "Sp3", "Sp4"]
        }

    def _load_settings(self):
        """
        Lädt Einstellungen aus der JSON-Datei.

        Wenn die Datei nicht existiert, werden die Standardeinstellungen
        zurückgegeben. Wenn die Datei existiert, wird sie gelesen und mit den
        Standardeinstellungen abgeglichen, um sicherzustellen, dass alle
        Schlüssel vorhanden sind. Dies verhindert Fehler, wenn nach einem
        Update neue Optionen hinzukommen.

        Returns:
            dict: Das geladene und vervollständigte Einstellungs-Dictionary.
        """
        defaults = self._get_defaults()
        if not os.path.exists(self.filepath):
            return defaults
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
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
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"Fehler beim Speichern der Einstellungen: {e}")

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