import unittest
from unittest.mock import patch, mock_open, call
import json 
from pathlib import Path

# Klasse, die getestet wird
from core.settings_manager import SettingsManager

class TestSettingsManager(unittest.TestCase):
    """Testet die Logik zum Laden und Speichern von Anwendungseinstellungen."""

    def setUp(self):
        """Patcht die Hilfsfunktion, um den Dateipfad zu kontrollieren."""
        # Singleton-Reset, um eine saubere Instanz für jeden Test zu gewährleisten.
        # Dies verhindert, dass Tests sich gegenseitig beeinflussen.
        if hasattr(SettingsManager, '_instance'):
            SettingsManager._instance = None
        # Das _initialized-Flag muss entfernt werden, damit __init__ erneut ausgeführt wird.
        if hasattr(SettingsManager, '_initialized'):
            delattr(SettingsManager, '_initialized')

        # Patch für das AppData-Verzeichnis
        patcher_app_data = patch('core.settings_manager.get_app_data_dir')
        self.mock_get_app_data_dir = patcher_app_data.start()
        self.mock_app_data_dir = Path('/fake/appdata/dir')
        self.mock_get_app_data_dir.return_value = self.mock_app_data_dir
        self.expected_filepath = self.mock_app_data_dir / "settings.json"
        self.addCleanup(patcher_app_data.stop)

        # Patch für das Anwendungs-Root-Verzeichnis (der fehlende Teil)
        patcher_root_dir = patch('core.settings_manager.get_application_root_dir')
        self.mock_get_root_dir = patcher_root_dir.start()
        self.mock_root_dir = Path('/fake/root/dir')
        self.mock_get_root_dir.return_value = self.mock_root_dir
        self.addCleanup(patcher_root_dir.stop)

    @patch('pathlib.Path.exists', return_value=False)
    def test_load_settings_no_file_uses_defaults(self, mock_exists):
        """Testet, ob Standardeinstellungen geladen werden, wenn keine Datei existiert."""
        sm = SettingsManager()
        defaults = sm._get_defaults()

        self.assertEqual(sm.settings, defaults)
        self.assertEqual(sm.get('theme'), 'light')
        # Prüfen, ob auf beide Pfade geprüft wurde
        self.assertEqual(mock_exists.call_count, 2)

    @patch('pathlib.Path.exists', return_value=True)
    def test_load_settings_with_existing_file(self, mock_exists):
        """Testet das erfolgreiche Laden aus einer existierenden Datei."""
        mock_data = json.dumps({'theme': 'dark', 'sound_enabled': False, 'last_player_names': ['A', 'B']}) 
        
        with patch('builtins.open', mock_open(read_data=mock_data)) as mock_file:
            sm = SettingsManager()
            self.assertEqual(sm.get('theme'), 'dark')
            self.assertFalse(sm.get('sound_enabled'))
            self.assertEqual(sm.get('last_player_names'), ['A', 'B'])
            mock_file.assert_called_once_with(self.expected_filepath, 'r', encoding='utf-8')
        # Prüfen, dass nur der erste Pfad geprüft wurde (da er existiert)
        mock_exists.assert_called_once()

    @patch('pathlib.Path.exists', return_value=True)
    def test_load_settings_with_partial_file_merges_defaults(self, mock_exists):
        """Testet, ob eine unvollständige Datei mit Standardwerten zusammengeführt wird."""
        mock_data = json.dumps({'theme': 'dark'}) # 'sound_enabled' und 'last_player_names' fehlen
        
        with patch('builtins.open', mock_open(read_data=mock_data)):
            sm = SettingsManager()
            self.assertEqual(sm.get('theme'), 'dark') # Wert aus Datei
            self.assertTrue(sm.get('sound_enabled')) # Wert aus Defaults
            self.assertIsNotNone(sm.get('last_player_names')) # Wert aus Defaults

    @patch('pathlib.Path.exists', return_value=True)
    def test_load_settings_with_corrupt_file_uses_defaults(self, mock_exists):
        """Testet, ob bei einer korrupten JSON-Datei auf Standardwerte zurückgegriffen wird."""
        mock_data = "this is not valid json"
        
        with patch('builtins.open', mock_open(read_data=mock_data)):
            sm = SettingsManager()
            defaults = sm._get_defaults()
            self.assertEqual(sm.settings, defaults)

    def test_get_value_with_default_fallback(self):
        """Testet die get-Methode mit einem Fallback-Standardwert."""
        # Initialisieren ohne Datei, um sicherzustellen, dass nur Defaults geladen werden
        with patch('os.path.exists', return_value=False):
            sm = SettingsManager()
        
        # Annahme: 'non_existent_key' ist nicht in den Defaults
        self.assertIsNone(sm.get('non_existent_key'))
        self.assertEqual(sm.get('non_existent_key', 'fallback'), 'fallback')

    @patch('pathlib.Path.mkdir')
    @patch('os.path.exists', return_value=False)
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_set_and_save_settings(self, mock_json_dump, mock_file, mock_exists, mock_mkdir):
        """Testet das Setzen und anschließende Speichern von Einstellungen."""
        sm = SettingsManager()
        
        # Werte ändern
        sm.set('theme', 'dark')
        sm.set('new_setting', 123)
        
        # Speichern
        sm.save_settings()
        
        # Überprüfen, ob mkdir aufgerufen wurde
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Überprüfen, ob die Datei zum Schreiben geöffnet wurde
        mock_file.assert_called_once_with(self.expected_filepath, 'w', encoding='utf-8')
        
        # Überprüfen, ob json.dump mit den korrekten, aktualisierten Daten aufgerufen wurde
        self.assertTrue(mock_json_dump.called)
        saved_data = mock_json_dump.call_args[0][0]
        
        self.assertEqual(saved_data['theme'], 'dark')
        self.assertEqual(saved_data['new_setting'], 123)
        self.assertTrue(saved_data['sound_enabled']) # Standardwert sollte noch da sein

    @patch('pathlib.Path.mkdir')
    @patch('os.path.exists', return_value=False) # Starten ohne Datei
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_settings_creates_directory_if_not_exists(self, mock_json_dump, mock_file, mock_exists, mock_mkdir):
        """Testet, ob save_settings das Verzeichnis erstellt, falls es nicht existiert."""
        sm = SettingsManager()

        # Speichern
        sm.save_settings()

        # Überprüfen, ob versucht wurde, das Verzeichnis zu erstellen.
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Überprüfen, ob die Datei trotzdem gespeichert wurde
        mock_file.assert_called_once_with(self.expected_filepath, 'w', encoding='utf-8')
        mock_json_dump.assert_called_once()
