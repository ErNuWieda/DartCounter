import unittest
from unittest.mock import patch, mock_open
import json
from pathlib import Path

# Klasse, die getestet wird
from core.settings_manager import SettingsManager

class TestSettingsManager(unittest.TestCase):
    """Testet die Logik zum Laden und Speichern von Anwendungseinstellungen."""

    def setUp(self):
        """Patcht die Hilfsfunktion, um den Dateipfad zu kontrollieren."""
        patcher = patch('core.settings_manager.get_app_data_dir')
        self.mock_get_app_data_dir = patcher.start()
        self.mock_app_data_dir = Path('/fake/appdata/dir')
        self.mock_get_app_data_dir.return_value = self.mock_app_data_dir
        self.expected_filepath = self.mock_app_data_dir / "settings.json"
        self.addCleanup(patcher.stop)

    @patch('os.path.exists', return_value=False)
    def test_load_settings_no_file_uses_defaults(self, mock_exists):
        """Testet, ob Standardeinstellungen geladen werden, wenn keine Datei existiert."""
        sm = SettingsManager()
        defaults = sm._get_defaults()
        
        self.assertEqual(sm.settings, defaults)
        self.assertEqual(sm.get('theme'), 'light')
        mock_exists.assert_called_once_with(self.expected_filepath)

    @patch('os.path.exists', return_value=True)
    def test_load_settings_with_existing_file(self, mock_exists):
        """Testet das erfolgreiche Laden aus einer existierenden Datei."""
        mock_data = json.dumps({'theme': 'dark', 'sound_enabled': False, 'last_player_names': ['A', 'B']})
        
        with patch('builtins.open', mock_open(read_data=mock_data)) as mock_file:
            sm = SettingsManager()
            self.assertEqual(sm.get('theme'), 'dark')
            self.assertFalse(sm.get('sound_enabled'))
            self.assertEqual(sm.get('last_player_names'), ['A', 'B'])
            mock_file.assert_called_once_with(self.expected_filepath, 'r', encoding='utf-8')

    @patch('os.path.exists', return_value=True)
    def test_load_settings_with_partial_file_merges_defaults(self, mock_exists):
        """Testet, ob eine unvollständige Datei mit Standardwerten zusammengeführt wird."""
        mock_data = json.dumps({'theme': 'dark'}) # 'sound_enabled' und 'last_player_names' fehlen
        
        with patch('builtins.open', mock_open(read_data=mock_data)):
            sm = SettingsManager()
            self.assertEqual(sm.get('theme'), 'dark') # Wert aus Datei
            self.assertFalse(sm.get('sound_enabled')) # Wert aus Defaults
            self.assertIsNotNone(sm.get('last_player_names')) # Wert aus Defaults

    @patch('os.path.exists', return_value=True)
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

    @patch('os.path.exists', return_value=False) # Starten ohne Datei
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_set_and_save_settings(self, mock_json_dump, mock_file, mock_exists):
        """Testet das Setzen und anschließende Speichern von Einstellungen."""
        sm = SettingsManager()
        
        # Werte ändern
        sm.set('theme', 'dark')
        sm.set('new_setting', 123)
        
        # Speichern
        sm.save_settings()
        
        # Überprüfen, ob die Datei zum Schreiben geöffnet wurde
        mock_file.assert_called_once_with(self.expected_filepath, 'w', encoding='utf-8')
        
        # Überprüfen, ob json.dump mit den korrekten, aktualisierten Daten aufgerufen wurde
        self.assertTrue(mock_json_dump.called)
        saved_data = mock_json_dump.call_args[0][0]
        
        self.assertEqual(saved_data['theme'], 'dark')
        self.assertEqual(saved_data['new_setting'], 123)
        self.assertFalse(saved_data['sound_enabled']) # Standardwert sollte noch da sein