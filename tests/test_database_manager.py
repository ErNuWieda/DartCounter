import unittest
from unittest.mock import patch, MagicMock, mock_open
import configparser
from pathlib import Path

# Fügt das Projektverzeichnis zum Python-Pfad hinzu, damit core.*-Importe funktionieren
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    """
    Testet die Ladelogik und Verbindungsherstellung des DatabaseManager.
    """

    @patch('core.database_manager.psycopg2.connect')
    @patch('core.database_manager.get_app_data_dir')
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="[postgresql]\nhost=user_host\ndatabase=user_db\nuser=user\npassword=user_pass")
    def test_loads_config_from_user_dir_first(self, mock_file, mock_exists, mock_get_app_data_dir, mock_connect):
        """
        Testet, ob die config.ini aus dem Benutzerverzeichnis priorisiert wird.
        """
        # Setup: Beide Konfigurationsdateien existieren
        mock_get_app_data_dir.return_value = Path('/fake/user/dir')
        # user_config_path.exists() -> True, root_config_path.exists() -> True
        mock_exists.side_effect = [True, True]

        db_manager = DatabaseManager()

        # Assert: Verbindung wird mit den Daten aus der User-Config aufgebaut
        self.assertTrue(db_manager.is_connected)
        mock_connect.assert_called_once_with(host='user_host', database='user_db', user='user', password='user_pass')

    @patch('core.database_manager.psycopg2.connect')
    @patch('core.database_manager.get_app_data_dir')
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="[postgresql]\nhost=root_host\ndatabase=root_db\nuser=root\npassword=root_pass")
    def test_loads_config_from_root_dir_as_fallback(self, mock_file, mock_exists, mock_get_app_data_dir, mock_connect):
        """
        Testet, ob die config.ini aus dem Projekt-Root als Fallback geladen wird.
        """
        # Setup: Nur die Root-Konfigurationsdatei existiert
        mock_get_app_data_dir.return_value = Path('/fake/user/dir')
        # user_config_path.exists() -> False, root_config_path.exists() -> True
        mock_exists.side_effect = [False, True, True]

        db_manager = DatabaseManager()

        # Assert: Verbindung wird mit den Daten aus der Root-Config aufgebaut
        self.assertTrue(db_manager.is_connected)
        mock_connect.assert_called_once_with(host='root_host', database='root_db', user='root', password='root_pass')

    @patch('core.database_manager.shutil.copy')
    @patch('core.database_manager.psycopg2.connect')
    @patch('core.database_manager.get_app_data_dir')
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="[postgresql]\nhost=example_host\ndatabase=example_db\nuser=example\npassword=example_pass")
    def test_creates_config_from_example_if_none_exist(self, mock_file, mock_exists, mock_get_app_data_dir, mock_connect, mock_copy):
        """
        Testet, ob config.ini aus config.ini.example erstellt wird, wenn keine existiert.
        """
        # Setup: Keine config.ini, aber eine config.ini.example existiert
        mock_get_app_data_dir.return_value = Path('/fake/user/dir')
        # user_config.exists() -> F, root_config.exists() -> F, example_config.exists() -> T, user_config.exists() (nach copy) -> T
        mock_exists.side_effect = [False, False, True, True]

        db_manager = DatabaseManager()

        # Assert: Die Beispieldatei wird kopiert
        mock_copy.assert_called_once()
        # Assert: Verbindung wird mit den Daten aus der neuen (ehemals Beispiel-)Config aufgebaut
        self.assertTrue(db_manager.is_connected)
        mock_connect.assert_called_once_with(host='example_host', database='example_db', user='example', password='example_pass')

    @patch('core.database_manager.psycopg2.connect')
    @patch('pathlib.Path.exists', return_value=False)
    def test_no_connection_if_no_config_can_be_found(self, mock_exists, mock_connect):
        """Testet, ob die Datenbankverbindung deaktiviert bleibt, wenn keine Konfiguration gefunden wird."""
        db_manager = DatabaseManager()
        self.assertFalse(db_manager.is_connected)
        mock_connect.assert_not_called()

if __name__ == '__main__':
    unittest.main()